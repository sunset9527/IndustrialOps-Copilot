"""Create review-required structured candidates from traceable bilingual corpus records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


_ALLOWED_PACKS = {"cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"}
_EVIDENCE_FIELDS = ("source_id", "source_file", "source_sha256", "page_number", "evidence_locator")
_CANDIDATE_TYPES = ("alarms", "components", "symptoms", "failure_modes", "maintenance_tasks", "safety_rules")
_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("safety_rules", "lockout_tagout", ("lock out", "lockout", "lock-out", "锁定", "挂牌")),
    ("safety_rules", "depressurization", ("depressur", "vent pressure", "泄压", "排空压力")),
    ("safety_rules", "lifting", ("lifting", "lift the", "起吊", "吊装")),
    ("safety_rules", "guarding", ("guard", "interlock", "防护", "联锁")),
    ("safety_rules", "warning", ("warning", "danger", "caution", "警告", "危险", "注意")),
    ("maintenance_tasks", "inspection", ("inspect", "inspection", "检查", "检验")),
    ("maintenance_tasks", "cleaning", ("clean", "cleaning", "清洁", "清理")),
    ("maintenance_tasks", "replacement", ("replace", "replacement", "更换", "替换")),
    ("maintenance_tasks", "lubrication", ("lubricat", "润滑")),
    ("components", "spindle", ("spindle", "主轴")),
    ("components", "tool_changer", ("tool changer", "刀库", "换刀器")),
    ("components", "vacuum_pump", ("vacuum pump", "dry pump", "真空泵", "干泵")),
    ("components", "shaft_seal", ("shaft seal", "轴封")),
    ("symptoms", "leak", ("leak", "leakage", "泄漏")),
    ("symptoms", "overheating", ("overheat", "over-temperature", "过热", "超温")),
    ("failure_modes", "explicit_failure", ("failure", "failed", "fault", "故障", "失效")),
)


def extract_structured_candidates(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return deterministic, evidence-preserving candidates that always need review."""
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        _validate_source_record(record)
        evidence_text = str(record["original_text"])
        searchable = f"{evidence_text}\n{record['text_zh']}".lower()
        source_record_id = _source_record_id(record)
        for alarm_code in _alarm_codes(searchable):
            candidate_id = _candidate_id("alarms", alarm_code, str(record["pack_id"]), source_record_id)
            if candidate_id not in seen:
                seen.add(candidate_id)
                candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "candidate_type": "alarms",
                        "candidate_status": "review_required",
                        "pack_id": record["pack_id"],
                        "label": alarm_code,
                        "source_record_id": source_record_id,
                        "source_id": record["source_id"],
                        "source_file": record["source_file"],
                        "source_sha256": record["source_sha256"],
                        "page_number": record["page_number"],
                        "evidence_locator": record["evidence_locator"],
                        "evidence_text": evidence_text,
                        "text_zh": record["text_zh"],
                        "extraction_reason": f"matched explicit alarm code: {alarm_code}",
                    }
                )
        specific_safety_found = False
        for candidate_type, label, patterns in _RULES:
            matched_pattern = next((pattern for pattern in patterns if pattern.lower() in searchable), None)
            if matched_pattern is None:
                continue
            if candidate_type == "safety_rules" and label == "warning" and specific_safety_found:
                continue
            candidate_id = _candidate_id(candidate_type, label, str(record["pack_id"]), source_record_id)
            if candidate_id in seen:
                continue
            seen.add(candidate_id)
            if candidate_type == "safety_rules" and label != "warning":
                specific_safety_found = True
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_type": candidate_type,
                    "candidate_status": "review_required",
                    "pack_id": record["pack_id"],
                    "label": label,
                    "source_record_id": source_record_id,
                    "source_id": record["source_id"],
                    "source_file": record["source_file"],
                    "source_sha256": record["source_sha256"],
                    "page_number": record["page_number"],
                    "evidence_locator": record["evidence_locator"],
                    "evidence_text": evidence_text,
                    "text_zh": record["text_zh"],
                    "extraction_reason": f"matched explicit {candidate_type} pattern: {matched_pattern}",
                }
            )
    return candidates


def _validate_source_record(record: dict[str, object]) -> None:
    missing = [field for field in _EVIDENCE_FIELDS if not str(record.get(field, "")).strip()]
    if missing:
        raise ValueError(f"missing evidence fields: {', '.join(missing)}")
    if str(record.get("pack_id", "")) not in _ALLOWED_PACKS:
        raise ValueError("record has an unknown pack_id")
    if not str(record.get("text", "")).strip() or not str(record.get("original_text", "")).strip():
        raise ValueError("record has no original source text")
    if str(record.get("text")) != str(record.get("original_text")):
        raise ValueError("record original text differs from source text")
    if not str(record.get("text_zh", "")).strip():
        raise ValueError("record has no Chinese text")
    if str(record.get("translation_status", "")) not in {"source_zh", "machine_translated_project_zh"}:
        raise ValueError("record has an unsupported translation status")
    _source_record_id(record)


def _source_record_id(record: dict[str, object]) -> str:
    identifier = record.get("candidate_id", record.get("unit_id", ""))
    if not str(identifier).strip():
        raise ValueError("record has no stable source identifier")
    return str(identifier)


def _candidate_id(candidate_type: str, label: str, pack_id: str, source_record_id: str) -> str:
    value = "|".join((candidate_type, label, pack_id, source_record_id))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _alarm_codes(text: str) -> list[str]:
    """Find codes only where an explicit English or Chinese alarm marker precedes them."""
    return list(dict.fromkeys(re.findall(r"(?:alarm|报警)\s*#?\s*(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)))


def write_candidate_outputs(
    output_directory: Path,
    candidates: list[dict[str, object]],
    *,
    input_sha256: str,
) -> dict[str, object]:
    """Write all candidate categories atomically and return their traceability manifest."""
    output_directory.mkdir(parents=True, exist_ok=True)
    candidate_counts: dict[str, int] = {}
    output_hashes: dict[str, str] = {}
    for candidate_type in _CANDIDATE_TYPES:
        records = [record for record in candidates if record["candidate_type"] == candidate_type]
        filename = f"{candidate_type}_candidates_v1.jsonl"
        path = output_directory / filename
        _write_jsonl(path, records)
        output_hashes[filename] = _sha256(path)
        if records:
            candidate_counts[candidate_type] = len(records)
    manifest: dict[str, object] = {
        "candidate_corpus_version": "structured_candidates_v1",
        "input_sha256": input_sha256,
        "total_candidates": len(candidates),
        "candidate_counts": candidate_counts,
        "output_sha256": output_hashes,
    }
    manifest_path = output_directory / "structured_candidate_manifest_v1.json"
    temporary = manifest_path.with_name(f"{manifest_path.name}.partial")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(manifest_path)
    return manifest


def validate_structured_candidates(candidates: list[dict[str, object]]) -> dict[str, int]:
    """Reject any candidate that cannot be audited as a review-only source derivative."""
    required = (
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
    candidate_ids: set[str] = set()
    counts: dict[str, int] = {}
    for candidate in candidates:
        missing = [field for field in required if not str(candidate.get(field, "")).strip()]
        if missing:
            raise ValueError(f"candidate is missing fields: {', '.join(missing)}")
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in candidate_ids:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        candidate_type = str(candidate["candidate_type"])
        if candidate_type not in _CANDIDATE_TYPES:
            raise ValueError(f"unknown candidate_type: {candidate_type}")
        if candidate["candidate_status"] != "review_required":
            raise ValueError("candidate is not review_required")
        if str(candidate["pack_id"]) not in _ALLOWED_PACKS:
            raise ValueError("candidate has an unknown pack_id")
        counts[candidate_type] = counts.get(candidate_type, 0) + 1
    return {"total_candidates": len(candidates), **counts}


def generate_candidate_corpus(input_path: Path, output_directory: Path) -> dict[str, object]:
    """Read a bilingual corpus, extract review candidates, and write its manifest."""
    with input_path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]
    candidates = extract_structured_candidates(records)
    validate_structured_candidates(candidates)
    return write_candidate_outputs(
        output_directory,
        candidates,
        input_sha256=_sha256(input_path),
    )


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate review-required structured IndustrialOps candidates.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(generate_candidate_corpus(arguments.input, arguments.output_directory), ensure_ascii=False))


if __name__ == "__main__":
    main()
