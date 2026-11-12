# ADR-0003: Model Selection of Gemini 3.8 Flash and Gemini Embedding 2

## Status
Accepted

## Date
2026-11-12

## Context
The agent requires:
- High performance and natural language comprehension in Indonesian (including formal campus terms and casual student phrasings).
- Low latency for streaming responses (first token under 3 seconds per PRD Section 3.3).
- Strict adherence to groundedness and refusal instructions to avoid hallucination.
- Consistent semantic embedding of Indonesian administrative text.

## Decision
We adopted:
1. **Gemini 3.8 Flash** (`gemini-3.8-flash`) as the primary LLM for intent classification, query rewriting, and grounded response synthesis.
2. **Gemini Embedding 2** (`gemini-embedding-2`) as the vector embedding model (producing 768-dimensional embeddings).

## Alternatives Considered

### 1. OpenAI GPT-4o / text-embedding-3
- **Pros**: Strong general capabilities.
- **Cons**: Higher API pricing and latency characteristics compared to lightweight flash models.
- **Rejected**: Gemini Flash models provide high Indonesian fluency and fast token-to-first-byte latency at competitive cost.

### 2. Open-source local models (Llama 3 / Ollama)
- **Pros**: Self-hosted, private execution.
- **Cons**: Requires dedicated GPU server infrastructure that is not guaranteed in the VPS environment specified in PRD Section 9.5.
- **Rejected**: Higher deployment and hardware maintenance overhead.

## Consequences
- Requires a single `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) environment variable.
- Uses `langchain-google-genai` for both chat models (`ChatGoogleGenerativeAI`) and embedding generation (`GoogleGenerativeAIEmbeddings`).
- State and prompts record `model_version = "gemini-3.8-flash"` for thesis reproducibility.
