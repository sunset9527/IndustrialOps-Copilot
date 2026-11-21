"""Small, side-effect-bounded primitives for RC acceptance runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
from uuid import uuid4

from industrialops.services.error_sanitizer import redact_sensitive_text


_RUN_ID_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SECRET_KEY_PATTERN = re.compile(r"(?:api[_-]?key|password|secret|token)$", re.IGNORECASE)


class RcRunError(ValueError):
    """An RC operation would violate isolation or report-history rules."""


@dataclass(frozen=True)
class RcRun:
    """Resources and report location exclusively owned by one RC run."""

    run_id: str
    compose_project: str
    report_directory: Path

    def owns_resource(self, resource_name: str) -> bool:
        """Return whether a Compose resource is safely attributable to this run."""

        return resource_name.startswith(f"{self.compose_project}-") or resource_name.startswith(
            f"{self.compose_project}_"
        )


def create_rc_run(output_root: Path, run_id: str) -> RcRun:
    """Reserve a fresh report directory and derive a non-default Compose identity."""

    if not _is_safe_run_id(run_id):
        raise RcRunError(f"RC_RUN_ID_INVALID: {run_id}")
    report_directory = output_root / run_id
    if report_directory.exists():
        raise RcRunError(f"RC_RUN_ALREADY_EXISTS: {run_id}")
    report_directory.mkdir(parents=True)
    return RcRun(
        run_id=run_id,
        compose_project=f"industrialops_rc_{run_id.replace('-', '_')}",
        report_directory=report_directory,
    )


def write_report_atomically(run: RcRun, report: dict[str, object]) -> Path:
    """Publish one sanitized JSON report without replacing existing evidence."""

    report_path = run.report_directory / "report.json"
    if report_path.exists():
        raise RcRunError("RC_REPORT_ALREADY_EXISTS")
    payload = _sanitize_value(report)
    temporary_path = run.report_directory / f".report-{uuid4().hex}.json"
    try:
        temporary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary_path.replace(report_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return report_path


def append_event(run: RcRun, event: dict[str, object]) -> Path:
    """Append one sanitized stage event so partial RC evidence survives later failures."""

    event_path = run.report_directory / "events.jsonl"
    line = json.dumps(_sanitize_value(event), ensure_ascii=False) + "\n"
    with event_path.open("a", encoding="utf-8") as stream:
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())
    return event_path


def summarize_latency_ms(samples: list[float]) -> dict[str, float | int]:
    """Summarize observed samples using the nearest-rank p95 without a pass threshold."""

    if not samples:
        raise RcRunError("RC_LATENCY_SAMPLES_REQUIRED")
    ordered = sorted(float(sample) for sample in samples)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    p95_index = math.ceil(len(ordered) * 0.95) - 1
    return {
        "sample_count": len(ordered),
        "minimum_ms": ordered[0],
        "median_ms": median,
        "p95_ms": ordered[p95_index],
        "maximum_ms": ordered[-1],
    }


def assess_fault_scenario(
    *,
    expected_code: str,
    observed_code: str,
    recovered: bool,
    safety_violation_ids: tuple[str, ...],
) -> dict[str, str]:
    """Classify a controlled fault only when failure, safety, and recovery all agree."""

    if safety_violation_ids:
        return {"status": "failed", "reason_code": "RC_FAULT_SAFETY_VIOLATION"}
    if observed_code != expected_code:
        return {"status": "failed", "reason_code": "RC_FAULT_UNEXPECTED_CODE"}
    if not recovered:
        return {"status": "failed", "reason_code": "RC_FAULT_RECOVERY_FAILED"}
    return {"status": "passed", "reason_code": "RC_FAULT_EXPECTED_AND_RECOVERED"}


def _is_safe_run_id(run_id: str) -> bool:
    return bool(_RUN_ID_PATTERN.fullmatch(run_id)) and run_id != "industrialops"


def _sanitize_value(value: object, *, key: str | None = None) -> object:
    if key and _SECRET_KEY_PATTERN.search(key):
        return "[REDACTED_TOKEN]" if key.lower() == "authorization" else "[REDACTED_SECRET]"
    if isinstance(value, dict):
        return {str(item_key): _sanitize_value(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value, max_length=10_000)
    return value
