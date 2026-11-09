"""Rerank candidate IDs using a caller-supplied local scorer."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable


class RerankerUnavailableError(RuntimeError):
    """The configured local scorer could not score a candidate."""


class Reranker:
    def __init__(self, *, scorer: Callable[[str, str], float] | None = None) -> None:
        if scorer is None:
            raise ValueError("Reranker requires a caller-supplied local scoring function.")
        self._scorer = scorer

    def rerank(self, query: str, candidate_ids: Iterable[str]) -> list[str]:
        """Order candidate IDs by descending finite score, then ascending ID.

        Raise RerankerUnavailableError if the scorer fails.
        """

        def sort_key(document_id: str) -> tuple[float, str]:
            try:
                score = self._scorer(query, document_id)
            except Exception:
                raise RerankerUnavailableError("Local reranker scoring is unavailable.") from None
            if not math.isfinite(score):
                raise ValueError(f"Reranker score for document {document_id!r} must be finite.")
            return -score, document_id

        return sorted(candidate_ids, key=sort_key)
