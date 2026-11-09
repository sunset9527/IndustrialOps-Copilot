from __future__ import annotations

import pytest

from industrialops.retrieval.vector import VectorIndex


def test_vector_search_ranks_by_cosine_similarity_then_document_id() -> None:
    def embedder(query: str) -> tuple[float, ...]:
        return {"query": (1.0, 0.0)}[query]

    index = VectorIndex(
        {
            "diagonal": (100.0, 100.0),
            "parallel-b": (3.0, 0.0),
            "parallel-a": (2.0, 0.0),
            "opposite": (-1.0, 0.0),
        },
        embedder=embedder,
    )

    assert index.search("query", limit=3) == ["parallel-a", "parallel-b", "diagonal"]


def test_vector_search_rejects_a_query_with_a_different_dimension() -> None:
    index = VectorIndex({"doc": (1.0, 0.0)}, embedder=lambda _: (1.0,))

    with pytest.raises(ValueError, match="vector dimensions must match"):
        index.search("query", limit=1)


@pytest.mark.parametrize("embedding", [(0.0, 0.0), (float("nan"), 1.0)])
def test_vector_search_rejects_an_undefined_cosine(embedding: tuple[float, ...]) -> None:
    index = VectorIndex({"doc": (1.0, 0.0)}, embedder=lambda _: embedding)

    with pytest.raises(ValueError, match="finite, non-zero norm"):
        index.search("query", limit=1)
