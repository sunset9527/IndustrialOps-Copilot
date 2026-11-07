from __future__ import annotations

from industrialops.phase0.scope_review_queue import build_scope_review_queue


def test_build_scope_review_queue_prioritizes_mixed_scope_records() -> None:
    records = [
        {
            "candidate_id": "broad",
            "source_id": "HAAS-OP-EN-2025",
            "page_number": 6,
            "applicability": "review_required",
            "source_file": "haas/manual.pdf",
            "evidence_locator": "HAAS-OP-EN-2025:p.6",
            "text": "General operation instructions.",
        },
        {
            "candidate_id": "mixed",
            "source_id": "HAAS-VFVM-SPECS-ZH",
            "page_number": 3,
            "applicability": "mixed_scope_review",
            "source_file": "haas/specification.pdf",
            "evidence_locator": "HAAS-VFVM-SPECS-ZH:p.3",
            "text": "SMTC option details.",
        },
        {"candidate_id": "ready", "source_id": "HAAS-AXIS-MOTION-ZH", "page_number": 2, "applicability": "provisionally_in_scope"},
    ]

    queue = build_scope_review_queue(records)

    assert queue == [
        {
            "review_id": "scope:mixed",
            "candidate_id": "mixed",
            "source_id": "HAAS-VFVM-SPECS-ZH",
            "page_number": 3,
            "priority": "high",
            "reason": "contains_explicit_out_of_scope_term",
            "source_file": "haas/specification.pdf",
            "evidence_locator": "HAAS-VFVM-SPECS-ZH:p.3",
            "text_preview": "SMTC option details.",
            "review_status": "pending",
        },
        {
            "review_id": "scope:broad",
            "candidate_id": "broad",
            "source_id": "HAAS-OP-EN-2025",
            "page_number": 6,
            "priority": "normal",
            "reason": "broad_manual_requires_model_applicability_review",
            "source_file": "haas/manual.pdf",
            "evidence_locator": "HAAS-OP-EN-2025:p.6",
            "text_preview": "General operation instructions.",
            "review_status": "pending",
        },
    ]
