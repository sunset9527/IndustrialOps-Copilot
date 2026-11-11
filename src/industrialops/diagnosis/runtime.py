"""Production assembly for the evidence-bound diagnosis workflow."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping

from industrialops.config import Settings
from industrialops.diagnosis.context import EquipmentContextResolver, ResolvedEquipmentContext
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.intent import IntentRoute
from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.knowledge.pack_loader import EquipmentPack, EquipmentPackLoader, StructuredEvidence
from industrialops.retrieval.industrial import AlarmCodeIndex, CompatibilityQuery, EquipmentMetadataFilter, IndustrialRetriever
from industrialops.retrieval.local_models import LocalBgeM3, LocalCrossEncoder


class PackScopedEvidenceRetriever:
    """Retrieve only approved structured evidence from one verified pack.

    This runtime layer is deliberately conservative: it never switches packs and it
    derives the eligible source set through the existing v0.2 compatibility filter.
    """

    def __init__(self, packs: dict[str, EquipmentPack], *, document_retrievers: Mapping[str, object] | None = None) -> None:
        self._packs = packs
        self._document_retrievers = document_retrievers or {}

    def __call__(
        self, request: DiagnosisRequest, context: ResolvedEquipmentContext, route: IntentRoute
    ) -> tuple[StructuredEvidence, ...]:
        pack = self._packs.get(request.pack_id)
        if pack is None:
            return ()
        compatibility = CompatibilityQuery(
            pack_id=request.pack_id,
            model=context.model,
            controller=context.controller,
            document_revision=context.document_revision,
        )
        eligible_documents = EquipmentMetadataFilter().filter(
            pack.documents,
            compatibility,
        )
        eligible_sources = {document.source_id for document in eligible_documents}
        evidence = [item for item in pack.structured_evidence if item.source_id in eligible_sources]
        if route.alarm_code:
            exact_ids = {item.candidate_id for item in AlarmCodeIndex(pack.alarm_records).lookup(route.alarm_code, pack_id=pack.pack_id)}
            return tuple(item for item in evidence if item.candidate_id in exact_ids)
        ranked = self._document_retrievers.get(pack.pack_id)
        if ranked is not None:
            ranked_documents = ranked.retrieve(request.question, compatibility, limit=10)
            eligible_sources = {item.document.source_id for item in ranked_documents}
            evidence = [item for item in evidence if item.source_id in eligible_sources]
        if ranked is not None:
            return tuple(sorted(evidence, key=lambda item: item.candidate_id)[:20])
        terms = {term.casefold() for term in request.question.replace("，", " ").replace("。", " ").split() if len(term) > 1}
        ranked = [
            item
            for item in evidence
            if not terms or any(term in (item.label + " " + item.evidence_text).casefold() for term in terms)
        ]
        return tuple(sorted(ranked, key=lambda item: item.candidate_id)[:20])


class LocalV02Retriever:
    """Lazy, pack-local BGE-M3/RRF/reranker index used by the diagnosis runtime."""

    def __init__(self, pack: EquipmentPack, embedding_path: Path, reranker_path: Path) -> None:
        self._pack, self._embedding_path, self._reranker_path = pack, embedding_path, reranker_path
        self._retriever: IndustrialRetriever | None = None

    def retrieve(self, query: str, compatibility: CompatibilityQuery, *, limit: int):
        if self._retriever is None:
            embedding = LocalBgeM3(self._embedding_path)
            documents = self._pack.documents
            vectors = embedding.embed([item.text + " " + item.text_zh for item in documents])
            reranker = LocalCrossEncoder(self._reranker_path)
            by_id = {item.document_id: item for item in documents}
            self._retriever = IndustrialRetriever(
                self._pack,
                embedder=lambda value: embedding.embed(value),
                document_vectors=dict(zip((item.document_id for item in documents), vectors, strict=True)),
                scorer=lambda question, document_id: reranker.score(question, by_id[document_id].text + " " + by_id[document_id].text_zh),
            )
        return self._retriever.retrieve(query, compatibility, limit=limit)


def build_default_workflow(settings: Settings) -> DiagnosisWorkflow:
    root = Path(__file__).resolve().parents[3]
    loader = EquipmentPackLoader(root / "data" / "packs", root / "config" / "equipment_pack_registry_v1.json")
    packs = {
        pack_id: loader.load(pack_id)
        for pack_id in ("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0")
    }
    return DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path(root / "config" / "equipment_pack_registry_v1.json"),
        retrieve=PackScopedEvidenceRetriever(
            packs,
            document_retrievers={
                pack_id: LocalV02Retriever(pack, Path(r"E:\huggingface\model"), Path(r"E:\huggingface\bge-reranker-base"))
                for pack_id, pack in packs.items()
            },
        ),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=settings.deepseek_timeout_seconds,
            max_tokens=settings.deepseek_max_tokens,
        ),
    )
