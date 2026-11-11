from __future__ import annotations

from industrialops.diagnosis.context import ResolvedEquipmentContext
from industrialops.diagnosis.evidence import EvidenceGapDetector
from industrialops.diagnosis.safety import SafetyPolicyGate
from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.knowledge.pack_loader import StructuredEvidence


def _context(status: str = "compatible", model: str | None = "VF-2") -> ResolvedEquipmentContext:
    return ResolvedEquipmentContext(
        status=status,
        pack_id="cnc_pack_v1.0.0",
        equipment_type="cnc_vertical_machining_center",
        manufacturer="Haas",
        model=model,
        controller="NGC",
        document_revision=None,
    )


def _evidence(candidate_type: str, evidence_id: str) -> StructuredEvidence:
    return StructuredEvidence(
        evidence_id=evidence_id,
        candidate_id=evidence_id,
        candidate_type=candidate_type,
        pack_id="cnc_pack_v1.0.0",
        label="spindle",
        source_id="HAAS-TEST",
        source_file="manual.pdf",
        source_sha256="a" * 64,
        page_number=3,
        evidence_locator="HAAS-TEST:p.3",
        evidence_text="Approved evidence",
    )


def test_safety_gate_requires_a_model_before_a_fault_diagnosis_can_include_repair_advice() -> None:
    decision = SafetyPolicyGate().evaluate(
        DiagnosisRequest(question="主轴异响，给我维修步骤", pack_id="cnc_pack_v1.0.0"),
        intent="fault_diagnosis",
        context=_context(status="model_unknown", model=None),
    )

    assert decision.status == "needs_information"
    assert decision.rule_ids == ("MODEL_REQUIRED",)
    assert "inspection_steps" in decision.blocked_fields


def test_safety_gate_blocks_a_request_to_bypass_a_machine_interlock() -> None:
    decision = SafetyPolicyGate().evaluate(
        DiagnosisRequest(question="旁路防护门联锁后继续运行", pack_id="cnc_pack_v1.0.0", model="VF-2"),
        intent="fault_diagnosis",
        context=_context(),
    )

    assert decision.status == "blocked"
    assert decision.rule_ids == ("SAFETY_INTERLOCK_BYPASS",)


def test_safety_gate_escalates_pump_disassembly_without_energy_isolation() -> None:
    decision = SafetyPolicyGate().evaluate(
        DiagnosisRequest(
            question="不做能源隔离，直接拆开真空泵检查即可吗？",
            pack_id="dry_vacuum_pump_pack_v1.0.0",
            model="nXDS15i",
        ),
        intent="fault_diagnosis",
        context=ResolvedEquipmentContext(
            status="compatible",
            pack_id="dry_vacuum_pump_pack_v1.0.0",
            equipment_type="dry_scroll_vacuum_pump",
            manufacturer="Edwards",
            model="nXDS15i",
            controller="not_applicable",
            document_revision=None,
        ),
    )

    assert decision.status == "escalate"
    assert decision.rule_ids == ("ENERGY_ISOLATION_REQUIRED", "VACUUM_RELEASE_REQUIRED")
    assert "inspection_steps" in decision.blocked_fields


def test_evidence_gap_detector_removes_steps_without_both_maintenance_and_safety_evidence() -> None:
    decision = EvidenceGapDetector().evaluate(
        "fault_diagnosis",
        (_evidence("failure_modes", "failure-1"), _evidence("maintenance_tasks", "maintenance-1")),
    )

    assert decision.status == "insufficient_evidence"
    assert decision.allowed_fields == ("candidate_causes",)
    assert decision.missing_evidence_types == ("safety_rules",)


def test_evidence_gap_detector_allows_causes_and_steps_only_when_required_evidence_exists() -> None:
    decision = EvidenceGapDetector().evaluate(
        "fault_diagnosis",
        (
            _evidence("symptoms", "symptom-1"),
            _evidence("failure_modes", "failure-1"),
            _evidence("maintenance_tasks", "maintenance-1"),
            _evidence("safety_rules", "safety-1"),
        ),
    )

    assert decision.status == "sufficient"
    assert decision.allowed_fields == ("candidate_causes", "inspection_steps")
    assert decision.missing_evidence_types == ()
