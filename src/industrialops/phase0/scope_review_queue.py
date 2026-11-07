"""Build a deterministic, auditable queue for unresolved scope decisions."""

from __future__ import annotations


def build_scope_review_queue(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return unresolved candidates ordered by scope-review risk."""
    queue: list[dict[str, object]] = []
    for record in records:
        applicability = record["applicability"]
        if applicability == "mixed_scope_review":
            priority = "high"
            reason = "contains_explicit_out_of_scope_term"
        elif applicability == "review_required":
            priority = "normal"
            reason = "broad_manual_requires_model_applicability_review"
        else:
            continue
        candidate_id = str(record["candidate_id"])
        queue.append(
            {
                "review_id": f"scope:{candidate_id}",
                "candidate_id": candidate_id,
                "source_id": record["source_id"],
                "page_number": record["page_number"],
                "priority": priority,
                "reason": reason,
            }
        )
    return sorted(queue, key=lambda item: (item["priority"] != "high", item["source_id"], item["page_number"]))
