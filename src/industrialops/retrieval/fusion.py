"""Rank-fusion helpers shared by later retrieval adapters."""

from __future__ import annotations


def reciprocal_rank_fusion(rankings: list[list[str]], *, limit: int, k: int = 60) -> list[str]:
    """Merge ranked document IDs using reciprocal rank fusion."""

    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, document_id in enumerate(ranking, start=1):
            scores[document_id] = scores.get(document_id, 0.0) + 1 / (k + rank)
    return [document_id for document_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]]
