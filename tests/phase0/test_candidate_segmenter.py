from __future__ import annotations

from industrialops.phase0.candidate_segmenter import segment_candidate


def test_segment_candidate_groups_paragraphs_without_losing_evidence() -> None:
    candidate = {
        "candidate_id": "c1",
        "source_id": "HAAS-TEST",
        "source_sha256": "a" * 64,
        "page_number": 7,
        "evidence_locator": "HAAS-TEST:p.7",
        "text": "标准冷却液检查。\n\n断开主电源后检查泵。\n\n记录结果。",
        "applicability": "mixed_scope_review",
    }

    segments = segment_candidate(candidate, max_characters=18)

    assert segments == [
        {
            "chunk_id": "c1:01",
            "parent_candidate_id": "c1",
            "chunk_index": 1,
            "source_id": "HAAS-TEST",
            "source_sha256": "a" * 64,
            "page_number": 7,
            "evidence_locator": "HAAS-TEST:p.7",
            "text": "标准冷却液检查。",
            "applicability": "mixed_scope_review",
        },
        {
            "chunk_id": "c1:02",
            "parent_candidate_id": "c1",
            "chunk_index": 2,
            "source_id": "HAAS-TEST",
            "source_sha256": "a" * 64,
            "page_number": 7,
            "evidence_locator": "HAAS-TEST:p.7",
            "text": "断开主电源后检查泵。\n\n记录结果。",
            "applicability": "mixed_scope_review",
        },
    ]


def test_segment_candidate_uses_single_line_boundaries_when_pdf_has_no_blank_paragraphs() -> None:
    candidate = {
        "candidate_id": "c2",
        "source_id": "HAAS-TEST",
        "source_sha256": "b" * 64,
        "page_number": 8,
        "evidence_locator": "HAAS-TEST:p.8",
        "text": "one\ntwo\nthree",
        "applicability": "mixed_scope_review",
    }

    segments = segment_candidate(candidate, max_characters=7)

    assert [segment["text"] for segment in segments] == ["one\ntwo", "three"]


def test_segment_candidate_starts_a_new_group_at_numbered_manual_section() -> None:
    candidate = {
        "candidate_id": "c3",
        "source_id": "EDW-TEST",
        "source_sha256": "c" * 64,
        "page_number": 56,
        "evidence_locator": "EDW-TEST:p.56",
        "text": "9.4.6 Bearing kit\nStandard pump procedure.\n9.4.7 Valve kit\nC version procedure.",
        "applicability": "mixed_scope_review",
    }

    segments = segment_candidate(candidate, max_characters=500)

    assert [segment["text"] for segment in segments] == [
        "9.4.6 Bearing kit\nStandard pump procedure.",
        "9.4.7 Valve kit\nC version procedure.",
    ]
