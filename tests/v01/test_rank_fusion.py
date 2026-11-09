from __future__ import annotations

from industrialops.retrieval.fusion import reciprocal_rank_fusion


def test_rrf_combines_rankings_without_duplicate_document_ids() -> None:
    results = reciprocal_rank_fusion(
        [["alarm-101", "safety"], ["safety", "maintenance"]],
        limit=3,
    )

    assert results == ["safety", "alarm-101", "maintenance"]
