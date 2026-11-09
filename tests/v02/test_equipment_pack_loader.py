from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
import subprocess
import sys
import os
from pathlib import Path

import pytest

from industrialops.knowledge.pack_loader import EquipmentPackLoader


def _canonical_hash(records: list[dict[str, object]]) -> str:
    payload = "\n".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_minimal_pack(tmp_path: Path) -> tuple[Path, Path]:
    pack_id = "cnc_pack_v1.0.0"
    pack_directory = tmp_path / "packs" / pack_id
    pack_directory.mkdir(parents=True)
    corpus = [
        {
            "pack_id": pack_id,
            "chunk_id": "chunk-001",
            "candidate_id": "candidate-001",
            "source_id": "HAAS-TEST",
            "source_file": "manual.pdf",
            "source_sha256": "a" * 64,
            "page_number": 3,
            "evidence_locator": "HAAS-TEST:p.3",
            "text": "VF-2 coolant pump",
            "text_zh": "VF-2 冷却液泵",
            "language": "zh-CN",
            "translation_status": "official_zh",
            "applicability": "approved_in_scope",
        }
    ]
    structured = [
        {
            "pack_id": pack_id,
            "candidate_id": "alarm-552",
            "candidate_type": "alarms",
            "candidate_status": "auto_reviewed_include",
            "label": "552",
            "source_id": "HAAS-TEST",
            "source_file": "manual.pdf",
            "source_sha256": "a" * 64,
            "page_number": 3,
            "evidence_locator": "HAAS-TEST:p.3",
            "evidence_text": "Alarm 552",
        }
    ]
    manifest = {
        "pack_id": pack_id,
        "freeze_status": "read_only_local_evidence",
        "corpus_record_count": len(corpus),
        "structured_candidate_count": len(structured),
        "source_count": 1,
        "sources": [
            {
                "source_id": "HAAS-TEST",
                "relative_path": "manual.pdf",
                "sha256": "a" * 64,
            }
        ],
        "content_sha256": _canonical_hash(corpus),
    }
    (pack_directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pack_directory / "corpus.jsonl").write_text(
        "\n".join(json.dumps(record) for record in corpus) + "\n",
        encoding="utf-8",
    )
    (pack_directory / "structured_candidates_auto_reviewed.jsonl").write_text(
        "\n".join(json.dumps(record) for record in structured) + "\n",
        encoding="utf-8",
    )
    registry_path = tmp_path / "equipment-pack-registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "registry_version": "v1",
                "packs": {
                    pack_id: {
                        "equipment_type": "cnc_vertical_machining_center",
                        "manufacturer": "Haas",
                        "models": ["VF-2"],
                        "controller": "NGC",
                        "equipment_aliases": ["VF2"],
                        "component_aliases": {},
                        "sources": {
                            "HAAS-TEST": {
                                "document_revision": "2025",
                                "applicable_models": ["VF-2"],
                                "controller": "NGC",
                            }
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return pack_directory.parent, registry_path


def test_equipment_pack_loader_is_available_as_a_public_module() -> None:
    project_root = Path(__file__).parents[2]
    environment = os.environ | {"PYTHONPATH": str(project_root / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from industrialops.knowledge.pack_loader import EquipmentPackLoader; print(EquipmentPackLoader.__name__)",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "EquipmentPackLoader"


def test_loader_verifies_a_frozen_pack_and_enriches_its_documents(tmp_path: Path) -> None:
    packs_root, registry_path = _write_minimal_pack(tmp_path)

    loaded_pack = EquipmentPackLoader(packs_root, registry_path).load("cnc_pack_v1.0.0")

    assert loaded_pack.pack_id == "cnc_pack_v1.0.0"
    assert loaded_pack.content_sha256 == _canonical_hash(
        [
            {
                "pack_id": "cnc_pack_v1.0.0",
                "chunk_id": "chunk-001",
                "candidate_id": "candidate-001",
                "source_id": "HAAS-TEST",
                "source_file": "manual.pdf",
                "source_sha256": "a" * 64,
                "page_number": 3,
                "evidence_locator": "HAAS-TEST:p.3",
                "text": "VF-2 coolant pump",
                "text_zh": "VF-2 冷却液泵",
                "language": "zh-CN",
                "translation_status": "official_zh",
                "applicability": "approved_in_scope",
            }
        ]
    )
    assert len(loaded_pack.documents) == 1
    assert asdict(loaded_pack.documents[0]) == {
        "document_id": "chunk-001",
        "pack_id": "cnc_pack_v1.0.0",
        "equipment_type": "cnc_vertical_machining_center",
        "manufacturer": "Haas",
        "applicable_models": ("VF-2",),
        "controller": "NGC",
        "source_id": "HAAS-TEST",
        "source_file": "manual.pdf",
        "source_sha256": "a" * 64,
        "document_revision": "2025",
        "page_number": 3,
        "evidence_locator": "HAAS-TEST:p.3",
        "text": "VF-2 coolant pump",
        "text_zh": "VF-2 冷却液泵",
        "language": "zh-CN",
        "translation_status": "official_zh",
        "source_record_id": "candidate-001",
        "registry_version": "v1",
    }
    assert loaded_pack.alarm_records[0].label == "552"


def test_loader_rejects_a_corpus_whose_content_hash_no_longer_matches(tmp_path: Path) -> None:
    packs_root, registry_path = _write_minimal_pack(tmp_path)
    corpus_path = packs_root / "cnc_pack_v1.0.0" / "corpus.jsonl"
    tampered_record = json.loads(corpus_path.read_text(encoding="utf-8"))
    tampered_record["text"] = "tampered evidence"
    corpus_path.write_text(json.dumps(tampered_record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="PACK_CONTENT_HASH_MISMATCH"):
        EquipmentPackLoader(packs_root, registry_path).load("cnc_pack_v1.0.0")


def test_loader_independently_loads_both_real_frozen_packs() -> None:
    project_root = Path(__file__).parents[2]
    loader = EquipmentPackLoader(
        project_root / "data" / "packs",
        project_root / "config" / "equipment_pack_registry_v1.json",
    )

    cnc_pack = loader.load("cnc_pack_v1.0.0")
    pump_pack = loader.load("dry_vacuum_pump_pack_v1.0.0")

    assert len(cnc_pack.documents) == 1212
    assert len(pump_pack.documents) == 128
    assert {document.pack_id for document in cnc_pack.documents} == {"cnc_pack_v1.0.0"}
    assert {document.pack_id for document in pump_pack.documents} == {"dry_vacuum_pump_pack_v1.0.0"}
