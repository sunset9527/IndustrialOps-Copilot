"""Pack-scoped industrial retrieval with deterministic compatibility controls."""
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Callable, Iterable, Sequence

from industrialops.knowledge.pack_loader import AlarmRecord, EquipmentDocument, EquipmentPack
from industrialops.retrieval.bm25 import Bm25Index, RetrievalDocument
from industrialops.retrieval.fusion import reciprocal_rank_fusion
from industrialops.retrieval.reranker import Reranker
from industrialops.retrieval.vector import VectorIndex


def normalize_value(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value).casefold()


@dataclass(frozen=True)
class CompatibilityQuery:
    pack_id: str
    equipment_type: str | None = None
    model: str | None = None
    controller: str | None = None
    document_revision: str | None = None


class EquipmentMetadataFilter:
    def filter(self, documents: Iterable[EquipmentDocument], query: CompatibilityQuery) -> list[EquipmentDocument]:
        result: list[EquipmentDocument] = []
        for document in documents:
            if document.pack_id != query.pack_id:
                continue
            if query.equipment_type and normalize_value(document.equipment_type) != normalize_value(query.equipment_type):
                continue
            if query.model and normalize_value(query.model) not in {normalize_value(item) for item in document.applicable_models}:
                continue
            if query.controller and normalize_value(query.controller) != normalize_value(document.controller):
                continue
            if query.document_revision and normalize_value(query.document_revision) != normalize_value(document.document_revision):
                continue
            result.append(document)
        return result


def normalize_alarm_code(value: str) -> str:
    cleaned = re.sub(r"(?i)\balarm\b|报警", "", value)
    return re.sub(r"[\s_\-:/]+", "", cleaned).upper()


class AlarmCodeIndex:
    def __init__(self, records: Iterable[AlarmRecord]) -> None:
        self._by_code: dict[str, list[AlarmRecord]] = {}
        for record in records:
            self._by_code.setdefault(normalize_alarm_code(record.label), []).append(record)
        for records_for_code in self._by_code.values():
            records_for_code.sort(key=lambda item: (item.source_id, item.page_number, item.candidate_id))

    def lookup(self, code: str, *, pack_id: str) -> list[AlarmRecord]:
        return [item for item in self._by_code.get(normalize_alarm_code(code), []) if item.pack_id == pack_id]


@dataclass(frozen=True)
class QueryExpansion:
    original_query: str
    expanded_query: str
    triggered_aliases: tuple[str, ...]
    registry_version: str


class AliasEnhancer:
    def __init__(self, pack: EquipmentPack, aliases: dict[str, object]) -> None:
        self._pack = pack
        self._aliases = aliases

    def enhance(self, query: str) -> QueryExpansion:
        additions: list[str] = []
        triggered: list[str] = []
        normalized_query = normalize_value(query)
        for category in ("equipment_aliases", "component_aliases"):
            value = self._aliases.get(category, [] if category == "equipment_aliases" else {})
            entries = value.values() if isinstance(value, dict) else [value]
            for aliases in entries:
                for alias in aliases if isinstance(aliases, list) else []:
                    if normalize_value(str(alias)) in normalized_query:
                        triggered.append(str(alias))
                        additions.append(str(alias))
        return QueryExpansion(query, " ".join([query, *dict.fromkeys(additions)]), tuple(dict.fromkeys(triggered)), self._pack.registry_version)


@dataclass(frozen=True)
class IndustrialRetrievalResult:
    document: EquipmentDocument
    final_rank: int
    stages: tuple[str, ...]


class IndustrialRetriever:
    """A strictly pack-scoped retriever; no cross-pack fallback exists."""
    def __init__(self, pack: EquipmentPack, *, embedder: Callable[[str], Sequence[float]], document_vectors: dict[str, Sequence[float]], scorer: Callable[[str, str], float]) -> None:
        self._pack = pack
        self._documents = {document.document_id: document for document in pack.documents}
        self._bm25 = Bm25Index.from_documents([RetrievalDocument(item.document_id, item.text + " " + item.text_zh) for item in pack.documents])
        self._vector = VectorIndex(document_vectors, embedder=embedder)
        self._reranker = Reranker(scorer=scorer)

    def retrieve(self, query: str, compatibility: CompatibilityQuery, *, limit: int = 5) -> list[IndustrialRetrievalResult]:
        eligible = EquipmentMetadataFilter().filter(self._pack.documents, compatibility)
        eligible_ids = {item.document_id for item in eligible}
        bm25 = [item.document_id for item in self._bm25.search(query, limit=len(self._documents)) if item.document_id in eligible_ids]
        vector = [item for item in self._vector.search(query, limit=len(self._documents)) if item in eligible_ids]
        fused = reciprocal_rank_fusion([bm25, vector], limit=len(eligible_ids))
        reranked = self._reranker.rerank(query, fused)
        return [IndustrialRetrievalResult(self._documents[item], rank, ("bm25", "vector", "rrf", "rerank")) for rank, item in enumerate(reranked[:limit], 1)]
