# ADR-0002: Use NeonDB (PostgreSQL with pgvector) for Knowledge Base Storage and RAG

## Status
Accepted

## Date
2026-11-12

## Context
The ULT Polsri AI chatbot requires a persistent vector store for Indonesian university procedures, SOPs, and service FAQs across five categories. Requirements include:
- Strict metadata filtering by category (`academic`, `student_affairs`, `general_admin`, `unit_info`, `complaints`) and publication status (`published`).
- High-performance vector similarity search (cosine distance).
- Minimal infrastructure overhead with zero local database server setup.
- Compatibility with PostgreSQL tools and standard SQL queries for auditing and thesis reporting.

## Decision
We selected **NeonDB**, a managed serverless PostgreSQL platform, utilizing the **`pgvector`** extension and the official **`langchain-postgres`** integration with HNSW indexing.

## Alternatives Considered

### 1. ChromaDB / FAISS (Local File-based Vector Stores)
- **Pros**: Quick to install locally.
- **Cons**: Difficult to share among distributed team members, officers, and CI test environments. Lacks full relational SQL features for joined audit tables (such as tracking user ratings and officer approval logs).
- **Rejected**: Lacks multi-environment persistence and auditability required by the thesis PRD.

### 2. Pinecone / Weaviate / Qdrant (Specialized Managed Vector DBs)
- **Pros**: Dedicated vector search engines with managed infrastructure.
- **Cons**: Introduces proprietary vector APIs, vendor lock-in, and separate infrastructure costs when relational storage is already needed for session threads and feedback.
- **Rejected**: NeonDB combines relational tables (checkpoints, feedback logs) and vector search in a single PostgreSQL instance using open-source `pgvector`.

## Consequences
- Requires the `psycopg[binary,pool]` driver and connection string in `postgresql+psycopg://` format.
- Documents are indexed using fast HNSW cosine indexes (`vector_cosine_ops`).
- Category filtering is executed natively in SQL before vector scoring.
