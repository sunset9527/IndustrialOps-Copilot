"""Conservative model-specific scope decisions."""

from __future__ import annotations

import re


_NXDS_MODEL_PATTERN = re.compile(r"\bnXDS(?:6|10|15|20)i(?:C|R)?\b", re.IGNORECASE)


def exclude_exclusive_out_of_scope_nxds_models(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Exclude only pages that name nXDS C/R variants and no standard nXDS model."""
    filtered: list[dict[str, object]] = []
    for record in records:
        updated = dict(record)
        models = sorted(
            {
                match.group(0)
                for match in _NXDS_MODEL_PATTERN.finditer(str(record["text"]))
            },
            key=str.casefold,
        )
        if models and all(model.casefold().endswith(("c", "r")) for model in models):
            updated["applicability"] = "excluded"
            updated["applicability_reasons"] = [
                f"exclusive_out_of_scope_models:{','.join(models)}"
            ]
        filtered.append(updated)
    return filtered
