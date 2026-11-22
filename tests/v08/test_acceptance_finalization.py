from __future__ import annotations

import pytest

from industrialops.evaluation.v08.acceptance import finalize_acceptance
from industrialops.evaluation.v08.core import RcRunError, create_rc_run


def test_finalization_marks_release_verified_only_when_every_required_check_passes(tmp_path) -> None:
    run = create_rc_run(tmp_path, "v08-final-acceptance")

    report = finalize_acceptance(
        run,
        {
            check_id: {"status": "passed", "evidence": f"{check_id}-evidence"}
            for check_id in (
                "cold_start", "http_demo", "fault_matrix", "baseline", "browser", "truth_audit", "regression"
            )
        },
    )

    assert report["overall_status"] == "release_verified"
    assert report["required_checks"]["browser"]["status"] == "passed"


def test_finalization_refuses_missing_or_failed_required_checks(tmp_path) -> None:
    run = create_rc_run(tmp_path, "v08-final-missing")

    with pytest.raises(RcRunError, match="RC_ACCEPTANCE_CHECKS_INCOMPLETE"):
        finalize_acceptance(run, {"cold_start": {"status": "passed"}})

    failed = create_rc_run(tmp_path, "v08-final-failed")
    report = finalize_acceptance(
        failed,
        {
            check_id: {"status": "failed" if check_id == "browser" else "passed"}
            for check_id in (
                "cold_start", "http_demo", "fault_matrix", "baseline", "browser", "truth_audit", "regression"
            )
        },
    )
    assert report["overall_status"] == "failed"
