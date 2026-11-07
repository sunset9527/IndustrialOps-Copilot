"""Source-level scope decisions for the curated phase-0 archive."""

from __future__ import annotations


def apply_source_scope_policy(
    records: list[dict[str, object]],
    broad_review_sources: set[str],
    catalog_sources: set[str],
) -> list[dict[str, object]]:
    """Apply only explicit source-level decisions to still-unreviewed records."""
    result: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        source_id = str(updated["source_id"])
        if source_id in catalog_sources:
            updated["applicability"] = "excluded"
        elif updated["applicability"] != "review_required":
            pass
        elif source_id not in broad_review_sources:
            updated["applicability"] = "provisionally_in_scope"
        result.append(updated)
    return result
