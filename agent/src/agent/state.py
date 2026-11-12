from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ULTDocument(TypedDict):
    """Represents a retrieved document chunk with source metadata."""
    entry_id: str
    content: str
    score: float
    category: str
    source_title: str
    source_ref: Optional[str]
    form_url: Optional[str]
    responsible_unit: Optional[str]
    verified_at: Optional[str]

class AgentState(TypedDict):
    """Global conversational and routing state for the ULT Polsri agent."""
    # Conversational message history
    messages: Annotated[List[AnyMessage], add_messages]

    # Query processing & intent mapping
    category: Optional[str]                   # academic, student_affairs, general_admin, unit_info, complaints
    rewritten_query: str                      # Standalone search query resolved from history
    
    # Retrieval & grading
    retrieved_documents: List[ULTDocument]    # Passages retrieved from NeonDB
    context_sufficient: bool                  # True if retrieved context passes relevance threshold

    # Generation & groundedness guards
    generated_answer: Optional[str]           # Response produced by Gemini 3.8 Flash
    citations: List[str]                      # Document sources cited
    guard_warnings: List[str]                 # Warning logs (e.g., PII detected)
    fallback_count: int                       # Count of consecutive unresolved fallbacks
    needs_escalation: bool                    # Trigger for officer contact details

    # Reproducibility & thesis metadata
    prompt_version: str
    model_version: str
    kb_version: str
