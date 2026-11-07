from __future__ import annotations

from industrialops.phase0.non_operational_filter import exclude_non_operational_records


def test_exclude_non_operational_records_excludes_conformity_declaration() -> None:
    records = [{"candidate_id": "c1", "text": "EU Declaration of Conformity", "applicability": "mixed_scope_review"}]

    result = exclude_non_operational_records(records)

    assert result == [
        {
            "candidate_id": "c1",
            "text": "EU Declaration of Conformity",
            "applicability": "excluded",
            "applicability_reasons": ["non_operational_document_type:conformity_declaration"],
        }
    ]


def test_exclude_non_operational_records_keeps_maintenance_instruction() -> None:
    records = [{"candidate_id": "c2", "text": "Replace the tip seal after isolating power.", "applicability": "mixed_scope_review"}]

    result = exclude_non_operational_records(records)

    assert result == [
        {
            "candidate_id": "c2",
            "text": "Replace the tip seal after isolating power.",
            "applicability": "mixed_scope_review",
        }
    ]
