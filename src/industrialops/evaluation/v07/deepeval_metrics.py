"""Framework-independent, deterministic workflow metrics for DeepEval reports."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from industrialops.diagnosis.schemas import WorkflowEvent


@dataclass(frozen=True)
class TraceContractResult:
    success: bool
    violation_ids: tuple[str, ...]
    actual_nodes: tuple[str, ...]
    terminal_status: str | None
    terminal_reason: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "success": self.success,
            "violation_ids": list(self.violation_ids),
            "actual_nodes": list(self.actual_nodes),
            "terminal_status": self.terminal_status,
            "terminal_reason": self.terminal_reason,
        }


def evaluate_trace_contract(
    events: Iterable[WorkflowEvent],
    *,
    expected_nodes: tuple[str, ...],
    expected_terminal_status: str,
    expected_reason: str | None = None,
) -> TraceContractResult:
    """Verify observable paths without relying on DeepEval's LLM metrics."""

    observed = tuple(events)
    actual_nodes = tuple(event.node for event in observed)
    terminal = observed[-1] if observed else None
    violations: list[str] = []
    if actual_nodes != expected_nodes:
        violations.append("WORKFLOW_PATH_MISMATCH")
    if terminal is None or terminal.status != expected_terminal_status:
        violations.append("WORKFLOW_TERMINAL_STATUS_MISMATCH")
    if expected_reason is not None and (terminal is None or terminal.reason != expected_reason):
        violations.append("WORKFLOW_REASON_MISMATCH")
    return TraceContractResult(
        success=not violations,
        violation_ids=tuple(violations),
        actual_nodes=actual_nodes,
        terminal_status=terminal.status if terminal else None,
        terminal_reason=terminal.reason if terminal else None,
    )
