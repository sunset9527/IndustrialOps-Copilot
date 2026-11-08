"""Immutable-style ledger records for page-level scope decisions."""

from __future__ import annotations


def _scope_record_id(record: dict[str, object]) -> str:
    """Return the page identity or the more precise chunk identity."""
    identifier = record.get("unit_id") or record.get("candidate_id")
    if identifier is None:
        raise ValueError("scope decision record requires unit_id or candidate_id")
    return str(identifier)


def build_pending_scope_decision_ledger(
    queue: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Create one pending decision record for every unresolved review task."""
    ledger: list[dict[str, object]] = []
    for item in queue:
        candidate_id = str(item.get("parent_candidate_id") or item["candidate_id"])
        unit_id = str(item.get("unit_id") or candidate_id)
        text_preview = str(item.get("text_preview", " ".join(str(item.get("text", "")).split())[:500]))
        ledger.append(
            {
                "decision_id": f"scope-decision:{unit_id}",
                "unit_id": unit_id,
                "parent_candidate_id": candidate_id,
                "candidate_id": candidate_id,
                "source_id": item["source_id"],
                "page_number": item["page_number"],
                "priority": item.get("priority", "normal"),
                "source_file": item["source_file"],
                "evidence_locator": item["evidence_locator"],
                "text_preview": text_preview,
                "decision": "pending",
                "decision_rationale": None,
                "reviewed_by": None,
            }
        )
    return ledger


def apply_scope_decisions(
    records: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Apply explicit include/exclude decisions without changing pending records."""
    decision_by_record = {
        _scope_record_id(decision): decision
        for decision in decisions
        if decision.get("decision") in {"include", "exclude"}
    }
    applied: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        decision = decision_by_record.get(_scope_record_id(record))
        if decision is not None:
            rationale = str(decision["decision_rationale"])
            updated["applicability"] = (
                "approved_in_scope" if decision["decision"] == "include" else "excluded"
            )
            updated["applicability_reasons"] = [f"scope_decision:{rationale}"]
        applied.append(updated)
    return applied


def merge_scope_decisions_into_ledger(
    ledger: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Record reviewed include/exclude decisions while retaining pending ledger rows."""
    decision_by_record = {
        _scope_record_id(decision): decision
        for decision in decisions
        if decision.get("decision") in {"include", "exclude"}
    }
    merged: list[dict[str, object]] = []
    for entry in ledger:
        updated = dict(entry)
        decision = decision_by_record.get(_scope_record_id(entry))
        if decision is not None:
            updated["decision"] = decision["decision"]
            updated["decision_rationale"] = decision["decision_rationale"]
            updated["reviewed_by"] = decision["reviewed_by"]
            updated["reviewed_at"] = decision["reviewed_at"]
        merged.append(updated)
    return merged
