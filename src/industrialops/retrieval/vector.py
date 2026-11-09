"""In-memory cosine retrieval with a caller-supplied query embedder."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence


class VectorIndex:
    def __init__(
        self,
        document_vectors: Mapping[str, Sequence[float]],
        *,
        embedder: Callable[[str], Sequence[float]],
    ) -> None:
        self._embedder = embedder
        self._document_vectors = {
            document_id: _unit_vector(vector)
            for document_id, vector in document_vectors.items()
        }

    def search(self, query: str, *, limit: int) -> list[str]:
        """Return document IDs ordered by decreasing cosine similarity, then ID."""
        query_vector = _unit_vector(self._embedder(query))
        scores: dict[str, float] = {}
        for document_id, vector in self._document_vectors.items():
            if len(vector) != len(query_vector):
                raise ValueError("Query and document vector dimensions must match.")
            scores[document_id] = math.fsum(
                query_component * document_component
                for query_component, document_component in zip(query_vector, vector)
            )
        ranked_ids = sorted(scores, key=lambda document_id: (-scores[document_id], document_id))
        return ranked_ids[:limit]


def _unit_vector(vector: Sequence[float]) -> tuple[float, ...]:
    norm = math.hypot(*vector)
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Cosine similarity requires vectors with a finite, non-zero norm.")
    return tuple(component / norm for component in vector)
