"""Deterministic work-order lifecycle rules independent of persistence."""

from __future__ import annotations

from enum import StrEnum


class WorkOrderStatus(StrEnum):
    """The only lifecycle states supported by the v0.4 work-order model."""

    DRAFT = "draft"
    APPROVED = "approved"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class WorkOrderAction(StrEnum):
    """Named transitions rather than client-supplied target statuses."""

    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    START = "start"
    COMPLETE = "complete"
    CLOSE = "close"
    CANCEL = "cancel"


class WorkOrderTransitionError(ValueError):
    """A stable domain error for any forbidden lifecycle transition."""

    code = "invalid_work_order_transition"


def transition_work_order(
    current: WorkOrderStatus,
    action: WorkOrderAction,
    *,
    actor_role: str,
    actor_is_assignee: bool,
) -> WorkOrderStatus:
    """Return the next status only when actor and source status are permitted."""

    if action is WorkOrderAction.APPROVE:
        return _require(current, WorkOrderStatus.DRAFT, actor_role in {"approver", "admin"}, WorkOrderStatus.APPROVED)
    if action is WorkOrderAction.REJECT:
        return _require(current, WorkOrderStatus.DRAFT, actor_role in {"approver", "admin"}, WorkOrderStatus.CANCELLED)
    if action is WorkOrderAction.ASSIGN:
        return _require(current, WorkOrderStatus.APPROVED, actor_role == "admin", WorkOrderStatus.ASSIGNED)
    if action is WorkOrderAction.START:
        return _require(current, WorkOrderStatus.ASSIGNED, actor_is_assignee, WorkOrderStatus.IN_PROGRESS)
    if action is WorkOrderAction.COMPLETE:
        return _require(current, WorkOrderStatus.IN_PROGRESS, actor_is_assignee, WorkOrderStatus.COMPLETED)
    if action is WorkOrderAction.CLOSE:
        return _require(current, WorkOrderStatus.COMPLETED, actor_role in {"approver", "admin"}, WorkOrderStatus.CLOSED)
    if action is WorkOrderAction.CANCEL:
        return _require(
            current,
            {WorkOrderStatus.DRAFT, WorkOrderStatus.APPROVED, WorkOrderStatus.ASSIGNED, WorkOrderStatus.IN_PROGRESS},
            actor_role == "admin",
            WorkOrderStatus.CANCELLED,
        )
    raise WorkOrderTransitionError("Unknown work-order action")


def _require(
    current: WorkOrderStatus,
    allowed_statuses: WorkOrderStatus | set[WorkOrderStatus],
    allowed_actor: bool,
    next_status: WorkOrderStatus,
) -> WorkOrderStatus:
    statuses = {allowed_statuses} if isinstance(allowed_statuses, WorkOrderStatus) else allowed_statuses
    if current not in statuses or not allowed_actor:
        raise WorkOrderTransitionError("The requested work-order transition is not allowed")
    return next_status
