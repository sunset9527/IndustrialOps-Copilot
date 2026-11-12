"""LangGraph orchestration for the human work-order approval pause point."""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class ApprovalWorkflowState(TypedDict, total=False):
    """The small, display-safe state required to request a decision."""

    work_order_id: str
    safety_summary: list[str]
    citations: list[dict[str, object]]
    approval_outcome: Literal["approved", "rejected"]


def _await_human_approval(state: ApprovalWorkflowState) -> ApprovalWorkflowState:
    resume = interrupt(
        {
            "work_order_id": state["work_order_id"],
            "safety_summary": state.get("safety_summary", []),
            "citations": state.get("citations", []),
        }
    )
    decision = resume.get("decision") if isinstance(resume, dict) else None
    if decision not in {"approved", "rejected"}:
        raise ValueError("approval decision must be approved or rejected")
    return {"approval_outcome": decision}


def _route_outcome(state: ApprovalWorkflowState) -> Literal["approved", "rejected"]:
    return state["approval_outcome"]


def _finish_approved(_: ApprovalWorkflowState) -> ApprovalWorkflowState:
    return {}


def _finish_rejected(_: ApprovalWorkflowState) -> ApprovalWorkflowState:
    return {}


def build_approval_workflow(checkpointer: BaseCheckpointSaver):
    """Compile a side-effect-free interrupt/resume graph using a durable saver."""

    graph = StateGraph(ApprovalWorkflowState)
    graph.add_node("await_human_approval", _await_human_approval)
    graph.add_node("approved", _finish_approved)
    graph.add_node("rejected", _finish_rejected)
    graph.add_edge(START, "await_human_approval")
    graph.add_conditional_edges(
        "await_human_approval",
        _route_outcome,
        {"approved": "approved", "rejected": "rejected"},
    )
    graph.add_edge("approved", END)
    graph.add_edge("rejected", END)
    return graph.compile(checkpointer=checkpointer)
