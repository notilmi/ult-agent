# ADR-0004: Multi-stage Deterministic Guardrails and Context Grading Pipeline

## Status
Accepted

## Date
2026-11-12

## Context
Per PRD Section 1, Section 2, and Section 3.3, accuracy and honest fallback take precedence over breadth. One fabricated deadline, requirement, or document link in a university administration context can directly disrupt a student's real affairs and erode trust.

The thesis specifically measures:
- Grounded answer rate (Target: ≥ 95%).
- Fabrications in acceptance test (Target: 0 of 30 questions).
- Honest fallback and escalation rate.

Relying solely on system prompt instructions without graph-level control creates a high risk of hallucination when retrieval is weak.

## Decision
We implemented a multi-stage deterministic graph pipeline:
1. **`input_guard`**: Regular expression filtering for Indonesian NIM (student ID), NIK, and phone numbers before storing in messages; immediate refusal on adversarial prompt injection.
2. **`grade_context`**: Explicit scoring node checking if retrieved document similarity exceeds `SIMILARITY_SCORE_THRESHOLD` (0.65). If below, generation is bypassed completely, routing directly to `fallback`.
3. **`output_guard`**: Post-generation verification that inspects synthesized text for forbidden transactional commitments (e.g. claiming to approve or issue letters directly) and overrides them with safe procedural advice.
4. **`escalate`**: Triggered after repeated fallbacks (`fallback_count >= 2`), upon explicit officer requests, or for complaint inquiries.

## Alternatives Considered

### 1. Autonomous ReAct Tool-Calling Agent (`create_react_agent`)
- **Pros**: Fewer nodes, dynamic multi-hop retrieval.
- **Cons**: Non-deterministic execution loops, higher latency, and difficulty in guaranteeing zero-hallucination when the model chooses not to call tools or guesses an answer.
- **Rejected**: Does not satisfy the strict thesis requirements for verifiable refusal and reproducible test branches.

### 2. Pure LLM-as-a-Judge for Context Grading
- **Pros**: Semantic nuance in deciding if a passage answers a question.
- **Cons**: Adds an extra round-trip LLM latency (1-2s) to every single request.
- **Rejected**: A calibrated vector similarity threshold provides fast, deterministic filtering, and generation prompt grounding handles synthesis.

## Consequences
- Every conversation turn follows a predictable, checkable path.
- Responses on unverified topics fail gracefully with official office hours and human contact channels.
- State fields (`context_sufficient`, `fallback_count`, `citations`) provide measurable variables for research analytics.
