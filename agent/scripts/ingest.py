#!/usr/bin/env python3
"""
Standalone Ingestion Script for ULT Polsri AI Service Agent
Reads Markdown (with YAML frontmatter) and PDF documents, generates embeddings using Gemini Embedding 2,
and stores them in NeonDB PostgreSQL (pgvector).
"""

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Ensure parent directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from src.config import GEMINI_API_KEY, EMBEDDING_MODEL, NEON_DATABASE_URL
from src.db.client import execute_init_sql
from src.db.vectorstore import get_vectorstore

def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Converts non-JSON serializable objects (date, datetime) into strings for pgvector JSONB."""
    sanitized = {}
    for k, v in meta.items():
        if isinstance(v, (date, datetime)):
            sanitized[k] = v.isoformat()
        elif isinstance(v, (str, int, float, bool)) or v is None:
            sanitized[k] = v
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [x.isoformat() if isinstance(x, (date, datetime)) else x for x in v]
        else:
            sanitized[k] = str(v)
    return sanitized

def parse_markdown_file(file_path: Path) -> List[Document]:
    """Parses a Markdown file with optional YAML frontmatter into Document chunks."""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    metadata: Dict[str, Any] = {
        "source": str(file_path.name),
        "source_path": str(file_path),
        "file_type": "markdown",
    }
    content = raw_text

    # Extract YAML frontmatter if present
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
    if frontmatter_match:
        yaml_content = frontmatter_match.group(1)
        content = frontmatter_match.group(2)
        try:
            parsed_meta = yaml.safe_load(yaml_content)
            if isinstance(parsed_meta, dict):
                metadata.update(parsed_meta)
        except Exception as e:
            print(f"[WARN] Failed to parse YAML frontmatter in {file_path.name}: {e}")

    # Ensure required fields have fallbacks
    metadata.setdefault("category", "general")
    metadata.setdefault("title", file_path.stem)
    metadata.setdefault("source_title", file_path.name)
    metadata.setdefault("status", "published")

    # Sanitize all metadata values to ensure JSON serializability (dates -> ISO string)
    metadata = sanitize_metadata(metadata)

    # Split long markdown procedures while preserving headings
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_text(content)

    documents = []
    for idx, chunk in enumerate(chunks):
        doc_meta = dict(metadata)
        doc_meta["chunk_index"] = idx
        # Combine title and metadata context with chunk for better semantic retrieval
        header_context = f"# {metadata.get('title', '')} ({metadata.get('category', '')})\n"
        full_chunk_text = header_context + chunk.strip()
        documents.append(Document(page_content=full_chunk_text, metadata=doc_meta))

    return documents

def parse_pdf_file(file_path: Path, category: str = "general") -> List[Document]:
    """Extracts text from a PDF document and splits it into Document chunks."""
    documents = []
    try:
        reader = PdfReader(str(file_path))
        full_text = ""
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                full_text += f"\n[Halaman {page_idx + 1}]\n" + text.strip()

        if not full_text.strip():
            print(f"[WARN] No readable text found in PDF: {file_path.name}")
            return []

        metadata: Dict[str, Any] = {
            "source": str(file_path.name),
            "source_path": str(file_path),
            "file_type": "pdf",
            "title": file_path.stem.replace("_", " ").title(),
            "category": category,
            "source_title": file_path.name,
            "status": "published",
        }
        metadata = sanitize_metadata(metadata)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=60,
            separators=["\n\n", "\n", " "],
        )
        chunks = splitter.split_text(full_text)

        for idx, chunk in enumerate(chunks):
            doc_meta = dict(metadata)
            doc_meta["chunk_index"] = idx
            documents.append(Document(page_content=chunk.strip(), metadata=doc_meta))

    except Exception as e:
        print(f"[ERROR] Failed to parse PDF {file_path.name}: {e}")

    return documents

def ingest_path(target_path: Path, category: str = "general") -> int:
    """Ingests files from target path (file or directory) into NeonDB vector store."""
    if not target_path.exists():
        print(f"[ERROR] Path does not exist: {target_path}")
        return 0

    vectorstore = get_vectorstore()
    if vectorstore is None:
        print("[ERROR] Cannot connect to NeonDB. Please check NEON_DATABASE_URL and GEMINI_API_KEY in .env")
        return 0

    all_docs: List[Document] = []

    if target_path.is_file():
        files = [target_path]
    else:
        files = list(target_path.rglob("*.md")) + list(target_path.rglob("*.pdf"))

    print(f"[INFO] Discovered {len(files)} document(s) in {target_path}")

    for file in files:
        if file.suffix.lower() == ".md":
            docs = parse_markdown_file(file)
            print(f"  - Parsed Markdown: {file.name} -> {len(docs)} chunk(s)")
            all_docs.extend(docs)
        elif file.suffix.lower() == ".pdf":
            docs = parse_pdf_file(file, category=category)
            print(f"  - Parsed PDF: {file.name} -> {len(docs)} chunk(s)")
            all_docs.extend(docs)

    if not all_docs:
        print("[WARN] No document chunks to ingest.")
        return 0

    print(f"[INFO] Ingesting {len(all_docs)} total chunks into NeonDB collection via {EMBEDDING_MODEL}...")
    try:
        vectorstore.add_documents(all_docs)
        print(f"[SUCCESS] Successfully ingested {len(all_docs)} chunks into NeonDB vector database!")
        return len(all_docs)
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Ingest Markdown and PDF documents into NeonDB pgvector.")
    parser.add_argument(
        "--path",
        type=str,
        default=str(AGENT_DIR / "data"),
        help="Path to file or directory to ingest (default: agent/data)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="academic",
        help="Category for unclassified documents (academic, student_affairs, general_admin, unit_info, complaints)",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Execute init_db.sql first to ensure tables exist in NeonDB",
    )

    args = parser.parse_args()

    print("=========================================================")
    print("  ULT Polsri AI Service Agent - Knowledge Base Ingestion ")
    print(f"  Embedding Model: {EMBEDDING_MODEL}")
    print("=========================================================")

    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY is missing in your environment or .env file.")
        sys.exit(1)

    if not NEON_DATABASE_URL:
        print("[ERROR] NEON_DATABASE_URL is missing in your environment or .env file.")
        sys.exit(1)

    if args.init_db:
        print("[INFO] Initializing NeonDB schema...")
        execute_init_sql()

    target = Path(args.path)
    count = ingest_path(target, category=args.category)
    print(f"[DONE] Finished. Processed {count} chunks.")

if __name__ == "__main__":
    main()
