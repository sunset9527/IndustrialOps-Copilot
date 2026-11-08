from __future__ import annotations

from industrialops.phase0.segment_scope_classifier import classify_segment_scope


def test_classify_segment_scope_rechecks_terms_at_chunk_granularity() -> None:
    segments = [
        {"chunk_id": "a:01", "source_id": "HAAS-AXIS-MOTION-ZH", "text": "检查标准伺服轴。"},
        {"chunk_id": "a:02", "source_id": "HAAS-AXIS-MOTION-ZH", "text": "SMTC 选件说明。"},
        {"chunk_id": "b:01", "source_id": "HAAS-OP-EN-2025", "text": "General mill operation."},
        {"chunk_id": "c:01", "source_id": "EDW-NXDS-DOCUMENTS", "text": "SMTC catalog entry."},
    ]

    result = classify_segment_scope(
        segments,
        exclusion_terms=["SMTC"],
        broad_review_sources={"HAAS-OP-EN-2025"},
        catalog_sources={"EDW-NXDS-DOCUMENTS"},
    )

    assert result == [
        {
            "chunk_id": "a:01",
            "source_id": "HAAS-AXIS-MOTION-ZH",
            "text": "检查标准伺服轴。",
            "applicability": "provisionally_in_scope",
            "applicability_reasons": [],
        },
        {
            "chunk_id": "a:02",
            "source_id": "HAAS-AXIS-MOTION-ZH",
            "text": "SMTC 选件说明。",
            "applicability": "mixed_scope_review",
            "applicability_reasons": ["explicit_out_of_scope_term:SMTC"],
        },
        {
            "chunk_id": "b:01",
            "source_id": "HAAS-OP-EN-2025",
            "text": "General mill operation.",
            "applicability": "review_required",
            "applicability_reasons": [],
        },
        {
            "chunk_id": "c:01",
            "source_id": "EDW-NXDS-DOCUMENTS",
            "text": "SMTC catalog entry.",
            "applicability": "excluded",
            "applicability_reasons": ["explicit_out_of_scope_term:SMTC"],
        },
    ]
