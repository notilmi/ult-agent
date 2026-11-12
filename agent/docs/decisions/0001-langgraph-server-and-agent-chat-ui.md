# ADR-0001: Deploying via LangGraph Server and Connecting LangChain Agent Chat UI

## Status
Accepted

## Date
2026-11-12

## Context
In PRD Section 9.5 and Section 16, two deployment modes were evaluated for the ULT Polsri AI chatbot:
- **Mode A**: Custom FastAPI service wrapping the compiled graph with manual streaming endpoints.
- **Mode B**: Standalone LangGraph Server exposing standard streaming APIs.

The project requires immediate accessibility via **LangChain Agent Chat UI** for testing and demonstration, while retaining the capability to connect a dedicated, custom React client in later phases.

## Decision
We chose **LangGraph Server** configured via `langgraph.json` (`"ult_agent": "./src/agent/graph.py:graph"`) and run locally using `langgraph dev --port 2024`.

## Alternatives Considered

### 1. Custom FastAPI / Starlette Service
- **Pros**: Complete control over HTTP route definitions and bespoke middleware.
- **Cons**: Requires writing and maintaining custom SSE streaming logic, thread lifecycle endpoints, message serialization, and custom adapters for UI widgets.
- **Rejected**: LangGraph Server natively implements the full streaming protocol expected by the official LangChain Agent Chat UI and the LangGraph SDK.

### 2. Standalone Terminal / CLI Runner
- **Pros**: Very fast to prototype.
- **Cons**: Unusable for real user testing and impossible to connect to graphical chat frontends.
- **Rejected**: Does not satisfy the requirement for web-based testing and thesis evaluation.

## Consequences
- The application can be started with a single standard command: `uv run langgraph dev`.
- The open-source LangChain Agent Chat UI connects directly without needing custom backend adapters.
- Future custom frontends can use `@langchain/langgraph-sdk` or standard streaming APIs without modifying graph definitions.
