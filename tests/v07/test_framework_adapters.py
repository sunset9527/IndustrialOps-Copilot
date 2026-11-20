from __future__ import annotations

from industrialops.evaluation.v07.frameworks import framework_availability


def test_framework_availability_reports_missing_import_without_claiming_a_score() -> None:
    result = framework_availability("definitely_missing_industrialops_framework")

    assert result.status == "framework_unavailable"
    assert result.version is None
    assert result.error_code == "EVALUATION_FRAMEWORK_IMPORT_FAILED"
