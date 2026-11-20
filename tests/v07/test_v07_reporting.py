from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrialops.evaluation.v07.run_store import RunStoreError, create_run_directory
from industrialops.evaluation.v07.runner import run_deterministic_evaluation


def test_run_store_never_overwrites_an_existing_run_directory(tmp_path: Path) -> None:
    create_run_directory(tmp_path, "before-001")

    with pytest.raises(RunStoreError, match="EVALUATION_RUN_ALREADY_EXISTS"):
        create_run_directory(tmp_path, "before-001")


def test_after_report_requires_a_before_run_and_preserves_failure_samples(tmp_path: Path) -> None:
    source = tmp_path / "frozen.jsonl"
    source.write_text('{}\n', encoding="utf-8")

    report = run_deterministic_evaluation(
        output_root=tmp_path / "reports",
        run_id="after-001",
        frozen_inputs=(source,),
        case_results=({"case_id": "case-1", "hard_gate_passed": False, "violation_ids": ["PACK_CONTAMINATION"]},),
        before_run_id="before-001",
    )

    assert report["before_run_id"] == "before-001"
    assert report["failure_samples"] == [{"case_id": "case-1", "violation_ids": ["PACK_CONTAMINATION"]}]
    destination = tmp_path / "reports" / "after-001"
    assert json.loads((destination / "cases.jsonl").read_text(encoding="utf-8")) == {
        "case_id": "case-1", "hard_gate_passed": False, "violation_ids": ["PACK_CONTAMINATION"]
    }
    assert json.loads((destination / "failures.jsonl").read_text(encoding="utf-8")) == {
        "case_id": "case-1", "violation_ids": ["PACK_CONTAMINATION"]
    }
    assert json.loads((destination / "environment.json").read_text(encoding="utf-8"))["profile"] == "deterministic"
