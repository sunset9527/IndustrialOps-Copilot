from __future__ import annotations

from industrialops.evaluation.retrieval_metrics import hit_at_k


def test_hit_at_k_counts_queries_with_an_allowed_evidence_id_in_the_top_k() -> None:
    score = hit_at_k(
        [
            (["alarm-101", "safety"], {"alarm-101"}),
            (["maintenance", "safety"], {"alarm-207"}),
            (["safety", "maintenance"], {"safety"}),
        ],
        k=1,
    )

    assert score == 2 / 3


def test_hit_at_k_returns_zero_for_an_empty_evaluation_set() -> None:
    assert hit_at_k([], k=5) == 0.0
