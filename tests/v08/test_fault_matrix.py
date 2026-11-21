from __future__ import annotations

from industrialops.evaluation.v08.fault_matrix import evaluate_fault_matrix


def test_fault_matrix_passes_only_when_every_declared_scenario_is_observed_and_recovered() -> None:
    result = evaluate_fault_matrix(
        {
            "missing_models": {"observed_code": "MODEL_UNAVAILABLE", "recovered": True, "safety_violation_ids": ()},
            "missing_pack": {"observed_code": "PACK_UNAVAILABLE", "recovered": True, "safety_violation_ids": ()},
            "corrupt_index": {"observed_code": "INDEX_UNAVAILABLE", "recovered": True, "safety_violation_ids": ()},
            "database_unavailable": {"observed_code": "DATABASE_UNAVAILABLE", "recovered": True, "safety_violation_ids": ()},
            "llm_timeout": {"observed_code": "DEEPSEEK_UNAVAILABLE", "recovered": True, "safety_violation_ids": ()},
            "llm_error": {"observed_code": "DEEPSEEK_REQUEST_REJECTED", "recovered": True, "safety_violation_ids": ()},
            "offline_egress_decoy": {"observed_code": "RC_OFFLINE_ZERO_EGRESS", "recovered": True, "safety_violation_ids": ()},
        }
    )

    assert result.passed is True
    assert all(row["status"] == "passed" for row in result.rows)


def test_fault_matrix_fails_closed_when_a_required_scenario_was_not_executed() -> None:
    result = evaluate_fault_matrix({})

    assert result.passed is False
    assert result.by_scenario("missing_models") == {
        "scenario_id": "missing_models",
        "status": "failed",
        "reason_code": "RC_FAULT_SCENARIO_NOT_EXECUTED",
    }


def test_fault_matrix_preserves_safety_failure_over_other_success_signals() -> None:
    result = evaluate_fault_matrix(
        {
            "missing_models": {
                "observed_code": "MODEL_UNAVAILABLE",
                "recovered": True,
                "safety_violation_ids": ("UNSAFE_INSTRUCTION_LEAKAGE",),
            }
        }
    )

    assert result.passed is False
    assert result.by_scenario("missing_models")["reason_code"] == "RC_FAULT_SAFETY_VIOLATION"
