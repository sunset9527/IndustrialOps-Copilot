from __future__ import annotations

from industrialops.retrieval.index_snapshot import build_index_snapshot


def test_index_snapshot_has_a_stable_hash_independent_of_input_order() -> None:
    first = build_index_snapshot("v0.1", ["manual-b", "manual-a"])
    second = build_index_snapshot("v0.1", ["manual-a", "manual-b"])

    assert first.version == "v0.1"
    assert first.document_ids == ("manual-a", "manual-b")
    assert first.content_sha256 == second.content_sha256
