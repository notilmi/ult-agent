import logging
from typing import Dict, Any
from src.agent.state import AgentState
from src.config import SIMILARITY_SCORE_THRESHOLD

logger = logging.getLogger(__name__)

def grade_context(state: AgentState) -> Dict[str, Any]:
    """
    Evaluates whether the retrieved documents provide sufficient context to answer the user inquiry.
    Combines numeric similarity score threshold with presence of valid content.
    """
    # If user explicitly asked for escalation or complaint, skip to escalate branch
    if state.get("needs_escalation"):
        return {"context_sufficient": False}

    docs = state.get("retrieved_documents", [])
    if not docs:
        return {"context_sufficient": False}

    # Check if the best matching document passes the calibrated similarity threshold
    best_score = max(d.get("score", 0.0) for d in docs)
    logger.info(f"Context grading: top similarity score = {best_score:.3f} (threshold: {SIMILARITY_SCORE_THRESHOLD})")

    # If the score is sufficient, allow generation
    is_sufficient = best_score >= SIMILARITY_SCORE_THRESHOLD

    return {
        "context_sufficient": is_sufficient,
    }
