from __future__ import annotations

from industrialops.evaluation.v07.deterministic_gate import evaluate_hard_gates


def test_cross_pack_citation_is_a_release_blocking_violation() -> None:
    outcome = evaluate_hard_gates(
        requested_pack_id="cnc_pack_v1.0.0",
        citation_pack_ids=("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"),
        unsafe_instruction_leaked=False,
        work_order_executed_before_approval=False,
    )

    assert outcome.passed is False
    assert outcome.violation_ids == ("PACK_CONTAMINATION",)


def test_clean_deterministic_outcome_passes_all_release_hard_gates() -> None:
    outcome = evaluate_hard_gates(
        requested_pack_id="cnc_pack_v1.0.0",
        citation_pack_ids=("cnc_pack_v1.0.0",),
        unsafe_instruction_leaked=False,
        work_order_executed_before_approval=False,
    )

    assert outcome.passed is True
    assert outcome.violation_ids == ()
