from __future__ import annotations

from traceback import format_exception

import pytest

from industrialops.retrieval.reranker import Reranker, RerankerUnavailableError


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


@pytest.mark.parametrize("score", [float("nan"), float("inf"), float("-inf")])
def test_reranker_rejects_non_finite_scores(score: float) -> None:
    scores = {"tie-b": 1.0, "invalid": score, "tie-a": 1.0}
    reranker = Reranker(scorer=lambda _, document_id: scores[document_id])

    with pytest.raises(ValueError, match="Reranker score for document 'invalid' must be finite"):
        reranker.rerank("query", ["tie-b", "invalid", "tie-a"])


def test_reranker_reports_scorer_failure_without_exposing_its_details() -> None:
    def unavailable_scorer(query: str, document_id: str) -> float:
        raise FileNotFoundError("Private local model path")

    reranker = Reranker(scorer=unavailable_scorer)

    with pytest.raises(RerankerUnavailableError, match="Local reranker scoring is unavailable") as error:
        reranker.rerank("query", ["candidate"])

    assert "Private local model path" not in "".join(format_exception(error.value))
