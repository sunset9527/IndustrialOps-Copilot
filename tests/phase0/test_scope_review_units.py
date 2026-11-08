from __future__ import annotations

from industrialops.phase0.scope_review_units import (
    build_scope_review_units,
    build_scope_review_units_from_segments,
)


def test_build_scope_review_units_uses_same_page_chunks_for_mixed_scope_content() -> None:
    records = [
        {
            "candidate_id": "mixed-page",
            "source_id": "EDW-NXDS-MANUAL-EN-L",
            "source_sha256": "a" * 64,
            "source_file": "edwards/manual.pdf",
            "page_number": 56,
            "evidence_locator": "EDW-NXDS-MANUAL-EN-L:p.56",
            "text": "Standard bearing kit.\n\nC version valve kit.",
            "applicability": "mixed_scope_review",
        },
        {
            "candidate_id": "broad-page",
            "source_id": "HAAS-OP-EN-2025",
            "source_sha256": "b" * 64,
            "source_file": "haas/manual.pdf",
            "page_number": 8,
            "evidence_locator": "HAAS-OP-EN-2025:p.8",
            "text": "General operation instructions.",
            "applicability": "review_required",
        },
    ]

    units = build_scope_review_units(records, max_characters=24)

    assert units == [
        {
            "unit_id": "mixed-page:01",
            "parent_candidate_id": "mixed-page",
            "source_id": "EDW-NXDS-MANUAL-EN-L",
            "source_sha256": "a" * 64,
            "source_file": "edwards/manual.pdf",
            "page_number": 56,
            "evidence_locator": "EDW-NXDS-MANUAL-EN-L:p.56",
            "text": "Standard bearing kit.",
            "review_reason": "mixed_scope_requires_chunk_decision",
            "priority": "high",
        },
        {
            "unit_id": "mixed-page:02",
            "parent_candidate_id": "mixed-page",
            "source_id": "EDW-NXDS-MANUAL-EN-L",
            "source_sha256": "a" * 64,
            "source_file": "edwards/manual.pdf",
            "page_number": 56,
            "evidence_locator": "EDW-NXDS-MANUAL-EN-L:p.56",
            "text": "C version valve kit.",
            "review_reason": "mixed_scope_requires_chunk_decision",
            "priority": "high",
        },
        {
            "unit_id": "broad-page",
            "parent_candidate_id": "broad-page",
            "source_id": "HAAS-OP-EN-2025",
            "source_sha256": "b" * 64,
            "source_file": "haas/manual.pdf",
            "page_number": 8,
            "evidence_locator": "HAAS-OP-EN-2025:p.8",
            "text": "General operation instructions.",
            "review_reason": "broad_manual_requires_page_decision",
            "priority": "normal",
        },
    ]


def test_build_scope_review_units_from_segments_keeps_only_unresolved_chunks() -> None:
    segments = [
        {
            "chunk_id": "mixed:01",
            "parent_candidate_id": "mixed",
            "source_id": "EDW-TEST",
            "source_sha256": "a" * 64,
            "source_file": "edwards/manual.pdf",
            "page_number": 10,
            "evidence_locator": "EDW-TEST:p.10",
            "text": "C variant kit.",
            "applicability": "mixed_scope_review",
        },
        {
            "chunk_id": "mixed:02",
            "parent_candidate_id": "mixed",
            "source_id": "EDW-TEST",
            "source_sha256": "a" * 64,
            "source_file": "edwards/manual.pdf",
            "page_number": 10,
            "evidence_locator": "EDW-TEST:p.10",
            "text": "Standard kit.",
            "applicability": "provisionally_in_scope",
        },
    ]

    units = build_scope_review_units_from_segments(segments)

    assert units == [
        {
            "unit_id": "mixed:01",
            "parent_candidate_id": "mixed",
            "source_id": "EDW-TEST",
            "source_sha256": "a" * 64,
            "source_file": "edwards/manual.pdf",
            "page_number": 10,
            "evidence_locator": "EDW-TEST:p.10",
            "text": "C variant kit.",
            "review_reason": "mixed_scope_requires_chunk_decision",
            "priority": "high",
        }
    ]
