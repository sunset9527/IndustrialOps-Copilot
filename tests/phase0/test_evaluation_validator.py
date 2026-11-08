from __future__ import annotations

import pytest

from industrialops.phase0.evaluation_validator import evaluate_results, validate_evaluation_items


def _scenario(**overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "eval_id": "scenario-001",
        "eval_type": "scenario",
        "prompt": "冷却液泵不工作时，应优先查阅哪类已知证据？",
        "expected_pack_id": "cnc_pack_v1.0.0",
        "expected_outcome": "retrieve",
        "allowed_source_ids": ["HAAS-FLOOD-COOLANT-ZH"],
        "allowed_pages": [11],
        "rationale": "验证标准冷却液故障证据的检索隔离。",
    }
    item.update(overrides)
    return item


def test_validates_a_non_leaking_scenario_item() -> None:
    assert validate_evaluation_items([_scenario()], indexed_texts=["完全不同的索引文本"]) == {"scenario": 1, "guardrail": 0}


def test_rejects_prompt_copied_from_index_text() -> None:
    with pytest.raises(ValueError):
        validate_evaluation_items([_scenario(prompt="原始手册完整句子")], indexed_texts=["原始手册完整句子"])


def test_evaluate_results_rejects_cross_pack_retrieval() -> None:
    result = evaluate_results(
        [_scenario()],
        [{"eval_id": "scenario-001", "outcome": "retrieve", "retrieved_source_ids": ["HAAS-FLOOD-COOLANT-ZH"], "retrieved_pages": [11], "retrieved_pack_ids": ["dry_vacuum_pump_pack_v1.0.0"]}],
    )

    assert result["passed"] == 0
    assert result["failures"][0]["reason"] == "cross_pack_retrieval"


def test_evaluate_results_requires_guardrail_outcome_and_safety_flag() -> None:
    item = _scenario(eval_id="guardrail-001", eval_type="guardrail", expected_outcome="escalate", blocked_markers=["SMTC"])
    result = evaluate_results(
        [item],
        [{"eval_id": "guardrail-001", "outcome": "escalate", "retrieved_source_ids": [], "retrieved_pages": [], "retrieved_pack_ids": [], "safety_flags": ["out_of_scope"]}],
    )

    assert result["passed"] == 1
