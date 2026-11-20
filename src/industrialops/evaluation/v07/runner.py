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
) -> dict[str, object]:
    """Write a before-style deterministic run without mutating frozen inputs."""

    verifier = FrozenInputVerifier.capture(frozen_inputs)
    destination = create_run_directory(output_root, run_id)
    cases = tuple(dict(result) for result in case_results)
    frozen_hashes = verifier.verify()
    failed_case_ids = [str(case.get("case_id", "unknown")) for case in cases if case.get("hard_gate_passed") is False]
    report: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "purpose": "before" if run_id.startswith("before-") else "validation",
        "profile": "deterministic",
        "frozen_input_hashes": frozen_hashes,
        "cases": cases,
        "hard_gates": {"passed": not failed_case_ids, "failed_case_ids": failed_case_ids},
    }
    (destination / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
