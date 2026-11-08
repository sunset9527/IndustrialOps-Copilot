"""Compatibility policy for generic multi-model Haas mill manuals."""

from __future__ import annotations


def apply_broad_manual_scope_policy(
    records: list[dict[str, object]],
    markers_by_source: dict[str, list[str]],
) -> list[dict[str, object]]:
    """Approve generic content while escalating explicit out-of-scope model mentions."""
    result: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        if record["applicability"] != "review_required":
            result.append(updated)
            continue
        markers = markers_by_source.get(str(record["source_id"]), [])
        matches = [marker for marker in markers if marker.casefold() in str(record["text"]).casefold()]
        if matches:
            updated["applicability"] = "mixed_scope_review"
            updated["applicability_reasons"] = [
                f"broad_manual_out_of_scope_model:{marker}" for marker in matches
            ]
        else:
            updated["applicability"] = "approved_in_scope"
            updated["applicability_reasons"] = ["broad_manual_generic_mill_content"]
        result.append(updated)
    return result
