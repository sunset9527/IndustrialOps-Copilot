"""Transactional work-order approval and lifecycle services."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from industrialops.domain.work_orders import WorkOrderAction, WorkOrderStatus, transition_work_order
from industrialops.models.work_order import ApprovalDecision, WorkOrder, WorkOrderTransition
from industrialops.models.user import User
from industrialops.services.audit import record_audit_event


class WorkOrderNotFoundError(LookupError):
    code = "work_order_not_found"


class ApprovalAlreadyDecidedError(ValueError):
    code = "approval_already_decided"


class WorkOrderVersionConflictError(ValueError):
    code = "stale_resource_version"


class AssigneeNotFoundError(LookupError):
    code = "assignee_not_found"


def get_work_order(db: Session, work_order_id: str, *, lock: bool = False) -> WorkOrder:
    """Load a work order, optionally taking the database row lock for a mutation."""

    statement = select(WorkOrder).where(WorkOrder.work_order_id == work_order_id)
    if lock:
        statement = statement.with_for_update()
    work_order = db.scalar(statement)
    if work_order is None:
        raise WorkOrderNotFoundError("Work order was not found")
    return work_order


def list_work_orders(
    db: Session,
    *,
    asset_id: str | None = None,
    status: str | None = None,
    created_by_user_id: int | None = None,
    decided_by_user_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[WorkOrder], int]:
    """Return stable work-order pages without exposing implementation-only records."""

    filters = []
    if asset_id is not None:
        filters.append(WorkOrder.asset_id == asset_id)
    if status is not None:
        filters.append(WorkOrder.status == status)
    if created_by_user_id is not None:
        filters.append(WorkOrder.created_by_user_id == created_by_user_id)
    if decided_by_user_id is not None:
        filters.append(ApprovalDecision.decided_by_user_id == decided_by_user_id)
    statement = select(WorkOrder)
    count_statement = select(func.count()).select_from(WorkOrder)
    if decided_by_user_id is not None:
        statement = statement.join(ApprovalDecision)
        count_statement = count_statement.join(ApprovalDecision)
    return (
        list(db.scalars(statement.where(*filters).order_by(WorkOrder.work_order_id).offset(offset).limit(limit))),
        db.scalar(count_statement.where(*filters)) or 0,
    )


def apply_approval_decision(
    db: Session,
    *,
    work_order_id: str,
    actor: User,
    decision: str,
    reason: str | None,
) -> tuple[WorkOrder, bool]:
    """Persist one final decision after its approval graph has resumed.

    A same-decision retry returns the existing work order without adding another
    transition or audit record.  A contradictory retry has a stable conflict code.
    """

    work_order = get_work_order(db, work_order_id, lock=True)
    existing = db.scalar(select(ApprovalDecision).where(ApprovalDecision.work_order_id == work_order_id))
    if existing is not None:
        if existing.decision == decision:
            return work_order, False
        raise ApprovalAlreadyDecidedError("Approval has already been decided")

    action = WorkOrderAction.APPROVE if decision == "approved" else WorkOrderAction.REJECT
    next_status = transition_work_order(
        WorkOrderStatus(work_order.status), action, actor_role=actor.role, actor_is_assignee=False
    )
    work_order.status = str(next_status)
    work_order.version += 1
    db.add(ApprovalDecision(
        work_order_id=work_order.work_order_id,
        thread_id=work_order.thread_id,
        decision=decision,
        reason=reason,
        decided_by_user_id=actor.id,
    ))
    db.add(WorkOrderTransition(
        work_order_id=work_order.work_order_id,
        action=str(action),
        from_status=WorkOrderStatus.DRAFT,
        to_status=str(next_status),
        actor_user_id=actor.id,
        reason=reason,
    ))
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=f"work_order.{decision}",
        subject_type="work_order",
        subject_id=work_order.work_order_id,
        detail=f'{{"thread_id":"{work_order.thread_id}","from_status":"draft","to_status":"{next_status}"}}',
    )
    db.flush()
    return work_order, True


def transition_existing_work_order(
    db: Session,
    *,
    work_order_id: str,
    actor: User,
    action: WorkOrderAction,
    expected_version: int,
    reason: str | None,
    assignee_username: str | None = None,
) -> WorkOrder:
    """Apply one non-approval lifecycle action with version and role checks."""

    work_order = get_work_order(db, work_order_id, lock=True)
    if work_order.version != expected_version:
        raise WorkOrderVersionConflictError("Work order has changed since it was read")
    assignee: User | None = None
    if action is WorkOrderAction.ASSIGN:
        if not assignee_username:
            raise AssigneeNotFoundError("An assignee username is required")
        assignee = db.scalar(select(User).where(User.username == assignee_username))
        if assignee is None:
            raise AssigneeNotFoundError("Assignee was not found")

    current = WorkOrderStatus(work_order.status)
    next_status = transition_work_order(
        current,
        action,
        actor_role=actor.role,
        actor_is_assignee=work_order.assigned_to_user_id == actor.id,
    )
    if assignee is not None:
        work_order.assigned_to_user_id = assignee.id
    work_order.status = str(next_status)
    work_order.version += 1
    now = datetime.now(timezone.utc)
    if next_status is WorkOrderStatus.COMPLETED:
        work_order.completed_at = now
    elif next_status is WorkOrderStatus.CLOSED:
        work_order.closed_at = now
    db.add(WorkOrderTransition(
        work_order_id=work_order.work_order_id,
        action=str(action),
        from_status=str(current),
        to_status=str(next_status),
        actor_user_id=actor.id,
        reason=reason,
    ))
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action="work_order.transitioned",
        subject_type="work_order",
        subject_id=work_order.work_order_id,
        detail=f'{{"thread_id":"{work_order.thread_id}","action":"{action}","from_status":"{current}","to_status":"{next_status}"}}',
    )
    db.flush()
    return work_order
