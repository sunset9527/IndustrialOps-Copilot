"""Exclude document types that cannot provide operational evidence."""

from __future__ import annotations


def exclude_non_operational_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Exclude conformity declarations while preserving all technical records."""
    filtered: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        if "declaration of conformity" in str(record["text"]).casefold():
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:conformity_declaration"]
        filtered.append(updated)
    return filtered
