from __future__ import annotations

from industrialops.phase0.scope_decision_ledger import (
    apply_scope_decisions,
    build_pending_scope_decision_ledger,
    merge_scope_decisions_into_ledger,
)


def test_build_pending_scope_decision_ledger_preserves_review_evidence() -> None:
    queue = [
        {
            "review_id": "scope:candidate-1",
            "candidate_id": "candidate-1",
            "source_id": "HAAS-OP-EN-2025",
            "page_number": 8,
            "priority": "high",
            "reason": "contains_explicit_out_of_scope_term",
            "source_file": "haas/manual.pdf",
            "evidence_locator": "HAAS-OP-EN-2025:p.8",
            "text_preview": "TSC option details.",
            "review_status": "pending",
        }
    ]

    ledger = build_pending_scope_decision_ledger(queue)

    assert ledger == [
        {
            "decision_id": "scope-decision:candidate-1",
            "unit_id": "candidate-1",
            "parent_candidate_id": "candidate-1",
            "candidate_id": "candidate-1",
            "source_id": "HAAS-OP-EN-2025",
            "page_number": 8,
            "priority": "high",
            "source_file": "haas/manual.pdf",
            "evidence_locator": "HAAS-OP-EN-2025:p.8",
            "text_preview": "TSC option details.",
            "decision": "pending",
            "decision_rationale": None,
            "reviewed_by": None,
        }
    ]


def test_apply_scope_decisions_changes_only_reviewed_candidates() -> None:
    records = [
        {"candidate_id": "include-me", "applicability": "mixed_scope_review"},
        {"candidate_id": "exclude-me", "applicability": "review_required"},
        {"candidate_id": "pending", "applicability": "review_required"},
    ]
    decisions = [
        {
            "candidate_id": "include-me",
            "decision": "include",
            "decision_rationale": "applies to the standard configuration",
        },
        {
            "candidate_id": "exclude-me",
            "decision": "exclude",
            "decision_rationale": "only describes an excluded option",
        },
    ]

    result = apply_scope_decisions(records, decisions)

    assert result == [
        {
            "candidate_id": "include-me",
            "applicability": "approved_in_scope",
            "applicability_reasons": ["scope_decision:applies to the standard configuration"],
        },
        {
            "candidate_id": "exclude-me",
            "applicability": "excluded",
            "applicability_reasons": ["scope_decision:only describes an excluded option"],
        },
        {"candidate_id": "pending", "applicability": "review_required"},
    ]


def test_build_pending_scope_decision_ledger_uses_chunk_unit_identity() -> None:
    units = [
        {
            "unit_id": "mixed-page:02",
            "parent_candidate_id": "mixed-page",
            "source_id": "EDW-NXDS-MANUAL-EN-L",
            "page_number": 56,
            "source_file": "edwards/manual.pdf",
            "evidence_locator": "EDW-NXDS-MANUAL-EN-L:p.56",
            "text": "C version valve kit.",
        }
    ]

    ledger = build_pending_scope_decision_ledger(units)

    assert ledger[0]["decision_id"] == "scope-decision:mixed-page:02"
    assert ledger[0]["unit_id"] == "mixed-page:02"
    assert ledger[0]["parent_candidate_id"] == "mixed-page"
    assert ledger[0]["candidate_id"] == "mixed-page"
    assert ledger[0]["text_preview"] == "C version valve kit."


def test_apply_scope_decisions_uses_chunk_unit_identity() -> None:
    units = [
        {
            "unit_id": "mixed-page:01",
            "parent_candidate_id": "mixed-page",
            "text": "Standard bearing kit.",
        },
        {
            "unit_id": "mixed-page:02",
            "parent_candidate_id": "mixed-page",
            "text": "C version valve kit.",
        },
    ]
    decisions = [
        {
            "unit_id": "mixed-page:01",
            "decision": "include",
            "decision_rationale": "explicitly applies to standard nXDS pumps",
        }
    ]

    result = apply_scope_decisions(units, decisions)

    assert result == [
        {
            "unit_id": "mixed-page:01",
            "parent_candidate_id": "mixed-page",
            "text": "Standard bearing kit.",
            "applicability": "approved_in_scope",
            "applicability_reasons": [
                "scope_decision:explicitly applies to standard nXDS pumps"
            ],
        },
        {
            "unit_id": "mixed-page:02",
            "parent_candidate_id": "mixed-page",
            "text": "C version valve kit.",
        },
    ]


def test_merge_scope_decisions_into_ledger_records_a_reviewed_decision() -> None:
    ledger = [
        {
            "decision_id": "scope-decision:mixed-page:01",
            "unit_id": "mixed-page:01",
            "decision": "pending",
            "decision_rationale": None,
            "reviewed_by": None,
        }
    ]
    decisions = [
        {
            "unit_id": "mixed-page:01",
            "decision": "include",
            "decision_rationale": "applies to the standard configuration",
            "reviewed_by": "phase0_scope_review",
            "reviewed_at": "2026-11-08",
        }
    ]

    result = merge_scope_decisions_into_ledger(ledger, decisions)

    assert result == [
        {
            "decision_id": "scope-decision:mixed-page:01",
            "unit_id": "mixed-page:01",
            "decision": "include",
            "decision_rationale": "applies to the standard configuration",
            "reviewed_by": "phase0_scope_review",
            "reviewed_at": "2026-11-08",
        }
    ]
