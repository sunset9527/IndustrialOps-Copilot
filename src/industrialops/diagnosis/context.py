"""Resolve only explicitly supplied equipment context against the versioned registry."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.retrieval.industrial import normalize_value


@dataclass(frozen=True)
class ResolvedEquipmentContext:
    status: str
    pack_id: str
    equipment_type: str | None
    manufacturer: str | None
    model: str | None
    controller: str | None
    document_revision: str | None
    reason_code: str | None = None


class EquipmentContextResolver:
    def __init__(self, registry: dict[str, Any]) -> None:
        self._registry = registry

    @classmethod
    def from_registry_path(cls, path: str | Path) -> "EquipmentContextResolver":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, request: DiagnosisRequest) -> ResolvedEquipmentContext:
        packs = self._registry.get("packs", {})
        pack = packs.get(request.pack_id)
        if not isinstance(pack, dict):
            return ResolvedEquipmentContext("pack_unknown", request.pack_id, None, None, None, None, None, "PACK_UNKNOWN")

        canonical_model = self._canonical_model(pack, request.model)
        if request.model is not None and canonical_model is None:
            return ResolvedEquipmentContext(
                "model_out_of_scope",
                request.pack_id,
                str(pack.get("equipment_type")),
                str(pack.get("manufacturer")),
                None,
                None,
                request.document_revision,
                "MODEL_OR_VARIANT_OUT_OF_SCOPE",
            )
        status = "model_unknown" if canonical_model is None else "compatible"
        return ResolvedEquipmentContext(
            status,
            request.pack_id,
            str(pack.get("equipment_type")),
            str(pack.get("manufacturer")),
            canonical_model,
            self._canonical_controller(pack, request.controller),
            request.document_revision,
        )

    def document_revision(self, pack_id: str, source_id: str) -> str:
        pack = self._registry.get("packs", {}).get(pack_id, {})
        source = pack.get("sources", {}).get(source_id, {}) if isinstance(pack, dict) else {}
        revision = source.get("document_revision") if isinstance(source, dict) else None
        return revision if isinstance(revision, str) else "unknown"

    @staticmethod
    def _canonical_model(pack: dict[str, Any], value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_value(value)
        for model in pack.get("models", []):
            if isinstance(model, str) and normalize_value(model) == normalized:
                return model
        return None

    @staticmethod
    def _canonical_controller(pack: dict[str, Any], value: str | None) -> str | None:
        if value is None:
            return None
        controller = pack.get("controller")
        if isinstance(controller, str) and normalize_value(controller) == normalize_value(value):
            return controller
        return None
