from __future__ import annotations

import pytest

from industrialops.phase0.pack_freezer import build_pack_manifests


def _source(pack: str, source_id: str) -> dict[str, object]:
    return {"source_id": source_id, "sha256": "a" * 64, "relative_path": f"{source_id}.pdf", "url": "https://example.test", "rights_boundary": "local_evidence_only", "pack_id": pack}


def _corpus(pack: str, source_id: str) -> dict[str, object]:
    return {"pack_id": pack, "source_id": source_id, "source_file": f"{source_id}.pdf", "source_sha256": "a" * 64, "page_number": 1, "evidence_locator": f"{source_id}:p.1", "text": "source", "original_text": "source", "text_zh": "来源", "translation_status": "source_zh"}


def test_build_pack_manifests_is_deterministic_and_keeps_rights_boundary() -> None:
    sources = [_source("cnc_pack_v1.0.0", "HAAS-1"), _source("dry_vacuum_pump_pack_v1.0.0", "EDW-1")]
    corpus = [_corpus("cnc_pack_v1.0.0", "HAAS-1"), _corpus("dry_vacuum_pump_pack_v1.0.0", "EDW-1")]

    first = build_pack_manifests(sources, corpus)
    second = build_pack_manifests(sources, corpus)

    assert first == second
    assert first["cnc_pack_v1.0.0"]["source_count"] == 1
    assert first["cnc_pack_v1.0.0"]["rights_boundary"] == "local_evidence_only"


def test_build_pack_manifests_rejects_corpus_source_missing_from_registry() -> None:
    with pytest.raises(ValueError):
        build_pack_manifests([], [_corpus("cnc_pack_v1.0.0", "HAAS-1")])
