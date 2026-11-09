from __future__ import annotations

from pathlib import Path

from industrialops.evaluation.industrial_retrieval import calculate_metrics, load_frozen_scenarios, write_report
from industrialops.knowledge.pack_loader import AlarmRecord, EquipmentDocument, EquipmentPack
from industrialops.retrieval.industrial import (
    AlarmCodeIndex,
    AliasEnhancer,
    CompatibilityQuery,
    EquipmentMetadataFilter,
    IndustrialRetriever,
)


def _document(document_id: str, *, pack_id: str = "cnc_pack_v1.0.0", model: str = "VF-2", controller: str = "NGC", revision: str = "2025") -> EquipmentDocument:
    return EquipmentDocument(document_id, pack_id, "cnc_vertical_machining_center", "Haas", (model,), controller, "SRC", "manual.pdf", "a" * 64, revision, 3, "SRC:p.3", "Alarm 552 coolant pump", "报警 552 冷却液泵", "zh-CN", "official_zh", document_id, "v1")


def _pack() -> EquipmentPack:
    return EquipmentPack("cnc_pack_v1.0.0", "hash", "v1", (_document("doc-a"), _document("doc-b", revision="2023")), (AlarmRecord("alarm-552", "cnc_pack_v1.0.0", "552", "SRC", "manual.pdf", "a" * 64, 3, "SRC:p.3", "Alarm 552"),))


def test_metadata_filter_normalizes_values_and_never_falls_back_from_an_explicit_mismatch() -> None:
    documents = _pack().documents
    matched = EquipmentMetadataFilter().filter(documents, CompatibilityQuery("cnc_pack_v1.0.0", model="vf 2", controller="ngc", document_revision="2025"))
    mismatched = EquipmentMetadataFilter().filter(documents, CompatibilityQuery("cnc_pack_v1.0.0", model="VF-3"))
    assert [item.document_id for item in matched] == ["doc-a"]
    assert mismatched == []


def test_alarm_index_uses_full_normalized_codes_and_preserves_pack_isolation() -> None:
    index = AlarmCodeIndex([*_pack().alarm_records, AlarmRecord("pump-552", "dry_vacuum_pump_pack_v1.0.0", "5520", "PUMP", "pump.pdf", "b" * 64, 1, "PUMP:p.1", "Alarm 5520")])
    assert [item.candidate_id for item in index.lookup("报警 552", pack_id="cnc_pack_v1.0.0")] == ["alarm-552"]
    assert index.lookup("552", pack_id="dry_vacuum_pump_pack_v1.0.0") == []


def test_alias_enhancer_does_not_modify_an_alarm_code_or_use_other_pack_aliases() -> None:
    enhanced = AliasEnhancer(_pack(), {"equipment_aliases": ["VF2"], "component_aliases": {"coolant pump": ["冷却液泵"]}}).enhance("VF2 报警 552")
    assert enhanced.original_query == "VF2 报警 552"
    assert "552" in enhanced.expanded_query
    assert enhanced.triggered_aliases == ("VF2",)


def test_industrial_retriever_filters_before_ranking_and_returns_evidence() -> None:
    pack = _pack()
    retriever = IndustrialRetriever(pack, embedder=lambda _: (1.0, 0.0), document_vectors={"doc-a": (1.0, 0.0), "doc-b": (0.0, 1.0)}, scorer=lambda _, document_id: 1.0 if document_id == "doc-a" else 0.0)
    results = retriever.retrieve("Alarm 552", CompatibilityQuery("cnc_pack_v1.0.0", document_revision="2025"))
    assert [(item.document.document_id, item.document.evidence_locator, item.final_rank) for item in results] == [("doc-a", "SRC:p.3", 1)]


def test_frozen_metrics_and_report_keep_per_case_evidence(tmp_path: Path) -> None:
    metrics = calculate_metrics([([{"source_id": "SRC", "page_number": 3}], {"allowed_source_ids": ["SRC"], "allowed_pages": [3]})])
    assert metrics.hit_at_1 == metrics.mrr == metrics.ndcg_at_5 == 1.0
    scenario_path = tmp_path / "scenarios.jsonl"
    scenario_path.write_text('{"eval_id":"case","expected_outcome":"retrieve"}\n', encoding="utf-8")
    assert load_frozen_scenarios(scenario_path)[0]["eval_id"] == "case"
    report = write_report(tmp_path / "report.json", {"results": {"case": []}})
    assert 'generated_at_utc' in report.read_text(encoding="utf-8")
