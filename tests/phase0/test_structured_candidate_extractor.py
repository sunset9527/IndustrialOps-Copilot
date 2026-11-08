from __future__ import annotations

import pytest

from industrialops.phase0.structured_candidate_extractor import (
    extract_structured_candidates,
    generate_candidate_corpus,
    validate_structured_candidates,
    write_candidate_outputs,
)


def _record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "candidate_id": "source-001",
        "pack_id": "dry_vacuum_pump_pack_v1.0.0",
        "source_id": "EDW-NXDS-MANUAL-EN-L",
        "source_file": "manual.pdf",
        "source_sha256": "a" * 64,
        "page_number": 12,
        "evidence_locator": "EDW-NXDS-MANUAL-EN-L:p.12",
        "language": "en",
        "text": "WARNING: Lock out electrical power before inspecting the pump.",
        "original_text": "WARNING: Lock out electrical power before inspecting the pump.",
        "text_zh": "警告：检查泵之前，请锁定电源。",
        "translation_status": "machine_translated_project_zh",
    }
    record.update(overrides)
    return record


def test_extracts_traceable_safety_candidate_as_review_required() -> None:
    candidates = extract_structured_candidates([_record()])

    safety = next(candidate for candidate in candidates if candidate["candidate_type"] == "safety_rules")
    assert safety["label"] == "lockout_tagout"
    assert safety["candidate_status"] == "review_required"
    assert safety["source_record_id"] == "source-001"
    assert safety["pack_id"] == "dry_vacuum_pump_pack_v1.0.0"
    assert safety["evidence_locator"] == "EDW-NXDS-MANUAL-EN-L:p.12"
    assert safety["evidence_text"] == _record()["original_text"]
    assert safety["text_zh"] == _record()["text_zh"]


def test_extraction_is_deterministic_and_can_emit_multiple_candidate_types() -> None:
    first = extract_structured_candidates([_record()])
    second = extract_structured_candidates([_record()])

    assert first == second
    assert {candidate["candidate_type"] for candidate in first} == {"safety_rules", "maintenance_tasks"}
    assert len({candidate["candidate_id"] for candidate in first}) == len(first)


def test_extracts_explicit_chinese_alarm_code_with_traceable_evidence() -> None:
    text = "报警 552 断路器跳闸。"
    candidates = extract_structured_candidates(
        [_record(language="zh-CN", text=text, original_text=text, text_zh=text, translation_status="source_zh")]
    )

    alarm = next(candidate for candidate in candidates if candidate["candidate_type"] == "alarms")
    assert alarm["label"] == "552"
    assert alarm["candidate_status"] == "review_required"
    assert alarm["evidence_text"] == text


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("evidence_locator", ""),
        ("source_sha256", ""),
        ("pack_id", "unknown_pack"),
        ("text_zh", ""),
    ],
)
def test_rejects_records_without_complete_traceable_bilingual_evidence(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        extract_structured_candidates([_record(**{field: value})])


def test_write_candidate_outputs_creates_category_files_and_a_count_manifest(tmp_path) -> None:
    candidates = extract_structured_candidates([_record()])

    manifest = write_candidate_outputs(tmp_path, candidates, input_sha256="input-hash")

    assert manifest["input_sha256"] == "input-hash"
    assert manifest["candidate_counts"] == {"maintenance_tasks": 1, "safety_rules": 1}
    assert (tmp_path / "safety_rules_candidates_v1.jsonl").is_file()
    assert (tmp_path / "alarms_candidates_v1.jsonl").read_text(encoding="utf-8") == ""
    assert '"candidate_type": "safety_rules"' in (tmp_path / "safety_rules_candidates_v1.jsonl").read_text(encoding="utf-8")
    assert (tmp_path / "structured_candidate_manifest_v1.json").is_file()


def test_generate_candidate_corpus_reads_bilingual_jsonl_and_writes_a_manifest(tmp_path) -> None:
    import json

    input_path = tmp_path / "bilingual.jsonl"
    input_path.write_text(json.dumps(_record(), ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = generate_candidate_corpus(input_path, tmp_path / "candidates")

    assert manifest["total_candidates"] == 2
    assert manifest["input_sha256"]
    assert (tmp_path / "candidates" / "structured_candidate_manifest_v1.json").is_file()


def test_validate_structured_candidates_rejects_missing_evidence() -> None:
    candidates = extract_structured_candidates([_record()])
    assert validate_structured_candidates(candidates)["total_candidates"] == 2

    candidates[0]["evidence_locator"] = ""
    with pytest.raises(ValueError):
        validate_structured_candidates(candidates)
