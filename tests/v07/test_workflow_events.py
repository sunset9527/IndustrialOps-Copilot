from __future__ import annotations

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.workflow import DiagnosisWorkflow


def _workflow() -> DiagnosisWorkflow:
    return DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path("config/equipment_pack_registry_v1.json"),
        retrieve=lambda request, context, route: (),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=None, model="deepseek-flash", timeout_seconds=1, max_tokens=100
        ),
    )


def test_work_order_request_has_a_current_next_action_and_observable_events() -> None:
    result = _workflow().invoke(
        {
            "request_id": "v07-work-order-001",
            "question": "请创建工单草稿",
            "pack_id": "cnc_pack_v1.0.0",
            "model": "VF-2",
            "controller": "NGC",
        }
    )

    assert result.intent == "work_order_draft"
    assert result.recommended_next_action == "create_work_order_draft_from_diagnosis"
    assert "当前版本未开放" not in " ".join(result.uncertainties)
    assert tuple(event.node for event in result.workflow_events) == ("intent_router", "answer_composer")
    assert result.workflow_events[-1].status == "needs_information"
    assert result.workflow_events[-1].duration_ms >= 0
