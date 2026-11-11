from __future__ import annotations

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.knowledge.pack_loader import StructuredEvidence


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
        evidence_text=f"{candidate_type} evidence",
    )


def test_compiled_langgraph_workflow_uses_evidence_fallback_and_records_actual_nodes() -> None:
    workflow = DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path("config/equipment_pack_registry_v1.json"),
        retrieve=lambda request, context, route: (
            _evidence("symptoms", "symptom-1"),
            _evidence("failure_modes", "failure-1"),
            _evidence("maintenance_tasks", "maintenance-1"),
            _evidence("safety_rules", "safety-1"),
        ),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=None, model="deepseek-flash", timeout_seconds=1, max_tokens=100
        ),
    )

    result = workflow.invoke(
        {
            "request_id": "request-001",
            "question": "VF-2 主轴异常噪声，给出检查步骤",
            "pack_id": "cnc_pack_v1.0.0",
            "model": "VF-2",
            "controller": "NGC",
        }
    )

    assert result.status == "answered"
    assert result.generation["provider"] == "evidence_fallback"
    assert result.inspection_steps
    assert {citation.evidence_id for citation in result.citations} >= {"maintenance-1", "safety-1"}
    assert result.workflow_trace == (
        "intent_router",
        "equipment_context_resolver",
        "evidence_retriever",
        "compatibility_validator",
        "fault_diagnosis_service",
        "safety_policy_gate",
        "evidence_gap_detector",
        "answer_composer",
    )


def test_compiled_langgraph_workflow_blocks_before_answer_generation() -> None:
    workflow = DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path("config/equipment_pack_registry_v1.json"),
        retrieve=lambda request, context, route: (_evidence("failure_modes", "failure-1"),),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=None, model="deepseek-flash", timeout_seconds=1, max_tokens=100
        ),
    )

    result = workflow.invoke(
        {
            "request_id": "request-002",
            "question": "旁路防护门联锁后继续运行",
            "pack_id": "cnc_pack_v1.0.0",
            "model": "VF-2",
        }
    )

    assert result.status == "blocked"
    assert result.inspection_steps == ()
    assert result.generation["provider"] == "policy_gate"
    assert "answer_composer" in result.workflow_trace
