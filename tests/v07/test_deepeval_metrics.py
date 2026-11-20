from __future__ import annotations

from industrialops.diagnosis.schemas import WorkflowEvent
from industrialops.evaluation.v07.deepeval_metrics import evaluate_trace_contract


def test_trace_contract_accepts_expected_safety_short_circuit() -> None:
    result = evaluate_trace_contract(
        (
            WorkflowEvent(node="intent_router", status="completed", duration_ms=0.1, input_count=1, output_count=1),
            WorkflowEvent(node="safety_policy_gate", status="blocked", duration_ms=0.1, input_count=1, output_count=1, reason="SAFETY_INTERLOCK_BYPASS"),
            WorkflowEvent(node="answer_composer", status="blocked", duration_ms=0.1, input_count=1, output_count=1, reason="SAFETY_INTERLOCK_BYPASS"),
        ),
        expected_nodes=("intent_router", "safety_policy_gate", "answer_composer"),
        expected_terminal_status="blocked",
        expected_reason="SAFETY_INTERLOCK_BYPASS",
    )

    assert result.success is True
    assert result.violation_ids == ()


def test_trace_contract_reports_unexpected_path_and_reason_without_a_judge() -> None:
    result = evaluate_trace_contract(
        (WorkflowEvent(node="intent_router", status="completed", duration_ms=0.1, input_count=1, output_count=1),),
        expected_nodes=("intent_router", "safety_policy_gate", "answer_composer"),
        expected_terminal_status="blocked",
        expected_reason="SAFETY_INTERLOCK_BYPASS",
    )

    assert result.success is False
    assert result.violation_ids == ("WORKFLOW_PATH_MISMATCH", "WORKFLOW_TERMINAL_STATUS_MISMATCH", "WORKFLOW_REASON_MISMATCH")
