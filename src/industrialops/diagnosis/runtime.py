"""Production assembly for the evidence-bound diagnosis workflow."""

from __future__ import annotations

from pathlib import Path

from industrialops.config import Settings
from industrialops.diagnosis.context import EquipmentContextResolver, ResolvedEquipmentContext
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.intent import IntentRoute
from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.knowledge.pack_loader import EquipmentPack, EquipmentPackLoader, StructuredEvidence
from industrialops.retrieval.industrial import AlarmCodeIndex, CompatibilityQuery, EquipmentMetadataFilter, normalize_alarm_code


class PackScopedEvidenceRetriever:
    """Retrieve only approved structured evidence from one verified pack.

    This runtime layer is deliberately conservative: it never switches packs and it
    derives the eligible source set through the existing v0.2 compatibility filter.
    """

    def __init__(self, packs: dict[str, EquipmentPack]) -> None:
        self._packs = packs

    def __call__(
        self, request: DiagnosisRequest, context: ResolvedEquipmentContext, route: IntentRoute
    ) -> tuple[StructuredEvidence, ...]:
        pack = self._packs.get(request.pack_id)
        if pack is None:
            return ()
        eligible_documents = EquipmentMetadataFilter().filter(
            pack.documents,
            CompatibilityQuery(
                pack_id=request.pack_id,
                model=context.model,
                controller=context.controller,
                document_revision=context.document_revision,
            ),
        )
        eligible_sources = {document.source_id for document in eligible_documents}
        evidence = [item for item in pack.structured_evidence if item.source_id in eligible_sources]
        if route.alarm_code:
            exact_ids = {item.candidate_id for item in AlarmCodeIndex(pack.alarm_records).lookup(route.alarm_code, pack_id=pack.pack_id)}
            return tuple(item for item in evidence if item.candidate_id in exact_ids)
        terms = {term.casefold() for term in request.question.replace("，", " ").replace("。", " ").split() if len(term) > 1}
        ranked = [
            item
            for item in evidence
            if not terms or any(term in (item.label + " " + item.evidence_text).casefold() for term in terms)
        ]
        return tuple(sorted(ranked, key=lambda item: item.candidate_id)[:20])


def build_default_workflow(settings: Settings) -> DiagnosisWorkflow:
    root = Path(__file__).resolve().parents[3]
    loader = EquipmentPackLoader(root / "data" / "packs", root / "config" / "equipment_pack_registry_v1.json")
    packs = {
        pack_id: loader.load(pack_id)
        for pack_id in ("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0")
    }
    return DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path(root / "config" / "equipment_pack_registry_v1.json"),
        retrieve=PackScopedEvidenceRetriever(packs),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=settings.deepseek_timeout_seconds,
            max_tokens=settings.deepseek_max_tokens,
        ),
    )
