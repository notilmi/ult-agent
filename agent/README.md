# ULT Polsri AI Service Agent

A grounded conversational AI service agent for the **Unit Layanan Terpadu (ULT) Politeknik Negeri Sriwijaya (Polsri)**, built using **LangGraph (Python)**, **NeonDB (`pgvector`)**, **Gemini 3.8 Flash**, and **Gemini Embedding 2**.

Compatible out-of-the-box with **LangChain Agent Chat UI** via the LangGraph CLI development server.

---

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the `agent/` directory:

```bash
cp .env.example .env
```

Fill in your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key
NEON_DATABASE_URL=postgresql+psycopg://username:password@ep-sample.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

### 2. Knowledge Base Ingestion to NeonDB

Initialize the database schema and ingest official ULT procedures (Markdown and PDF):

```bash
# Ingest all markdown and PDF files in agent/data/
uv run python scripts/ingest.py --init-db
```

Or ingest a specific file or folder:
```bash
uv run python scripts/ingest.py --path data/markdown/FAQ-01-001.md --category academic
```

### 3. Run the LangGraph Server (for Agent Chat UI)

Start the local LangGraph server on port 2024 with hot-reloading:

```bash
uv run langgraph dev --port 2024
```

### 4. Connect with LangChain Agent Chat UI

1. Clone and launch the [LangChain Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui):
   ```bash
   git clone https://github.com/langchain-ai/agent-chat-ui.git
   cd agent-chat-ui
   npm install
   npm run dev
   ```
2. Open `http://localhost:3000` in your browser.
3. In Agent Chat UI Settings:
   - **Deployment URL**: `http://localhost:2024`
   - **Graph ID**: `ult_agent`

---

## 🧪 Running Tests

Run the test suite verifying guards, routing logic, and ingestion:

```bash
uv run pytest
```

---

## 📚 Documentation & Architecture Decision Records (ADRs)

Detailed architectural documentation and design decisions are recorded in `docs/`:

* **[Architecture & Implementation Guide](docs/architecture.md)**: Deep dive into the 8-node state graph, PII redaction rules, context grading, and client integration.
* **[Knowledge Base Ingestion Guide](docs/ingestion-guide.md)**: Step-by-step guide for curating Markdown with YAML frontmatter and PDF documents into NeonDB.
* **Architecture Decision Records (ADRs)**:
  * **[ADR-0001: Deploying via LangGraph Server & Agent Chat UI](docs/decisions/0001-langgraph-server-and-agent-chat-ui.md)**
  * **[ADR-0002: NeonDB (PostgreSQL with pgvector) for Knowledge Base](docs/decisions/0002-neondb-pgvector-for-vector-store.md)**
  * **[ADR-0003: Selection of Gemini 3.8 Flash & Gemini Embedding 2](docs/decisions/0003-gemini-models-for-llm-and-embeddings.md)**
  * **[ADR-0004: Multi-stage Deterministic Guardrails & Context Grading Pipeline](docs/decisions/0004-deterministic-groundedness-and-guardrails.md)**

---

## 🏛️ Architecture Overview

The agent executes a deterministic multi-stage state graph:

1. **`input_guard`**: Detects and redacts Indonesian personal identifiers (NIM, NIK, phone numbers) and blocks prompt injections.
2. **`query_refine`**: Resolves multi-turn references into standalone search queries using `gemini-3.8-flash` and categorizes into the 5 official ULT service areas (`academic`, `student_affairs`, `general_admin`, `unit_info`, `complaints`).
3. **`retrieve`**: Performs cosine similarity vector search in NeonDB using `gemini-embedding-2`.
4. **`grade_context`**: Grades retrieved passage relevance against a calibrated threshold.
5. **`generate_answer`**: Generates grounded responses citing official sources, requirements, steps, responsible units, and form URLs.
6. **`output_guard`**: Verifies that no forbidden transactional commitments or hallucinations were made.
7. **`fallback`**: Provides polite, honest "information not yet in KB" messages.
8. **`escalate`**: Routes directly to human officer contacts, service hours, and helpdesk upon repeated fallbacks or user requests.
