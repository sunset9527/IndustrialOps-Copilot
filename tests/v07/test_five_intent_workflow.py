from __future__ import annotations

import pytest

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.knowledge.pack_loader import StructuredEvidence


def _evidence(kind: str) -> StructuredEvidence:
    return StructuredEvidence(
        evidence_id=f"e-{kind}", candidate_id=f"e-{kind}", candidate_type=kind,
        pack_id="cnc_pack_v1.0.0", label="coolant", source_id="HAAS-MAINTENANCE-ZH",
        source_file="manual.pdf", source_sha256="a" * 64, page_number=3,
        evidence_locator="HAAS-MAINTENANCE-ZH:p.3", evidence_text=f"{kind} reviewed evidence",
    )


@pytest.fixture()
def workflow() -> DiagnosisWorkflow:
    return DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path("config/equipment_pack_registry_v1.json"),
        retrieve=lambda request, context, route: tuple(_evidence(kind) for kind in ("alarms", "failure_modes", "maintenance_tasks", "safety_rules")),
        answer_generator=DeepSeekAnswerGenerator.from_settings(api_key=None, model="deepseek-flash", timeout_seconds=1, max_tokens=100),
    )


@pytest.mark.parametrize(
    ("question", "expected_intent", "expected_status"),
    [
        ("请查询 VF-2 冷却液手册。", "manual_query", "answered"),
        ("VF-2 报警 552 表示什么？", "alarm_lookup", "answered"),
        ("VF-2 的维护周期是什么？", "maintenance_plan", "answered"),
        ("VF-2 冷却液异常，给出检查步骤。", "fault_diagnosis", "answered"),
        ("为刚才的诊断创建工单。", "work_order_draft", "needs_information"),
    ],
)
def test_five_supported_intents_have_an_auditable_end_to_end_path(
    workflow: DiagnosisWorkflow, question: str, expected_intent: str, expected_status: str
) -> None:
    result = workflow.invoke({"request_id": f"v07-{expected_intent}", "question": question, "pack_id": "cnc_pack_v1.0.0", "model": "VF-2", "controller": "NGC"})

    assert result.intent == expected_intent
    assert result.status == expected_status
    assert result.workflow_events
    assert result.workflow_events[-1].node == "answer_composer"
