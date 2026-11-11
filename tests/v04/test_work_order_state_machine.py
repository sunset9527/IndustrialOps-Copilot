from __future__ import annotations

import pytest

from industrialops.domain.work_orders import (
    WorkOrderAction,
    WorkOrderStatus,
    WorkOrderTransitionError,
    transition_work_order,
)


@pytest.mark.parametrize(
    ("current", "action", "role", "is_assignee", "expected"),
    [
        (WorkOrderStatus.DRAFT, WorkOrderAction.APPROVE, "approver", False, WorkOrderStatus.APPROVED),
        (WorkOrderStatus.DRAFT, WorkOrderAction.APPROVE, "admin", False, WorkOrderStatus.APPROVED),
        (WorkOrderStatus.DRAFT, WorkOrderAction.REJECT, "approver", False, WorkOrderStatus.CANCELLED),
        (WorkOrderStatus.APPROVED, WorkOrderAction.ASSIGN, "admin", False, WorkOrderStatus.ASSIGNED),
        (WorkOrderStatus.ASSIGNED, WorkOrderAction.START, "user", True, WorkOrderStatus.IN_PROGRESS),
        (WorkOrderStatus.IN_PROGRESS, WorkOrderAction.COMPLETE, "user", True, WorkOrderStatus.COMPLETED),
        (WorkOrderStatus.COMPLETED, WorkOrderAction.CLOSE, "approver", False, WorkOrderStatus.CLOSED),
        (WorkOrderStatus.COMPLETED, WorkOrderAction.CLOSE, "admin", False, WorkOrderStatus.CLOSED),
        (WorkOrderStatus.DRAFT, WorkOrderAction.CANCEL, "admin", False, WorkOrderStatus.CANCELLED),
        (WorkOrderStatus.APPROVED, WorkOrderAction.CANCEL, "admin", False, WorkOrderStatus.CANCELLED),
        (WorkOrderStatus.ASSIGNED, WorkOrderAction.CANCEL, "admin", False, WorkOrderStatus.CANCELLED),
        (WorkOrderStatus.IN_PROGRESS, WorkOrderAction.CANCEL, "admin", False, WorkOrderStatus.CANCELLED),
    ],
)
def test_transition_work_order_allows_only_the_declared_lifecycle(
    current: WorkOrderStatus,
    action: WorkOrderAction,
    role: str,
    is_assignee: bool,
    expected: WorkOrderStatus,
) -> None:
    assert transition_work_order(current, action, actor_role=role, actor_is_assignee=is_assignee) is expected


@pytest.mark.parametrize(
    ("current", "action", "role", "is_assignee"),
    [
        (WorkOrderStatus.DRAFT, WorkOrderAction.APPROVE, "user", False),
        (WorkOrderStatus.DRAFT, WorkOrderAction.ASSIGN, "admin", False),
        (WorkOrderStatus.APPROVED, WorkOrderAction.START, "user", True),
        (WorkOrderStatus.ASSIGNED, WorkOrderAction.START, "user", False),
        (WorkOrderStatus.IN_PROGRESS, WorkOrderAction.COMPLETE, "approver", False),
        (WorkOrderStatus.COMPLETED, WorkOrderAction.CLOSE, "user", False),
        (WorkOrderStatus.CLOSED, WorkOrderAction.CANCEL, "admin", False),
        (WorkOrderStatus.CANCELLED, WorkOrderAction.APPROVE, "admin", False),
    ],
)
def test_transition_work_order_rejects_invalid_state_or_role_combinations(
    current: WorkOrderStatus,
    action: WorkOrderAction,
    role: str,
    is_assignee: bool,
) -> None:
    with pytest.raises(WorkOrderTransitionError) as error:
        transition_work_order(current, action, actor_role=role, actor_is_assignee=is_assignee)

    assert error.value.code == "invalid_work_order_transition"


def test_ordinary_user_cannot_cancel_a_work_order_even_when_assigned() -> None:
    with pytest.raises(WorkOrderTransitionError) as error:
        transition_work_order(
            WorkOrderStatus.ASSIGNED,
            WorkOrderAction.CANCEL,
            actor_role="user",
            actor_is_assignee=True,
        )

    assert error.value.code == "invalid_work_order_transition"
