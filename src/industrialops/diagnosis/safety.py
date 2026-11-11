"""Deterministic rules that constrain all diagnosis output."""

from __future__ import annotations

from dataclasses import dataclass

from industrialops.diagnosis.context import ResolvedEquipmentContext
from industrialops.diagnosis.schemas import DiagnosisRequest


@dataclass(frozen=True)
class SafetyDecision:
    status: str
    rule_ids: tuple[str, ...] = ()
    blocked_fields: tuple[str, ...] = ()


class SafetyPolicyGate:
    """Apply non-bypassable safety and scope rules before answer generation."""

    def evaluate(
        self,
        request: DiagnosisRequest,
        *,
        intent: str,
        context: ResolvedEquipmentContext,
    ) -> SafetyDecision:
        text = request.question.casefold()
        if context.status == "model_out_of_scope":
            return SafetyDecision("blocked", ("MODEL_OR_VARIANT_OUT_OF_SCOPE",), ("candidate_causes", "inspection_steps"))
        if any(marker in text for marker in ("smtc", "双臂换刀", "nxds15ir", "nxdsi r", "c/r")):
            return SafetyDecision("blocked", ("MODEL_OR_VARIANT_OUT_OF_SCOPE",), ("candidate_causes", "inspection_steps"))
        if intent == "fault_diagnosis" and context.status == "model_unknown":
            return SafetyDecision("needs_information", ("MODEL_REQUIRED",), ("inspection_steps",))
        if any(marker in text for marker in ("旁路", "bypass")) and any(
            marker in text for marker in ("联锁", "防护门", "interlock", "guard")
        ):
            return SafetyDecision("blocked", ("SAFETY_INTERLOCK_BYPASS",), ("candidate_causes", "inspection_steps"))

        rule_ids: list[str] = []
        if any(marker in text for marker in ("不做能源隔离", "未断电", "不挂牌", "without isolation", "no lockout")):
            rule_ids.append("ENERGY_ISOLATION_REQUIRED")
        if context.equipment_type == "dry_scroll_vacuum_pump" and any(
            marker in text for marker in ("拆开", "拆卸", "disassemble", "remove")
        ):
            rule_ids.append("VACUUM_RELEASE_REQUIRED")
        if rule_ids:
            return SafetyDecision("escalate", tuple(rule_ids), ("inspection_steps",))
        if any(marker in text for marker in ("有毒", "易燃", "腐蚀", "高压", "高温", "toxic", "flammable", "corrosive", "high pressure")):
            return SafetyDecision("escalate", ("HAZARDOUS_MEDIA_ESCALATION",), ("inspection_steps",))
        if any(marker in text for marker in ("修改参数", "控制参数", "parameter change", "change parameter")):
            return SafetyDecision("escalate", ("CONTROL_PARAMETER_CHANGE",), ("inspection_steps",))
        if "edwards" in text and context.pack_id == "cnc_pack_v1.0.0" or "haas" in text and context.pack_id == "dry_vacuum_pump_pack_v1.0.0":
            return SafetyDecision("blocked", ("CROSS_PACK_EVIDENCE",), ("candidate_causes", "inspection_steps"))
        return SafetyDecision("allow")
