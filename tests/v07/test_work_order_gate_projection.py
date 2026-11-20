from __future__ import annotations

from industrialops.evaluation.v07.work_order_projection import project_work_order_hard_gates


def test_draft_work_order_is_not_an_approval_bypass() -> None:
    outcome = project_work_order_hard_gates(status="draft", approval_decision=None, snapshot_hash_before="a", snapshot_hash_after="a")

    assert outcome.passed is True
    assert outcome.violation_ids == ()


def test_execution_status_without_approval_is_a_release_blocker() -> None:
    outcome = project_work_order_hard_gates(status="in_progress", approval_decision=None, snapshot_hash_before="a", snapshot_hash_after="a")

    assert outcome.passed is False
    assert outcome.violation_ids == ("WORK_ORDER_APPROVAL_BYPASS",)


def test_snapshot_change_after_approval_is_a_release_blocker() -> None:
    outcome = project_work_order_hard_gates(status="approved", approval_decision="approved", snapshot_hash_before="a", snapshot_hash_after="b")

    assert outcome.passed is False
    assert outcome.violation_ids == ("WORK_ORDER_SNAPSHOT_CHANGED",)
