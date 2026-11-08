"""Exclude document types that cannot provide operational evidence."""

from __future__ import annotations

import re


def _is_dot_leader_contents_entry(text: str) -> bool:
    """Return whether every visible line is a table-of-contents entry."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return bool(lines) and all(re.search(r"(?:\.\s*){3,}\d+\s*$", line) for line in lines)


def exclude_non_operational_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Exclude non-operational document pages while preserving technical records."""
    filtered: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        text = str(record["text"]).casefold()
        compact_text = re.sub(r"\s+", "", text)
        if "declarationofconformity" in compact_text:
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:conformity_declaration"]
        elif (
            text.startswith("contents\n")
            or text.startswith("contents ")
            or _is_dot_leader_contents_entry(text)
        ):
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:table_of_contents"]
        elif text.startswith("copyright notice\n") or text.startswith("copyright notice "):
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = ["non_operational_document_type:copyright_notice"]
        filtered.append(updated)
    return filtered
