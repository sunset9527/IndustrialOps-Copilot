from __future__ import annotations

from industrialops.diagnosis.faults import FaultDiagnosisService
from industrialops.knowledge.pack_loader import StructuredEvidence


def _evidence(kind: str, label: str) -> StructuredEvidence:
    return StructuredEvidence(label, label, kind, "cnc_pack_v1.0.0", label, "SRC", "manual.pdf", "a" * 64, 3, "SRC:p.3", f"{kind} text")


def test_fault_diagnosis_service_separates_facts_causes_steps_and_safety_evidence() -> None:
    result = FaultDiagnosisService().extract((
        _evidence("alarms", "552"), _evidence("failure_modes", "coolant_pump_short"),
        _evidence("maintenance_tasks", "inspect_pump"), _evidence("safety_rules", "isolate_power"),
    ))

    assert result.confirmed_facts == ("alarms text",)
    assert result.candidate_causes == ("failure_modes text",)
    assert result.inspection_steps == ("maintenance_tasks text",)
    assert result.safety_prerequisites == ("safety_rules text",)
