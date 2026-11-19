from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrialops.knowledge.pack_loader import EquipmentDocument, EquipmentPack
from industrialops.retrieval.index_store import IndexIntegrityError, IndexStore


def _document(document_id: str) -> EquipmentDocument:
    return EquipmentDocument(
        document_id=document_id, pack_id="cnc_pack_v1.0.0", equipment_type="cnc", manufacturer="Haas",
        applicable_models=("VF-2",), controller="NGC", source_id="SRC", source_file="source.pdf",
        source_sha256="a" * 64, document_revision="2025", page_number=1, evidence_locator="SRC:p.1",
        text=f"English {document_id}", text_zh=f"中文 {document_id}", language="zh-CN",
        translation_status="official_zh", source_record_id=document_id, registry_version="registry-v1",
    )


def _pack() -> EquipmentPack:
    return EquipmentPack("cnc_pack_v1.0.0", "b" * 64, "registry-v1", (_document("doc-1"), _document("doc-2")), ())


def test_index_store_reuses_a_complete_index_with_identical_frozen_inputs(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def encode(texts: list[str]) -> list[list[float]]:
        calls.append(tuple(texts))
        return [[1.0, 0.0], [0.0, 1.0]]

    store = IndexStore(tmp_path)
    first = store.prepare(_pack(), registry_sha256="c" * 64, model_fingerprint="d" * 64, encode=encode)
    second = store.prepare(_pack(), registry_sha256="c" * 64, model_fingerprint="d" * 64, encode=encode)

    assert first == second
    assert calls == [("English doc-1 中文 doc-1", "English doc-2 中文 doc-2")]
    assert (first.path / "manifest.json").is_file()
    assert (first.path / "document_ids.json").is_file()
    assert (first.path / "vectors.json").is_file()


def test_index_store_creates_a_new_immutable_version_when_model_fingerprint_changes(tmp_path: Path) -> None:
    store = IndexStore(tmp_path)
    first = store.prepare(_pack(), registry_sha256="c" * 64, model_fingerprint="d" * 64, encode=lambda _texts: [[1.0], [2.0]])
    second = store.prepare(_pack(), registry_sha256="c" * 64, model_fingerprint="e" * 64, encode=lambda _texts: [[1.0], [2.0]])

    assert first.index_id != second.index_id
    assert first.path != second.path
    assert first.path.is_dir() and second.path.is_dir()


def test_index_store_refuses_a_corrupted_completed_index_instead_of_silently_using_it(tmp_path: Path) -> None:
    store = IndexStore(tmp_path)
    prepared = store.prepare(_pack(), registry_sha256="c" * 64, model_fingerprint="d" * 64, encode=lambda _texts: [[1.0], [2.0]])
    (prepared.path / "vectors.json").write_text(json.dumps([[1.0]]), encoding="utf-8")

    with pytest.raises(IndexIntegrityError, match="INDEX_VECTOR_COUNT_MISMATCH"):
        store.load(prepared)
