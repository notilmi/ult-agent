-- NeonDB (PostgreSQL) Vector Database Setup for ULT Polsri AI Service Agent
-- Enables pgvector extension and creates knowledge base tables

CREATE EXTENSION IF NOT EXISTS vector;

-- Drop table if migrating schema (optional, keep commented for safety)
-- DROP TABLE IF EXISTS ult_knowledge_base CASCADE;

CREATE TABLE IF NOT EXISTS ult_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id VARCHAR(64),                      -- e.g., FAQ-01-001 (academic)
    category VARCHAR(64) NOT NULL,             -- academic, student_affairs, general_admin, unit_info, complaints
    title VARCHAR(255) NOT NULL,               -- Service or procedure name
    content TEXT NOT NULL,                     -- Text chunk / requirements & steps
    embedding VECTOR(768),                     -- Dimension for gemini-embedding-2 (768 dimensions)
    source_title VARCHAR(255) NOT NULL,        -- Official document title / SOP
    source_ref VARCHAR(255),                   -- SK document number or reference code
    form_url VARCHAR(500),                     -- Official link to downloadable form
    responsible_unit VARCHAR(128),             -- Responsible Polsri unit (e.g., Bagian Akademik)
    verified_at DATE DEFAULT CURRENT_DATE,     -- Verification date by officer
    valid_until DATE,                          -- Validity period
    version INT DEFAULT 1,                     -- Revision counter
    status VARCHAR(32) DEFAULT 'published'     -- draft, in_review, published, archived
);

-- HNSW cosine similarity index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS ult_kb_embedding_hnsw_idx 
ON ult_knowledge_base USING hnsw (embedding vector_cosine_ops);

-- Index for filtering by category and publication status
CREATE INDEX IF NOT EXISTS ult_kb_category_status_idx 
ON ult_knowledge_base (category, status);

-- Audit table for logging fallback, escalation, and user feedback
CREATE TABLE IF NOT EXISTS ult_chat_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(128) NOT NULL,
    answer_id VARCHAR(128),
    rating INT,                                -- +1 (thumbs-up) or -1 (thumbs-down)
    reason VARCHAR(64),                        -- wrong, incomplete, unclear, slow
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
