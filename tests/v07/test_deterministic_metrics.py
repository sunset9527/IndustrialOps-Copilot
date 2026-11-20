from __future__ import annotations

import pytest

from industrialops.evaluation.v07.deterministic_metrics import (
    binary_metric,
    inspection_evidence_coverage,
    retrieval_metrics,
)


def test_binary_metric_excludes_not_run_cases_from_its_denominator() -> None:
    result = binary_metric(
        "model_compatibility_accuracy",
        (("compatible", True), ("out_of_scope", True), ("not-run", None), ("wrong", False)),
    )

    assert result.as_dict() == {
        "name": "model_compatibility_accuracy",
        "status": "completed",
        "numerator": 2,
        "denominator": 3,
        "rate": 2 / 3,
        "passed_case_ids": ["compatible", "out_of_scope"],
        "failed_case_ids": ["wrong"],
        "not_run_case_ids": ["not-run"],
        "not_run_reasons": {},
    }


def test_binary_metric_without_applicable_cases_is_not_run_not_zero() -> None:
    result = binary_metric("safety_prerequisite_coverage", (("no-safety", None),))

    assert result.status == "not_run"
    assert result.denominator == 0
    assert result.rate is None
    assert result.not_run_case_ids == ("no-safety",)


def test_inspection_coverage_counts_supported_steps_without_double_counting() -> None:
    result = inspection_evidence_coverage(
        "case-1",
        inspection_steps=("inspect pump", "check pressure", "inspect pump"),
        supported_steps=("inspect pump",),
    )

    assert result.as_dict()["numerator"] == 1
    assert result.as_dict()["denominator"] == 2
    assert result.as_dict()["rate"] == 0.5


def test_retrieval_metrics_report_source_page_mrr_and_ndcg_from_ranked_evidence() -> None:
    result = retrieval_metrics(
        (
            (
                "case-1",
                (
                    {"source_id": "other", "page_number": 1},
                    {"source_id": "source-a", "page_number": 7},
                ),
                {"source-a"},
                {7},
            ),
        )
    )

    assert result["source_hit_at_1"].rate == 0.0
    assert result["source_hit_at_3"].rate == 1.0
    assert result["page_hit_at_3"].rate == 1.0
    assert result["mrr"].rate == 0.5
    assert result["ndcg_at_5"].rate == pytest.approx(1 / 1.5849625007211563)
