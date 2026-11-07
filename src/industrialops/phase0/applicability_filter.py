"""Conservative applicability filtering for the declared equipment scope."""

from __future__ import annotations


def apply_exclusion_terms(
    candidates: list[dict[str, object]],
    exclusion_terms: list[str],
) -> list[dict[str, object]]:
    """Flag candidates with explicit out-of-scope terms for mixed-scope review.

    A term can be an incidental cross-reference on an otherwise applicable page.
    Therefore term matching alone never performs a final exclusion. Candidates
    without a match also remain review-required because absence of a forbidden
    term is not proof that a mixed manual page applies.
    """
    filtered: list[dict[str, object]] = []
    for candidate in candidates:
        text = str(candidate["text"])
        matches = [term for term in exclusion_terms if term.casefold() in text.casefold()]
        result = dict(candidate)
        result["applicability_reasons"] = [
            f"explicit_out_of_scope_term:{term}" for term in matches
        ]
        if matches:
            result["applicability"] = "mixed_scope_review"
        filtered.append(result)
    return filtered
