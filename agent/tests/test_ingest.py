"""
Tests for the standalone ingestion parser.
"""

from pathlib import Path
from scripts.ingest import parse_markdown_file

def test_parse_markdown_frontmatter():
    sample_file = Path(__file__).resolve().parent.parent / "data" / "markdown" / "FAQ-01-001.md"
    assert sample_file.exists(), f"Sample file not found at {sample_file}"

    docs = parse_markdown_file(sample_file)
    assert len(docs) > 0, "Expected at least one document chunk"
    
    first_doc = docs[0]
    meta = first_doc.metadata
    assert meta.get("id") == "FAQ-01-001"
    assert meta.get("category") == "academic"
    assert "Surat Keterangan Mahasiswa Aktif" in meta.get("title", "")
    assert "Persyaratan" in first_doc.page_content or "Deskripsi Layanan" in first_doc.page_content
    # Ensure all metadata values are JSON serializable (no raw date objects)
    import json
    json_str = json.dumps(meta)
    assert isinstance(meta.get("verified_at"), str)
    assert meta.get("verified_at") == "2026-10-15"
