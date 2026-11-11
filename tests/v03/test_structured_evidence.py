from __future__ import annotations

from pathlib import Path

from industrialops.knowledge.pack_loader import EquipmentPackLoader, StructuredEvidence


def test_loader_exposes_all_auto_reviewed_structured_evidence_from_a_frozen_pack() -> None:
    project_root = Path(__file__).parents[2]
    loader = EquipmentPackLoader(
        project_root / "data" / "packs",
        project_root / "config" / "equipment_pack_registry_v1.json",
    )

    pack = loader.load("cnc_pack_v1.0.0")

    assert len(pack.structured_evidence) == 1196
    assert isinstance(pack.structured_evidence[0], StructuredEvidence)
    assert {item.candidate_type for item in pack.structured_evidence} == {
        "alarms",
        "components",
        "failure_modes",
        "maintenance_tasks",
        "safety_rules",
        "symptoms",
    }
    assert all(item.pack_id == "cnc_pack_v1.0.0" for item in pack.structured_evidence)
    assert all(item.evidence_id == item.candidate_id for item in pack.structured_evidence)
    assert all(item.evidence_text for item in pack.structured_evidence)
