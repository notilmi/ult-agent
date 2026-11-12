from typing import Dict, Any, List
from src.agent.state import AgentState, ULTDocument
from src.db.vectorstore import search_documents

def retrieve(state: AgentState) -> Dict[str, Any]:
    """Retrieves relevant knowledge base passages from NeonDB pgvector."""
    query = state.get("rewritten_query")
    if not query:
        return {"retrieved_documents": []}

    category = state.get("category")
    raw_results = search_documents(query=query, category=category)

    structured_docs: List[ULTDocument] = []
    for doc, score in raw_results:
        meta = doc.metadata or {}
        structured_docs.append({
            "entry_id": str(meta.get("id") or meta.get("entry_id") or "FAQ-GEN"),
            "content": doc.page_content,
            "score": float(score),
            "category": str(meta.get("category", "general")),
            "source_title": str(meta.get("source_title", "Dokumen Resmi ULT Polsri")),
            "source_ref": meta.get("source_ref"),
            "form_url": meta.get("form_url"),
            "responsible_unit": meta.get("responsible_unit"),
            "verified_at": meta.get("verified_at"),
        })

    return {
        "retrieved_documents": structured_docs,
    }
