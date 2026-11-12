"""
LangGraph Application Definition for ULT Polsri AI Service Agent
Configured to be served via LangGraph Server and accessible through LangChain Agent Chat UI.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from src.agent.state import AgentState
from src.agent.nodes.guards import input_guard, output_guard
from src.agent.nodes.query import query_refine
from src.agent.nodes.retrieval import retrieve
from src.agent.nodes.grading import grade_context
from src.agent.nodes.generation import generate_answer
from src.agent.nodes.fallback_escalate import fallback, escalate

def route_after_input_guard(state: AgentState) -> Literal["query_refine", "__end__"]:
    """If input guard halted on prompt injection or off-topic abuse, route directly to END."""
    messages = state.get("messages", [])
    if messages and messages[-1].type == "ai":
        return END
    return "query_refine"

def route_after_query_refine(state: AgentState) -> Literal["retrieve", "escalate"]:
    """Routes directly to human officer escalation if requested or complaint category."""
    if state.get("needs_escalation", False):
        return "escalate"
    return "retrieve"

def route_after_grading(state: AgentState) -> Literal["generate_answer", "fallback"]:
    """Routes to generation if context is sufficient; otherwise routes to honest fallback."""
    if state.get("context_sufficient", False):
        return "generate_answer"
    return "fallback"

def route_after_fallback(state: AgentState) -> Literal["escalate", "__end__"]:
    """Routes to escalation if repeated fallbacks exceeded threshold; otherwise ends turn."""
    if state.get("needs_escalation", False):
        return "escalate"
    return END

def build_graph():
    """Builds and compiles the ULT Polsri StateGraph."""
    builder = StateGraph(AgentState)

    # 1. Register nodes
    builder.add_node("input_guard", input_guard)
    builder.add_node("query_refine", query_refine)
    builder.add_node("retrieve", retrieve)
    builder.add_node("grade_context", grade_context)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("output_guard", output_guard)
    builder.add_node("fallback", fallback)
    builder.add_node("escalate", escalate)

    # 2. Wire edges
    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {
            "query_refine": "query_refine",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "query_refine",
        route_after_query_refine,
        {
            "retrieve": "retrieve",
            "escalate": "escalate",
        },
    )
    builder.add_edge("retrieve", "grade_context")
    builder.add_conditional_edges(
        "grade_context",
        route_after_grading,
        {
            "generate_answer": "generate_answer",
            "fallback": "fallback",
        },
    )
    builder.add_edge("generate_answer", "output_guard")
    builder.add_edge("output_guard", END)
    builder.add_conditional_edges(
        "fallback",
        route_after_fallback,
        {
            "escalate": "escalate",
            END: END,
        },
    )
    builder.add_edge("escalate", END)

    # Compile graph without checkpointer: LangGraph Server (langgraph dev)
    # automatically provides persistence and thread state management.
    compiled_graph = builder.compile()
    return compiled_graph

# Expose compiled graph instance for LangGraph Server / Agent Chat UI
graph = build_graph()
