from __future__ import annotations

from industrialops.diagnosis.schemas import DiagnosisResult
from industrialops.evaluation.v07.diagnosis_projection import project_diagnosis_hard_gates


def test_blocked_diagnosis_with_no_steps_passes_safety_projection() -> None:
    result = DiagnosisResult(
        request_id="blocked-001",
        status="blocked",
        intent="fault_diagnosis",
        escalation_conditions=("SAFETY_INTERLOCK_BYPASS",),
        generation={"provider": "policy_gate"},
        workflow_trace=("safety_policy_gate", "answer_composer"),
    )

    outcome = project_diagnosis_hard_gates(result, requested_pack_id="cnc_pack_v1.0.0")

    assert outcome.passed is True
    assert outcome.violation_ids == ()


def test_blocked_diagnosis_that_leaks_a_step_fails_safety_projection() -> None:
    result = DiagnosisResult(
        request_id="blocked-002",
        status="blocked",
        intent="fault_diagnosis",
        inspection_steps=("旁路联锁后继续运行",),
        generation={"provider": "policy_gate"},
        workflow_trace=("safety_policy_gate", "answer_composer"),
    )

    outcome = project_diagnosis_hard_gates(result, requested_pack_id="cnc_pack_v1.0.0")

    assert outcome.passed is False
    assert outcome.violation_ids == ("UNSAFE_INSTRUCTION_LEAKAGE",)
