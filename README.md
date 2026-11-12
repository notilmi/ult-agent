# ULT Polsri AI Service Assistant (`ulp-helper`)

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.17%2B-darkgreen.svg)](https://github.com/langchain-ai/langgraph)
[![Next.js](https://img.shields.io/badge/Next.js-16%2B-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/NeonDB-pgvector-00e599.svg)](https://neon.tech/)
[![Google Gemini](https://img.shields.io/badge/Gemini-3.8%20Flash%20%7C%20Embedding%202-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, grounded conversational AI assistant designed for the **Unit Layanan Terpadu (ULT) Politeknik Negeri Sriwijaya (Polsri)**. 

The system guides students, lecturers, alumni, and general public through administrative services, academic procedures, complaint submissions, and information requests—with **strict zero-hallucination guardrails**, **automated PII redaction**, **NeonDB (`pgvector`) retrieval**, and **human officer escalation**.

---

## 📑 Table of Contents

- [Key Capabilities & Guardrails](#-key-capabilities--guardrails)
- [Repository Structure](#-repository-structure)
- [Architecture Overview](#️-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Environment Configuration](#1-environment-configuration)
  - [2. Knowledge Base Ingestion](#2-knowledge-base-ingestion)
  - [3. Start Backend Server](#3-start-backend-server)
  - [4. Start Frontend Client](#4-start-frontend-client)
- [Knowledge Base Management](#-knowledge-base-management)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Documentation & Architecture Decisions](#-documentation--architecture-decisions)
- [License & Attribution](#-license--attribution)

---

## ✨ Key Capabilities & Guardrails

* **Zero-Hallucination & Strict Groundedness**: Every answer is synthesized exclusively from verified ULT official documents and procedures stored in NeonDB. If context is missing or similarity is low, the assistant politely declines and provides official escalation contacts.
* **Privacy & PII Protection**: Automatic regex-based redaction of sensitive Indonesian identifiers (NIM, NIK, telephone numbers) before processing any prompt.
* **Prompt Injection Defense**: Multi-pattern screening against roleplay overrides, jailbreaks, system prompt exfiltration, and delimiter attacks.
* **Informational & Procedural Scope Only**: Strictly non-transactional. The assistant does not alter grades, reset passwords, or generate official letters; it provides official requirements, procedures, responsible units, and direct form URLs.
* **Transparent Escalation**: When inquiries fall outside the knowledge base or after repeated fallbacks, the system routes users directly to ULT Polsri service hours, physical desk location (Lantai 1 Gedung Pusat Administrasi Polsri), and contact channels.

---

## 📂 Repository Structure

This repository is organized as a unified monorepo containing the Python LangGraph backend and the Next.js chat client:

```text
ulp-helper/
├── agent/                             # Backend LangGraph application & ingestion pipeline
│   ├── data/                          # Seed knowledge base documents
│   │   ├── markdown/                  # Structured markdown FAQs with YAML frontmatter
│   │   └── pdf/                       # Official procedure PDFs & guidelines
│   ├── docs/                          # In-depth architectural guides & ADRs
│   │   ├── decisions/                 # Architecture Decision Records (0001 - 0004)
│   │   ├── architecture.md            # Detailed 8-node state machine architecture
│   │   └── ingestion-guide.md         # Document curation & vector ingestion guide
│   ├── scripts/                       # Database scripts & CLI tools
│   │   ├── init_db.sql                # NeonDB schema and pgvector index setup
│   │   └── ingest.py                  # Chunking and embedding ingestion CLI
│   ├── src/                           # Backend application source code
│   │   ├── agent/                     # LangGraph state machine, nodes, and helpers
│   │   │   ├── nodes/                 # 8 discrete state nodes (guards, retrieval, etc.)
│   │   │   ├── graph.py               # Compiled StateGraph definition
│   │   │   ├── state.py               # AgentState schema & TypedDict definitions
│   │   │   └── utils.py               # Multimodal sanitization & formatting utilities
│   │   ├── db/                        # NeonDB / PGVector connection & search helpers
│   │   └── config.py                  # Pydantic environment configuration
│   ├── tests/                         # Pytest test suite (unit & integration tests)
│   ├── langgraph.json                 # LangGraph server configuration
│   └── pyproject.toml                 # uv/Python dependency definitions
│
├── client-demo/                       # Frontend Next.js Chat Client (Chat ULT Polsri)
│   ├── public/                        # Polsri logo, favicon, and static assets
│   ├── src/
│   │   ├── app/                       # Next.js App Router (layout, page, metadata)
│   │   ├── components/                # UI components (chat thread, avatars, markdown)
│   │   ├── hooks/                     # Custom React hooks (streaming, media query)
│   │   └── providers/                 # LangGraph SDK client & stream providers
│   ├── package.json                   # Next.js & pnpm dependency definitions
│   └── tailwind.config.js             # Tailwind CSS design system configuration
│
├── langgraph.json                     # Root LangGraph server mapping
├── README.md                          # Root project documentation (this file)
└── .gitignore                         # Project-wide VCS ignore rules
```

---

## 🏛️ Architecture Overview

The backend uses a compiled **LangGraph `StateGraph`** executing an 8-node deterministic workflow:

```mermaid
flowchart TD
    Start([User Message]) --> InputGuard[1. input_guard\nPII Redaction & Injection Check]
    
    InputGuard -->|Unsafe / Injected| Escalate[8. escalate\nHuman Officer Routing]
    InputGuard -->|Safe| QueryRefine[2. query_refine\nQuery Resolution & Classification]
    
    QueryRefine --> Retrieve[3. retrieve\nCosine Search in NeonDB pgvector]
    Retrieve --> GradeContext[4. grade_context\nThreshold Calibration]
    
    GradeContext -->|Pass >= 0.55| GenerateAnswer[5. generate_answer\nGrounded LLM Synthesis]
    GradeContext -->|Below Threshold| Fallback[7. fallback\nPolite Scope Refusal]
    
    GenerateAnswer --> OutputGuard[6. output_guard\nHallucination & Transaction Defense]
    
    OutputGuard -->|Passed| End([Deliver Answer])
    OutputGuard -->|Flagged Violation| Fallback
    
    Fallback -->|Fallback Limit Reached| Escalate
    Fallback -->|Single Fallback| End
    Escalate --> End
```

### Node Responsibilities:
1. **`input_guard`**: Redacts Indonesian NIK, NIM, and phone numbers; blocks prompt injection payloads.
2. **`query_refine`**: Contextualizes multi-turn conversations into standalone queries and classifies into 5 service areas (`academic`, `student_affairs`, `general_admin`, `unit_info`, `complaints`).
3. **`retrieve`**: Computes 768-dim embeddings via `gemini-embedding-2` and queries NeonDB using cosine distance.
4. **`grade_context`**: Verifies whether retrieved passages meet the calibrated similarity threshold (`>= 0.55`).
5. **`generate_answer`**: Synthesizes verified responses with citations, requirements, steps, responsible units, and official form URLs.
6. **`output_guard`**: Scans the draft output to ensure no unauthorized transactional commitments or speculative claims were made.
7. **`fallback`**: Delivers honest refusals when information is not present in the official knowledge base.
8. **`escalate`**: Provides official ULT service desk contact numbers, operating hours, and location.

---

## 🛠 Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Agent Orchestration** | LangGraph (Python) 0.17+ | Stateful graph workflow with deterministic branching |
| **LLM Engine** | Google Gemini 3.8 Flash | High-speed, context-aware reasoning & response synthesis |
| **Embeddings** | Google Gemini Embedding 2 | Dense semantic representations (768 dimensions) |
| **Vector Database** | NeonDB (Serverless PostgreSQL) | `pgvector` extension with HNSW/IVFFlat cosine indexing |
| **Package Manager** | `uv` (Python) & `pnpm` (Node.js) | Fast, deterministic dependency management |
| **Frontend Client** | Next.js 16 (React 19) + Tailwind CSS | Responsive, branded chat UI powered by `@langchain/langgraph-sdk` |
| **Development Server** | LangGraph CLI (`langgraph dev`) | Background hot-reload runtime & LangGraph Studio debugger |

---

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

1. **Python 3.12+** or **3.14+** with [`uv`](https://docs.astral.sh/uv/):
   ```bash
   # Install uv (Windows PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. **Node.js 18+** with [`pnpm`](https://pnpm.io/):
   ```bash
   npm install -g pnpm
   ```
3. **Google Gemini API Key**: Obtain from [Google AI Studio](https://aistudio.google.com/).
4. **NeonDB Database**: PostgreSQL instance with `pgvector` enabled (obtain connection URL from [Neon Console](https://console.neon.tech/)).

---

## 🚀 Quick Start Guide

### 1. Environment Configuration

#### Backend Environment
Create `agent/.env` based on `agent/.env.example`:

```bash
cd agent
cp .env.example .env
```

Edit `agent/.env` with your credentials:
```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# NeonDB PostgreSQL Connection
NEON_DATABASE_URL=postgresql+psycopg://user:password@ep-sample-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# Model Configurations
LLM_MODEL=gemini-3.8-flash
EMBEDDING_MODEL=gemini-embedding-2

# Calibration & Guardrail Thresholds
SIMILARITY_THRESHOLD=0.55
RETRIEVAL_TOP_K=4
MAX_FALLBACK_COUNT=2
```

#### Frontend Environment
Create `client-demo/.env.local`:

```bash
cd ../client-demo
cp .env.example .env.local
```

Ensure `client-demo/.env.local` contains:
```env
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=ult_agent
```

---

### 2. Knowledge Base Ingestion

Run the database initialization and ingest the bundled seed procedures:

```bash
cd agent
uv run python scripts/ingest.py --init-db
```

Output:
```text
[INFO] Initializing NeonDB schema...
[INFO] NeonDB schema initialized successfully.
[INFO] Discovered 5 document(s) in agent/data
  - Parsed Markdown: FAQ-01-001.md -> 2 chunk(s)
  - Parsed Markdown: FAQ-01-002.md -> 3 chunk(s)
  - Parsed Markdown: FAQ-02-001.md -> 3 chunk(s)
  - Parsed Markdown: FAQ-04-001.md -> 2 chunk(s)
  - Parsed Markdown: FAQ-05-001.md -> 2 chunk(s)
[INFO] Ingesting 12 total chunks into NeonDB collection via gemini-embedding-2...
[SUCCESS] Ingested 12 chunks into NeonDB vector store.
```

---

### 3. Start Backend Server

Launch the LangGraph development server with live reload on port `2024`:

```bash
# From workspace root or agent/ directory
cd agent
uv run langgraph dev --port 2024
```

Access Points:
* **API Server**: `http://127.0.0.1:2024`
* **Swagger Documentation**: `http://127.0.0.1:2024/docs`
* **LangGraph Studio**: [Open Studio Inspector](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

---

### 4. Start Frontend Client

In a separate terminal, start the Next.js development server:

```bash
cd client-demo
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. The rebranded **Chat ULT Polsri** interface is now connected live to your local LangGraph backend.

---

## 📚 Knowledge Base Management

Knowledge base documents reside in `agent/data/markdown/` and `agent/data/pdf/`. 

### Document Structure (Markdown)
Each Markdown FAQ must include standard YAML frontmatter:

```markdown
---
title: Prosedur Pengajuan Surat Keterangan Mahasiswa Aktif
category: academic
document_id: FAQ-01-001
verified_at: "2026-10-15"
source_url: https://polsri.ac.id/layanan/surat-keterangan
tags: [surat aktif, akademik, beasiswa]
---

### Ringkasan Layanan
Layanan penerbitan Surat Keterangan Mahasiswa Aktif untuk keperluan BPJS, tunjangan gaji orang tua, atau beasiswa.

### Persyaratan Dokumen
1. Bukti Pembayaran UKT semester berjalan.
2. Kartu Rencana Studi (KRS) yang telah divalidasi DPA.
...
```

### Ingestion CLI Options
```bash
# Ingest single file
uv run python scripts/ingest.py --path data/markdown/FAQ-02-001.md

# Ingest specific directory with category tag
uv run python scripts/ingest.py --path data/pdf/ --category complaints

# Re-initialize database tables and indexes
uv run python scripts/ingest.py --init-db
```

For complete document authoring guidelines, see [Knowledge Base Ingestion Guide](agent/docs/ingestion-guide.md).

---

## 🧪 Testing & Quality Assurance

### Run Backend Unit & Integration Tests
```bash
cd agent
uv run pytest
```
Tests cover:
- PII regex masking (NIK, NIM, phone numbers).
- Prompt injection detection and deflection.
- Standalone query rewriting and intent classification.
- Cosine similarity threshold grading.
- Zero-hallucination grounded answer generation.
- Repeated fallback and human escalation triggers.

### Build Frontend Production Bundle
```bash
cd client-demo
pnpm build
```

---

## 📖 Documentation & Architecture Decisions

Comprehensive architectural guides and decisions are recorded in `agent/docs/`:

* 📘 **[Architecture & Implementation Specification](agent/docs/architecture.md)**: State schemas, node contracts, PII patterns, and client streaming protocol.
* 📗 **[Knowledge Base Ingestion Guide](agent/docs/ingestion-guide.md)**: Metadata formatting, document categorization, and chunking strategies.
* 🏛️ **Architecture Decision Records (ADRs)**:
  * **[ADR-0001: LangGraph Server & Agent Chat UI Integration](agent/docs/decisions/0001-langgraph-server-and-agent-chat-ui.md)**
  * **[ADR-0002: NeonDB PostgreSQL with pgvector for Knowledge Base](agent/docs/decisions/0002-neondb-pgvector-for-vector-store.md)**
  * **[ADR-0003: Selection of Gemini 3.8 Flash & Gemini Embedding 2](agent/docs/decisions/0003-gemini-models-for-llm-and-embeddings.md)**
  * **[ADR-0004: Multi-stage Deterministic Guardrails & Context Grading Pipeline](agent/docs/decisions/0004-deterministic-groundedness-and-guardrails.md)**

---

## 📜 License & Attribution

Developed for **Unit Layanan Terpadu (ULT) Politeknik Negeri Sriwijaya**.  
Distributed under the MIT License. See [LICENSE](client-demo/LICENSE) for more details.
