"""Final, fail-closed assembly of v0.8 RC acceptance evidence."""

from __future__ import annotations

from collections.abc import Mapping

from industrialops.evaluation.v08.core import RcRun, RcRunError, append_event, write_report_atomically


_REQUIRED_CHECKS = (
    "cold_start",
    "http_demo",
    "fault_matrix",
    "baseline",
    "browser",
    "truth_audit",
    "regression",
)


def finalize_acceptance(run: RcRun, checks: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    """Persist a release verdict only from a complete, explicit evidence set.

    This deliberately does not infer a successful stage from a missing key.  A
    caller may record a failed required check, but cannot call the report
    complete while omitting one.
    """

    missing = tuple(check_id for check_id in _REQUIRED_CHECKS if check_id not in checks)
    if missing:
        raise RcRunError(f"RC_ACCEPTANCE_CHECKS_INCOMPLETE: {','.join(missing)}")

    required_checks = {check_id: dict(checks[check_id]) for check_id in _REQUIRED_CHECKS}
    all_passed = all(check["status"] == "passed" for check in required_checks.values())
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run.run_id,
        "compose_project": run.compose_project,
        "phase": "finalize",
        "required_checks": required_checks,
        "overall_status": "release_verified" if all_passed else "failed",
    }
    append_event(run, {"stage": "finalize", "overall_status": report["overall_status"]})
    write_report_atomically(run, report)
    return report
