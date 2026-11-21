from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrialops.evaluation.v08.core import (
    RcRunError,
    append_event,
    assess_fault_scenario,
    create_rc_run,
    summarize_latency_ms,
    write_report_atomically,
)


def test_rc_run_owns_only_a_unique_non_default_compose_project(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-smoke")

    assert run.run_id == "20261121-smoke"
    assert run.compose_project == "industrialops_rc_20261121_smoke"
    assert run.report_directory == tmp_path / "20261121-smoke"
    assert run.owns_resource("industrialops_rc_20261121_smoke-db-1") is True
    assert run.owns_resource("industrialops-db-1") is False

    with pytest.raises(RcRunError, match="RC_RUN_ALREADY_EXISTS"):
        create_rc_run(tmp_path, "20261121-smoke")


def test_rc_run_rejects_a_default_or_unsafe_compose_identity(tmp_path: Path) -> None:
    with pytest.raises(RcRunError, match="RC_RUN_ID_INVALID"):
        create_rc_run(tmp_path, "industrialops")

    with pytest.raises(RcRunError, match="RC_RUN_ID_INVALID"):
        create_rc_run(tmp_path, "../../existing-project")


def test_atomic_report_write_redacts_sensitive_values_and_refuses_replacement(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-report")
    report = {
        "run_id": run.run_id,
        "database_url": "mysql+pymysql://user:secret@localhost/industrialops",
        "api_key": "deepseek-secret",
        "model_path": r"E:\huggingface\model",
        "nested": {"authorization": "Bearer super-secret-token"},
    }

    report_path = write_report_atomically(run, report)
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert saved["database_url"] == "[REDACTED_DATABASE_URL]"
    assert saved["api_key"] == "[REDACTED_SECRET]"
    assert saved["model_path"] == "[REDACTED_PATH]"
    assert saved["nested"]["authorization"] == "[REDACTED_TOKEN]"

    with pytest.raises(RcRunError, match="RC_REPORT_ALREADY_EXISTS"):
        write_report_atomically(run, {"run_id": run.run_id})


def test_event_stream_is_append_only_and_redacts_each_partial_result(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-events")

    event_path = append_event(run, {"stage": "preflight", "status": "passed"})
    append_event(run, {"stage": "cold_start", "status": "failed", "error": "Bearer partial-secret"})

    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
    assert events == [
        {"stage": "preflight", "status": "passed"},
        {"stage": "cold_start", "status": "failed", "error": "[REDACTED_TOKEN]"},
    ]


def test_latency_summary_uses_documented_nearest_rank_percentile_without_threshold() -> None:
    summary = summarize_latency_ms([11.0, 2.0, 7.0, 20.0, 5.0])

    assert summary == {
        "sample_count": 5,
        "minimum_ms": 2.0,
        "median_ms": 7.0,
        "p95_ms": 20.0,
        "maximum_ms": 20.0,
    }


def test_fault_assessment_requires_expected_failure_and_successful_recovery() -> None:
    passed = assess_fault_scenario(
        expected_code="MODEL_BGE_MISSING",
        observed_code="MODEL_BGE_MISSING",
        recovered=True,
        safety_violation_ids=(),
    )
    unexpected_code = assess_fault_scenario(
        expected_code="MODEL_BGE_MISSING",
        observed_code="INTERNAL_ERROR",
        recovered=True,
        safety_violation_ids=(),
    )
    unsafe = assess_fault_scenario(
        expected_code="LLM_TIMEOUT",
        observed_code="LLM_TIMEOUT",
        recovered=True,
        safety_violation_ids=("CROSS_PACK_CITATION",),
    )

    assert passed == {"status": "passed", "reason_code": "RC_FAULT_EXPECTED_AND_RECOVERED"}
    assert unexpected_code == {"status": "failed", "reason_code": "RC_FAULT_UNEXPECTED_CODE"}
    assert unsafe == {"status": "failed", "reason_code": "RC_FAULT_SAFETY_VIOLATION"}
