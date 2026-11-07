"""Immutable-style ledger records for page-level scope decisions."""

from __future__ import annotations


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
    decision_by_candidate = {
        str(decision["candidate_id"]): decision
        for decision in decisions
        if decision.get("decision") in {"include", "exclude"}
    }
    applied: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        decision = decision_by_candidate.get(str(record["candidate_id"]))
        if decision is not None:
            rationale = str(decision["decision_rationale"])
            updated["applicability"] = (
                "approved_in_scope" if decision["decision"] == "include" else "excluded"
            )
            updated["applicability_reasons"] = [f"scope_decision:{rationale}"]
        applied.append(updated)
    return applied
