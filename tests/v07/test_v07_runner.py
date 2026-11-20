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
