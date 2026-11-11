from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.workflow import DiagnosisWorkflow


@pytest.fixture()
def workflow() -> DiagnosisWorkflow:
    return DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path("config/equipment_pack_registry_v1.json"),
        retrieve=lambda request, context, route: (),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=None, model="deepseek-flash", timeout_seconds=1, max_tokens=100
        ),
    )


@pytest.mark.parametrize(
    "case",
    [
        json.loads(line)
        for line in (Path(__file__).parents[2] / "data/evaluation/guardrail_eval_v1.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ],
    ids=lambda case: str(case["eval_id"]),
)
def test_frozen_guardrail_cases_keep_their_declared_outcomes(workflow: DiagnosisWorkflow, case: dict[str, object]) -> None:
    result = workflow.invoke(
        {
            "request_id": f"guardrail-{case['eval_id']}",
            "question": case["prompt"],
            "pack_id": case["expected_pack_id"],
            "model": "VF-2" if case["expected_pack_id"] == "cnc_pack_v1.0.0" else "nXDS15i",
        }
    )

    expected_status = {
        "refuse": "blocked",
        "escalate": "blocked",
        "insufficient_evidence": "insufficient_evidence",
    }[str(case["expected_outcome"])]
    assert result.status == expected_status
