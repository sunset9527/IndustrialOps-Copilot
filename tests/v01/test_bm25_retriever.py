from __future__ import annotations

from industrialops.retrieval.bm25 import Bm25Index, RetrievalDocument


def test_bm25_ranks_an_exact_alarm_code_match_before_unrelated_documents() -> None:
    index = Bm25Index.from_documents(
        [
            RetrievalDocument("alarm-101", "Alarm 101 indicates lubrication pressure is low."),
            RetrievalDocument("safety", "Lock out energy sources before inspection."),
        ]
    )

    results = index.search("Alarm 101", limit=2)

    assert [result.document_id for result in results] == ["alarm-101"]


def test_bm25_returns_no_result_when_query_has_no_indexed_terms() -> None:
    index = Bm25Index.from_documents([RetrievalDocument("safety", "Lock out energy sources.")])

    assert index.search("vacuum pump", limit=5) == []
