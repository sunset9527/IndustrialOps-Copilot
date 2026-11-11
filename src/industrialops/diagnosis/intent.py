"""Deterministic routing for industrial diagnosis requests."""

from __future__ import annotations

from dataclasses import dataclass
import re

from industrialops.diagnosis.schemas import DiagnosisRequest
from industrialops.retrieval.industrial import normalize_alarm_code


@dataclass(frozen=True)
class IntentRoute:
    intent: str
    rule_id: str
    alarm_code: str | None = None


class IntentRouter:
    """Classify requests without delegating safety-critical decisions to an LLM."""

    _alarm_pattern = re.compile(r"(?i)(?:alarm|报警)\s*([A-Z]*\s*\d+(?:[.\-]\d+)?)")

    def route(self, request: DiagnosisRequest) -> IntentRoute:
        if match := self._alarm_pattern.search(request.question):
            return IntentRoute("alarm_lookup", "EXPLICIT_ALARM_CODE", normalize_alarm_code(match.group(1)))
        text = request.question.casefold()
        if any(marker in text for marker in ("工单", "work order")):
            return IntentRoute("work_order_draft", "WORK_ORDER_REQUEST")
        if any(marker in text for marker in ("保养", "维护周期", "maintenance schedule")):
            return IntentRoute("maintenance_plan", "MAINTENANCE_REQUEST")
        if any(marker in text for marker in ("故障", "异常", "异响", "诊断", "检查步骤", "维修", "旁路", "联锁", "拆开", "拆卸")):
            return IntentRoute("fault_diagnosis", "DIAGNOSIS_REQUEST")
        if any(marker in text for marker in ("手册", "manual", "说明书")):
            return IntentRoute("manual_query", "MANUAL_REQUEST")
        return IntentRoute("out_of_scope", "UNCLASSIFIED_REQUEST")
