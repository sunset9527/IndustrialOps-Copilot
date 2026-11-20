from __future__ import annotations

from pathlib import Path

from industrialops.evaluation.v07.runner import run_deterministic_evaluation


def test_deterministic_runner_records_before_run_with_frozen_input_hashes(tmp_path: Path) -> None:
    scenario = tmp_path / "scenario_eval_v1.jsonl"
    guardrail = tmp_path / "guardrail_eval_v1.jsonl"
    scenario.write_text('{"eval_id":"retrieve-1"}\n', encoding="utf-8")
    guardrail.write_text('{"eval_id":"guardrail-1"}\n', encoding="utf-8")

    report = run_deterministic_evaluation(
        output_root=tmp_path / "reports",
        run_id="before-001",
        frozen_inputs=(scenario, guardrail),
        case_results=(),
    )

    assert report["purpose"] == "before"
    assert report["hard_gates"]["passed"] is True
    assert report["frozen_input_hashes"][str(scenario)]
    assert (tmp_path / "reports" / "before-001" / "report.json").exists()


def test_deterministic_runner_fails_report_when_any_case_fails_a_hard_gate(tmp_path: Path) -> None:
    scenario = tmp_path / "scenario_eval_v1.jsonl"
    scenario.write_text('{"eval_id":"retrieve-1"}\n', encoding="utf-8")

    report = run_deterministic_evaluation(
        output_root=tmp_path / "reports",
        run_id="before-unsafe-001",
        frozen_inputs=(scenario,),
        case_results=({"case_id": "unsafe-1", "hard_gate_passed": False, "violation_ids": ["UNSAFE_INSTRUCTION_LEAKAGE"]},),
    )

    assert report["hard_gates"]["passed"] is False
    assert report["hard_gates"]["failed_case_ids"] == ["unsafe-1"]


def test_runner_records_framework_smoke_as_a_distinct_profile(tmp_path: Path) -> None:
    scenario = tmp_path / "scenario.jsonl"
    scenario.write_text('{}\n', encoding="utf-8")

    report = run_deterministic_evaluation(
        output_root=tmp_path / "reports",
        run_id="validation-framework-001",
        frozen_inputs=(scenario,),
        case_results=({"case_id": "framework-smoke", "hard_gate_passed": True},),
        profile="framework-smoke",
        framework_results={"ragas": {"status": "available", "version": "0.4.4"}},
    )

    assert report["profile"] == "framework-smoke"
    assert report["framework_results"] == {"ragas": {"status": "available", "version": "0.4.4"}}
