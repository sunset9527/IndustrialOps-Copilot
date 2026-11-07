"""Exclude document types that cannot provide operational evidence."""

from __future__ import annotations


def exclude_non_operational_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Exclude non-operational document pages while preserving technical records."""
    filtered: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        text = str(record["text"]).casefold()
        if "declaration of conformity" in text:
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:conformity_declaration"]
        elif text.startswith("contents\n") or text.startswith("contents "):
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:table_of_contents"]
        elif text.startswith("copyright notice\n") or text.startswith("copyright notice "):
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:copyright_notice"]
        filtered.append(updated)
    return filtered
