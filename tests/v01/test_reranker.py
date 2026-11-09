from __future__ import annotations

import pytest

from industrialops.retrieval.reranker import Reranker


def test_reranker_scores_only_the_candidates_and_breaks_ties_by_document_id() -> None:
    scores = {
        ("query", "best"): 2.0,
        ("query", "tie-b"): 1.0,
        ("query", "tie-a"): 1.0,
        ("query", "outside"): 3.0,
    }
    scored_ids = []

    def scorer(query: str, document_id: str) -> float:
        scored_ids.append(document_id)
        return scores[query, document_id]

    candidates = ["tie-b", "best", "tie-a"]

    assert Reranker(scorer=scorer).rerank("query", candidates) == ["best", "tie-a", "tie-b"]
    assert sorted(scored_ids) == sorted(candidates)


def test_reranker_requires_a_caller_supplied_local_scorer() -> None:
    with pytest.raises(ValueError, match="caller-supplied local scoring function"):
        Reranker()
