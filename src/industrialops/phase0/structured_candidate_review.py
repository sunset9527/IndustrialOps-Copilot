"""Conservatively decide whether structured candidates can enter later formal review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


_ALLOWED_PACKS = {"cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"}
_OUT_OF_SCOPE_MARKERS = (
    "smtc",
    "tsc",
    "robot",
    "pallet",
    "4th axis",
    "5th axis",
    "fourth axis",
    "fifth axis",
    "第四轴",
    "第五轴",
    "机器人",
    "托盘",
    "serial option",
    "remote option",
    "远程选件",
    "串口选件",
    "umc-",
    "gm-",
    "dc-",
    "st-",
    "lathe",
    "turning center",
)
_NAVIGATION_MARKERS = ("table of contents", "contents\n", "目录\n", "order information", "订货信息")
_DANGEROUS_ACTIONS = ("remove", "replace", "disassemble", "open", "拆卸", "更换", "打开")
_SAFETY_PREREQUISITES = ("lockout", "lock out", "disconnect power", "depressur", "isolate", "隔离", "断开电源", "泄压")
_REQUIRED_FIELDS = (
    "candidate_id",
    "candidate_type",
    "candidate_status",
    "pack_id",
    "label",
    "source_record_id",
    "source_id",
    "source_file",
    "source_sha256",
    "page_number",
    "evidence_locator",
    "evidence_text",
    "text_zh",
    "extraction_reason",
)


def review_structured_candidates(
    candidates: list[dict[str, object]],
    *,
    reviewed_at: str = "2026-11-08",
) -> list[dict[str, object]]:
    """Create deterministic include/hold/exclude decisions without inventing technical facts."""
    decisions: list[dict[str, object]] = []
    seen: set[str] = set()
    for candidate in candidates:
        _validate_candidate(candidate)
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        decision, rationale = _decide(candidate)
        decisions.append(
            {
                "decision_id": _decision_id(candidate_id, decision),
                "candidate_id": candidate_id,
                "candidate_type": candidate["candidate_type"],
                "pack_id": candidate["pack_id"],
                "decision": decision,
                "decision_rationale": rationale,
                "reviewed_at": reviewed_at,
                "reviewed_by": "structured_candidate_conservative_review",
                "source_id": candidate["source_id"],
                "source_file": candidate["source_file"],
                "source_sha256": candidate["source_sha256"],
                "page_number": candidate["page_number"],
                "evidence_locator": candidate["evidence_locator"],
            }
        )
    return decisions


def _decide(candidate: dict[str, object]) -> tuple[str, str]:
    evidence = str(candidate["evidence_text"])
    normalized = evidence.lower()
    if any(marker in normalized for marker in _NAVIGATION_MARKERS):
        return "exclude", "navigation-only or ordering evidence cannot support an operational candidate"
    marker = next((marker for marker in _OUT_OF_SCOPE_MARKERS if marker in normalized), None)
    if marker is None and re.search(r"\bnxds(?:6|10|15|20)i[cr]\b", normalized):
        marker = "nXDS C/R variant"
    if marker is not None:
        display_marker = marker.upper() if marker in {"smtc", "tsc", "umc-", "gm-", "dc-", "st-"} else marker
        return "not_retrievable", f"evidence contains out-of-scope marker: {display_marker}"
    if candidate["candidate_type"] in {"safety_rules", "maintenance_tasks"}:
        has_dangerous_action = any(action in normalized for action in _DANGEROUS_ACTIONS)
        has_prerequisite = any(prerequisite in normalized for prerequisite in _SAFETY_PREREQUISITES)
        if has_dangerous_action and not has_prerequisite:
            return "not_retrievable", "dangerous action lacks explicit isolation or depressurization prerequisite"
    return "include", "explicit candidate label with complete in-scope source evidence"


def _validate_candidate(candidate: dict[str, object]) -> None:
    missing = [field for field in _REQUIRED_FIELDS if not str(candidate.get(field, "")).strip()]
    if missing:
        raise ValueError(f"candidate is missing fields: {', '.join(missing)}")
    if candidate["candidate_status"] != "review_required":
        raise ValueError("candidate status must be review_required")
    if str(candidate["pack_id"]) not in _ALLOWED_PACKS:
        raise ValueError("candidate has unknown pack_id")


def _decision_id(candidate_id: str, decision: str) -> str:
    return hashlib.sha256(f"{candidate_id}|{decision}".encode("utf-8")).hexdigest()[:24]


def generate_review_ledger(input_path: Path, output_directory: Path) -> dict[str, object]:
    """Review a candidate JSONL file or category directory and write a traceable ledger."""
    input_files = [input_path] if input_path.is_file() else sorted(input_path.glob("*_candidates_v1.jsonl"))
    if not input_files:
        raise ValueError("no candidate JSONL files found")
    candidates: list[dict[str, object]] = []
    for path in input_files:
        with path.open(encoding="utf-8") as file:
            candidates.extend(json.loads(line) for line in file if line.strip())
    decisions = review_structured_candidates(candidates)
    included_candidates = project_included_candidates(candidates, decisions)
    output_directory.mkdir(parents=True, exist_ok=True)
    ledger_path = output_directory / "structured_candidate_decision_ledger_v1.jsonl"
    _write_jsonl(ledger_path, decisions)
    included_path = output_directory / "structured_candidates_auto_reviewed_v1.jsonl"
    _write_jsonl(included_path, included_candidates)
    decision_counts: dict[str, int] = {}
    for decision in decisions:
        value = str(decision["decision"])
        decision_counts[value] = decision_counts.get(value, 0) + 1
    manifest: dict[str, object] = {
        "review_version": "structured_candidate_review_v1",
        "input_sha256": _combined_sha256(input_files),
        "total_candidates": len(candidates),
        "auto_included_candidates": len(included_candidates),
        "decision_counts": decision_counts,
        "ledger_sha256": _sha256(ledger_path),
        "auto_included_sha256": _sha256(included_path),
    }
    manifest_path = output_directory / "structured_candidate_review_manifest_v1.json"
    temporary = manifest_path.with_name(f"{manifest_path.name}.partial")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(manifest_path)
    return manifest


def project_included_candidates(
    candidates: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Project only conservative-review inclusions; holds and exclusions remain outside the indexable set."""
    decision_by_candidate: dict[str, dict[str, object]] = {}
    for decision in decisions:
        candidate_id = str(decision.get("candidate_id", ""))
        if not candidate_id or candidate_id in decision_by_candidate:
            raise ValueError("decision ledger has missing or duplicate candidate_id")
        decision_by_candidate[candidate_id] = decision
    projected: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", ""))
        decision = decision_by_candidate.get(candidate_id)
        if decision is None:
            raise ValueError(f"candidate has no review decision: {candidate_id}")
        if decision["decision"] != "include":
            continue
        updated = dict(candidate)
        updated["candidate_status"] = "auto_reviewed_include"
        updated["review_decision_id"] = decision["decision_id"]
        updated["review_decision_rationale"] = decision["decision_rationale"]
        projected.append(updated)
    return projected


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    temporary = path.with_name(f"{path.name}.partial")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _combined_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(_sha256(path).encode("ascii"))
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a conservative structured-candidate decision ledger.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(generate_review_ledger(arguments.input, arguments.output_directory), ensure_ascii=False))


if __name__ == "__main__":
    main()
