from __future__ import annotations

from industrialops.phase0.bilingual_corpus import build_bilingual_records, split_text_for_translation


def test_build_bilingual_records_preserves_original_english_and_evidence() -> None:
    records = [
        {
            "unit_id": "en-1",
            "pack_id": "dry_vacuum_pump_pack_v1.0.0",
            "language": "en",
            "text": "Isolate electrical power before service.",
            "evidence_locator": "EDW-MANUAL:p.3",
        }
    ]

    result = build_bilingual_records(records, translate=lambda text: "维修前隔离电源。")

    assert result == [
        {
            "unit_id": "en-1",
            "pack_id": "dry_vacuum_pump_pack_v1.0.0",
            "language": "en",
            "text": "Isolate electrical power before service.",
            "evidence_locator": "EDW-MANUAL:p.3",
            "original_text": "Isolate electrical power before service.",
            "text_zh": "维修前隔离电源。",
            "translation_status": "machine_translated_project_zh",
        }
    ]


def test_build_bilingual_records_uses_source_chinese_without_translation() -> None:
    records = [
        {
            "unit_id": "zh-1",
            "pack_id": "cnc_pack_v1.0.0",
            "language": "zh-CN",
            "text": "维修前断开电源。",
        }
    ]

    result = build_bilingual_records(records, translate=lambda _: (_ for _ in ()).throw(AssertionError()))

    assert result[0]["original_text"] == "维修前断开电源。"
    assert result[0]["text_zh"] == "维修前断开电源。"
    assert result[0]["translation_status"] == "source_zh"


def test_split_text_for_translation_preserves_all_source_characters() -> None:
    text = "First sentence.\nSecond sentence with a longer technical phrase.\nThird."

    pieces = split_text_for_translation(text, max_characters=25)

    assert "".join(pieces) == text
    assert all(len(piece) <= 25 for piece in pieces)


def test_build_bilingual_records_rejects_empty_english_translation() -> None:
    records = [{"unit_id": "en-2", "language": "en", "text": "Lock out power."}]

    try:
        build_bilingual_records(records, translate=lambda _: "   ")
    except ValueError as error:
        assert "empty Chinese translation" in str(error)
    else:
        raise AssertionError("An empty translated record must not enter the corpus")


def test_validate_bilingual_records_checks_original_and_evidence() -> None:
    from industrialops.phase0.bilingual_corpus import validate_bilingual_records

    records = [
        {
            "unit_id": "en-3",
            "language": "en",
            "text": "Disconnect power.",
            "original_text": "Disconnect power.",
            "text_zh": "断开电源。",
            "translation_status": "machine_translated_project_zh",
            "source_id": "EDW-NXDS-MANUAL-EN-L",
            "source_file": "manual.pdf",
            "source_sha256": "abc",
            "page_number": 3,
            "evidence_locator": "manual:p.3",
        }
    ]

    assert validate_bilingual_records(records) == {"total": 1, "source_zh": 0, "machine_translated": 1}
