"""Metrics for retrieval results evaluated against declared evidence IDs."""

from __future__ import annotations

from collections.abc import Iterable, Set


def hit_at_k(cases: Iterable[tuple[list[str], Set[str]]], *, k: int) -> float:
    """Return the share of cases with an allowed evidence ID in the top ``k``."""

    materialized_cases = list(cases)
    if not materialized_cases:
        return 0.0
    hits = sum(bool(set(result_ids[:k]) & allowed_ids) for result_ids, allowed_ids in materialized_cases)
    return hits / len(materialized_cases)
