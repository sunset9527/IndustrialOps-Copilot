"""Project persisted work-order state into deterministic v0.7 gates."""

from __future__ import annotations

from industrialops.evaluation.v07.deterministic_gate import HardGateOutcome


def project_work_order_hard_gates(
    *,
    status: str,
    approval_decision: str | None,
    snapshot_hash_before: str,
    snapshot_hash_after: str,
) -> HardGateOutcome:
    """Ensure execution cannot precede approval and snapshots remain immutable."""

    violations: list[str] = []
    executable = {"assigned", "in_progress", "completed", "closed"}
    if status in executable and approval_decision != "approved":
        violations.append("WORK_ORDER_APPROVAL_BYPASS")
    if snapshot_hash_before != snapshot_hash_after:
        violations.append("WORK_ORDER_SNAPSHOT_CHANGED")
    return HardGateOutcome(not violations, tuple(violations))
