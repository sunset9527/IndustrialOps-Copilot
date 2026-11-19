"""Production assembly for the evidence-bound diagnosis workflow."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
import hashlib

from industrialops.config import Settings
from industrialops.diagnosis.context import EquipmentContextResolver, ResolvedEquipmentContext
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.intent import IntentRoute
from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.knowledge.pack_loader import EquipmentPack, EquipmentPackLoader, StructuredEvidence
from industrialops.retrieval.industrial import AlarmCodeIndex, CompatibilityQuery, EquipmentMetadataFilter, IndustrialRetriever
from industrialops.retrieval.local_models import LocalBgeM3, LocalCrossEncoder, model_fingerprint
from industrialops.retrieval.bm25 import Bm25Index, RetrievalDocument
from industrialops.retrieval.index_store import IndexStore


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

    def __init__(
        self,
        pack: EquipmentPack,
        embedding_path: Path,
        reranker_path: Path,
        document_vectors: Mapping[str, object],
    ) -> None:
        self._pack, self._embedding_path, self._reranker_path = pack, embedding_path, reranker_path
        self._document_vectors = document_vectors
        self._retriever: IndustrialRetriever | None = None

    def retrieve(self, query: str, compatibility: CompatibilityQuery, *, limit: int):
        if self._retriever is None:
            eligible = EquipmentMetadataFilter().filter(self._pack.documents, compatibility)
            bm25 = Bm25Index.from_documents(
                [RetrievalDocument(item.document_id, item.text + " " + item.text_zh) for item in eligible]
            )
            candidate_ids = [item.document_id for item in bm25.search(query, limit=32)]
            candidate_documents = tuple(item for item in eligible if item.document_id in set(candidate_ids))
            if not candidate_documents:
                return []
            candidate_pack = EquipmentPack(
                self._pack.pack_id, self._pack.content_sha256, self._pack.registry_version,
                candidate_documents, self._pack.alarm_records, self._pack.structured_evidence,
            )
            embedding = LocalBgeM3(self._embedding_path)
            documents = candidate_pack.documents
            # Bound runtime encoding to the same evidence object rather than
            # letting one unusually long PDF extraction dominate first-query
            # latency. Source text and citations remain untouched.
            index_text = lambda item: (item.text + " " + item.text_zh)[:1000]
            vectors = {
                item.document_id: self._document_vectors[item.document_id]
                for item in documents
                if item.document_id in self._document_vectors
            }
            if len(vectors) != len(documents):
                return []
            reranker = LocalCrossEncoder(self._reranker_path)
            by_id = {item.document_id: item for item in documents}
            self._retriever = IndustrialRetriever(
                candidate_pack,
                embedder=lambda value: embedding.embed(value),
                document_vectors=vectors,
                scorer=lambda question, document_id: reranker.score(question, index_text(by_id[document_id])),
            )
        return self._retriever.retrieve(query, compatibility, limit=limit)


def build_default_workflow(settings: Settings) -> DiagnosisWorkflow:
    root = Path(__file__).resolve().parents[3]
    packs_root = settings.packs_root if settings.packs_root.is_absolute() else root / settings.packs_root
    registry_path = settings.pack_registry_path if settings.pack_registry_path.is_absolute() else root / settings.pack_registry_path
    indexes_root = settings.indexes_root if settings.indexes_root.is_absolute() else root / settings.indexes_root
    loader = EquipmentPackLoader(packs_root, registry_path)
    packs = {
        pack_id: loader.load(pack_id)
        for pack_id in ("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0")
    }
    registry_sha256 = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    index_store = IndexStore(indexes_root)
    embedding_fingerprint = model_fingerprint(settings.bge_model_path)
    vectors_by_pack = {
        pack_id: index_store.read_vectors(index_store.expected_artifact(
            pack, registry_sha256=registry_sha256, model_fingerprint=embedding_fingerprint
        ))
        for pack_id, pack in packs.items()
    }
    return DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path(registry_path),
        retrieve=PackScopedEvidenceRetriever(
            packs,
            document_retrievers={
                pack_id: LocalV02Retriever(
                    pack,
                    settings.bge_model_path,
                    settings.reranker_model_path,
                    vectors_by_pack[pack_id],
                )
                for pack_id, pack in packs.items()
            },
        ),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=settings.deepseek_timeout_seconds,
            max_tokens=settings.deepseek_max_tokens,
            offline_mode=settings.offline_mode,
        ),
    )
