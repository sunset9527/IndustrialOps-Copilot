from __future__ import annotations

from industrialops.diagnosis.context import ResolvedEquipmentContext
from industrialops.diagnosis.intent import IntentRoute
from industrialops.diagnosis.runtime import PackScopedEvidenceRetriever
from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.knowledge.pack_loader import AlarmRecord, EquipmentDocument, EquipmentPack, StructuredEvidence
from industrialops.retrieval.industrial import IndustrialRetrievalResult


def _document(document_id: str, source_id: str) -> EquipmentDocument:
    return EquipmentDocument(document_id, "cnc_pack_v1.0.0", "cnc_vertical_machining_center", "Haas", ("VF-2",), "NGC", source_id, f"{source_id}.pdf", "a" * 64, "2025", 3, f"{source_id}:p.3", "spindle noise", "主轴异响", "zh-CN", "official_zh", document_id, "v1")


def _evidence(evidence_id: str, source_id: str) -> StructuredEvidence:
    return StructuredEvidence(evidence_id, evidence_id, "failure_modes", "cnc_pack_v1.0.0", "spindle", source_id, f"{source_id}.pdf", "a" * 64, 3, f"{source_id}:p.3", "failure evidence")


def test_runtime_evidence_retriever_projects_only_v02_ranked_document_sources_into_structured_evidence() -> None:
    first, second = _document("doc-1", "SRC-1"), _document("doc-2", "SRC-2")
    pack = EquipmentPack("cnc_pack_v1.0.0", "hash", "v1", (first, second), (), (_evidence("evidence-1", "SRC-1"), _evidence("evidence-2", "SRC-2")))

    class RankedRetriever:
        def retrieve(self, query, compatibility, *, limit):
            assert query == "主轴异响"
            assert compatibility.model == "VF-2"
            assert limit == 10
            return [IndustrialRetrievalResult(first, 1, ("bm25", "vector", "rrf", "rerank"))]

    retriever = PackScopedEvidenceRetriever({pack.pack_id: pack}, document_retrievers={pack.pack_id: RankedRetriever()})
    result = retriever(
        DiagnosisRequest(question="主轴异响", pack_id=pack.pack_id, model="VF-2"),
        ResolvedEquipmentContext("compatible", pack.pack_id, "cnc_vertical_machining_center", "Haas", "VF-2", "NGC", None),
        IntentRoute("fault_diagnosis", "DIAGNOSIS_REQUEST"),
    )

    assert [item.evidence_id for item in result] == ["evidence-1"]


def test_exact_alarm_lookup_does_not_build_the_semantic_retriever() -> None:
    document = _document("doc-1", "SRC-1")
    alarm = StructuredEvidence("alarm-552", "alarm-552", "alarms", "cnc_pack_v1.0.0", "552", "SRC-1", "SRC-1.pdf", "a" * 64, 3, "SRC-1:p.3", "Alarm 552 evidence")
    pack = EquipmentPack("cnc_pack_v1.0.0", "hash", "v1", (document,), (AlarmRecord("alarm-552", "cnc_pack_v1.0.0", "552", "SRC-1", "SRC-1.pdf", "a" * 64, 3, "SRC-1:p.3", "Alarm 552 evidence"),), (alarm,))

    class MustNotRun:
        def retrieve(self, *args, **kwargs):
            raise AssertionError("exact alarm lookup must bypass semantic retrieval")

    result = PackScopedEvidenceRetriever({pack.pack_id: pack}, document_retrievers={pack.pack_id: MustNotRun()})(
        DiagnosisRequest(question="报警 552", pack_id=pack.pack_id, model="VF-2"),
        ResolvedEquipmentContext("compatible", pack.pack_id, "cnc_vertical_machining_center", "Haas", "VF-2", "NGC", None),
        IntentRoute("alarm_lookup", "EXPLICIT_ALARM_CODE", "552"),
    )

    assert result == (alarm,)
