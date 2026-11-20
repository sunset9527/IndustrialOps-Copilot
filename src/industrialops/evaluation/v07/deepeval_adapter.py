"""Framework-neutral, redacted trace projection for DeepEval."""

from __future__ import annotations

from collections.abc import Iterable

from industrialops.diagnosis.schemas import WorkflowEvent


def to_trace_spans(events: Iterable[WorkflowEvent]) -> tuple[dict[str, object], ...]:
    """Project workflow events without questions, prompts, evidence text, or secrets."""

    return tuple(
        {
            "name": event.node,
            "type": _span_type(event.node),
            "status": event.status,
            "duration_ms": event.duration_ms,
            "input_count": event.input_count,
            "output_count": event.output_count,
            "reason": event.reason,
        }
        for event in events
    )


def _span_type(node: str) -> str:
    if node == "evidence_retriever":
        return "retriever"
    if node == "answer_composer":
        return "llm"
    if node in {"intent_router", "equipment_context_resolver", "safety_policy_gate", "evidence_gap_detector"}:
        return "agent"
    return "workflow"
