from __future__ import annotations

from industrialops.phase0.source_scope_policy import apply_source_scope_policy


def test_source_scope_policy_marks_curated_service_source_as_provisionally_in_scope() -> None:
    records = [{"source_id": "HAAS-AXIS-MOTION-ZH", "applicability": "review_required"}]

    result = apply_source_scope_policy(records, {"HAAS-OP-EN-2025"}, {"EDW-NXDS-DOCUMENTS"})

    assert result == [{"source_id": "HAAS-AXIS-MOTION-ZH", "applicability": "provisionally_in_scope"}]


def test_source_scope_policy_keeps_broad_manual_and_excludes_catalog() -> None:
    records = [
        {"source_id": "HAAS-OP-EN-2025", "applicability": "review_required"},
        {"source_id": "EDW-NXDS-DOCUMENTS", "applicability": "mixed_scope_review"},
    ]

    result = apply_source_scope_policy(records, {"HAAS-OP-EN-2025"}, {"EDW-NXDS-DOCUMENTS"})

    assert result == [
        {"source_id": "HAAS-OP-EN-2025", "applicability": "review_required"},
        {"source_id": "EDW-NXDS-DOCUMENTS", "applicability": "excluded"},
    ]
