"""Rerank candidate IDs using a caller-supplied local scorer."""

from __future__ import annotations

from collections.abc import Callable, Iterable


class Reranker:
    def __init__(self, *, scorer: Callable[[str, str], float] | None = None) -> None:
        if scorer is None:
            raise ValueError("Reranker requires a caller-supplied local scoring function.")
        self._scorer = scorer

    def rerank(self, query: str, candidate_ids: Iterable[str]) -> list[str]:
        """Order candidate IDs by descending scorer value, then ascending ID."""
        return sorted(
            candidate_ids,
            key=lambda document_id: (-self._scorer(query, document_id), document_id),
        )
