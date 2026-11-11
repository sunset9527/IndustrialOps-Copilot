from __future__ import annotations

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.intent import IntentRouter
from industrialops.diagnosis.schemas import DiagnosisRequest


def test_intent_router_prioritizes_an_explicit_alarm_code() -> None:
    route = IntentRouter().route(
        DiagnosisRequest(question="VF-2 报警 552，冷却液泵也有异响", pack_id="cnc_pack_v1.0.0")
    )

    assert route.intent == "alarm_lookup"
    assert route.rule_id == "EXPLICIT_ALARM_CODE"
    assert route.alarm_code == "552"


def test_context_resolver_normalizes_a_declared_model_alias_without_guessing_missing_model() -> None:
    resolver = EquipmentContextResolver.from_registry_path(
        "config/equipment_pack_registry_v1.json"
    )

    resolved = resolver.resolve(
        DiagnosisRequest(
            question="请给出检查步骤",
            pack_id="cnc_pack_v1.0.0",
            model="vf 2",
            controller="ngc",
        )
    )
    unknown_model = resolver.resolve(
        DiagnosisRequest(question="请给出检查步骤", pack_id="cnc_pack_v1.0.0")
    )

    assert resolved.status == "compatible"
    assert resolved.model == "VF-2"
    assert resolved.controller == "NGC"
    assert unknown_model.status == "model_unknown"
    assert unknown_model.model is None


def test_context_resolver_rejects_out_of_scope_variant_instead_of_mapping_it_to_standard_model() -> None:
    resolver = EquipmentContextResolver.from_registry_path(
        "config/equipment_pack_registry_v1.json"
    )

    resolved = resolver.resolve(
        DiagnosisRequest(
            question="请确认 nXDS15iR 的专用维修方法",
            pack_id="dry_vacuum_pump_pack_v1.0.0",
            model="nXDS15iR",
        )
    )

    assert resolved.status == "model_out_of_scope"
    assert resolved.model is None
    assert resolved.reason_code == "MODEL_OR_VARIANT_OUT_OF_SCOPE"
