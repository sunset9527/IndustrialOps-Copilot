"""Extract answer fields from approved structured evidence without inference."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from industrialops.knowledge.pack_loader import StructuredEvidence


@dataclass(frozen=True)
class DiagnosisExtraction:
    confirmed_facts: tuple[str, ...]
    candidate_causes: tuple[str, ...]
    inspection_steps: tuple[str, ...]
    safety_prerequisites: tuple[str, ...]


class FaultDiagnosisService:
    """Project evidence types into explicitly non-deterministic answer fields."""

    def extract(self, evidence: Iterable[StructuredEvidence]) -> DiagnosisExtraction:
        by_type: dict[str, list[str]] = {}
        for item in evidence:
            by_type.setdefault(item.candidate_type, []).append(item.evidence_text)
        return DiagnosisExtraction(
            confirmed_facts=tuple(by_type.get("alarms", ())),
            candidate_causes=tuple([*by_type.get("symptoms", ()), *by_type.get("failure_modes", ())]),
            inspection_steps=tuple(by_type.get("maintenance_tasks", ())),
            safety_prerequisites=tuple(by_type.get("safety_rules", ())),
        )
