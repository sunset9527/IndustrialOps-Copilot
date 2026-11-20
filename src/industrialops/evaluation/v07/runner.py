"""Deterministic v0.7 evaluation orchestration and auditable report writing."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from collections.abc import Iterable, Mapping

from industrialops.evaluation.v07.input_integrity import FrozenInputVerifier
from industrialops.evaluation.v07.run_store import create_run_directory


def run_deterministic_evaluation(
    *,
    output_root: Path,
    run_id: str,
    frozen_inputs: tuple[Path, ...],
    case_results: Iterable[Mapping[str, object]],
    before_run_id: str | None = None,
    profile: str = "deterministic",
    framework_results: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Write a before-style deterministic run without mutating frozen inputs."""

    verifier = FrozenInputVerifier.capture(frozen_inputs)
    destination = create_run_directory(output_root, run_id)
    cases = tuple(dict(result) for result in case_results)
    frozen_hashes = verifier.verify()
    failed_case_ids = [str(case.get("case_id", "unknown")) for case in cases if case.get("hard_gate_passed") is False]
    purpose = "before" if run_id.startswith("before-") else "after" if run_id.startswith("after-") else "validation"
    if purpose == "after" and not before_run_id:
        raise ValueError("EVALUATION_BEFORE_RUN_REQUIRED")
    failure_samples = [
        {"case_id": str(case.get("case_id", "unknown")), "violation_ids": list(case.get("violation_ids", ())) }
        for case in cases
        if case.get("hard_gate_passed") is False
    ]
    if profile not in {"deterministic", "framework-smoke", "judge"}:
        raise ValueError("EVALUATION_PROFILE_INVALID")
    report: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "purpose": purpose,
        "before_run_id": before_run_id,
        "profile": profile,
        "frozen_input_hashes": frozen_hashes,
        "cases": cases,
        "hard_gates": {"passed": not failed_case_ids, "failed_case_ids": failed_case_ids},
        "failure_samples": failure_samples,
        "framework_results": dict(framework_results or {}),
    }
    (destination / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_jsonl(destination / "cases.jsonl", cases)
    _write_jsonl(destination / "failures.jsonl", failure_samples)
    (destination / "environment.json").write_text(
        json.dumps(
            {
                "profile": profile,
                "generated_at_utc": report["generated_at_utc"],
                "frozen_input_count": len(frozen_inputs),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def _write_jsonl(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    """Persist each audited record separately so failures remain inspectable."""

    path.write_text(
        "".join(json.dumps(dict(record), ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
