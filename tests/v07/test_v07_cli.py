from __future__ import annotations

from industrialops.evaluation.v07.run import framework_smoke_cases


def test_framework_smoke_cases_keep_missing_optional_frameworks_out_of_hard_gate_denominator() -> None:
    cases, results = framework_smoke_cases()

    assert {case["case_id"] for case in cases} == {"framework-ragas", "framework-deepeval"}
    assert all(case["hard_gate_passed"] is True for case in cases)
    assert set(results) == {"ragas", "deepeval"}
