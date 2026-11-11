"""Evidence sufficiency rules for diagnosis response fields."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from industrialops.knowledge.pack_loader import StructuredEvidence


@dataclass(frozen=True)
class EvidenceDecision:
    status: str
    allowed_fields: tuple[str, ...]
    missing_evidence_types: tuple[str, ...]


class EvidenceGapDetector:
    """Determine what can be said from approved, compatible evidence only."""

    def evaluate(self, intent: str, evidence: Iterable[StructuredEvidence]) -> EvidenceDecision:
        types = {item.candidate_type for item in evidence}
        if intent == "fault_diagnosis":
            has_cause = bool(types & {"symptoms", "failure_modes"})
            if not has_cause:
                return EvidenceDecision("insufficient_evidence", (), ("symptoms_or_failure_modes",))
            missing: list[str] = []
            if "maintenance_tasks" not in types:
                missing.append("maintenance_tasks")
            if "safety_rules" not in types:
                missing.append("safety_rules")
            if missing:
                return EvidenceDecision("insufficient_evidence", ("candidate_causes",), tuple(missing))
            return EvidenceDecision("sufficient", ("candidate_causes", "inspection_steps"), ())
        if intent == "alarm_lookup":
            return EvidenceDecision("sufficient", ("confirmed_facts",), ()) if "alarms" in types else EvidenceDecision("insufficient_evidence", (), ("alarms",))
        if intent == "maintenance_plan":
            return EvidenceDecision("sufficient", ("inspection_steps",), ()) if "maintenance_tasks" in types else EvidenceDecision("insufficient_evidence", (), ("maintenance_tasks",))
        if intent == "manual_query":
            return EvidenceDecision("sufficient", ("confirmed_facts",), ()) if types else EvidenceDecision("insufficient_evidence", (), ("compatible_evidence",))
        return EvidenceDecision("insufficient_evidence", (), ("supported_intent",))
