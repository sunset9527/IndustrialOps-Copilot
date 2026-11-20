"""Offline framework-object construction for the v0.7 evaluation adapters.

This module deliberately does not run LLM-as-a-judge metrics or export traces.
It verifies that reviewed IndustrialOps records can enter the real SDK data
models while preserving the deterministic hard gates as the safety authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def build_ragas_dataset(rows: Iterable[Mapping[str, object]]) -> Any:
    """Create a real Ragas dataset from reviewed single-turn rows.

    ``metadata`` is retained in IndustrialOps' report rather than passed to
    Ragas because Ragas' ``SingleTurnSample`` schema intentionally accepts
    only evaluation fields.
    """

    from ragas import EvaluationDataset, SingleTurnSample

    samples = [
        SingleTurnSample(
            user_input=_optional_text(row.get("user_input")),
            response=_optional_text(row.get("response")),
            retrieved_contexts=_text_list(row.get("retrieved_contexts")),
            reference_contexts=_text_list(row.get("reference_contexts")),
            reference=_optional_text(row.get("reference")),
        )
        for row in rows
    ]
    return EvaluationDataset(samples=samples, name="industrialops-v07-framework-smoke")


def build_deepeval_trace_case(*, scenario_id: str, spans: Iterable[Mapping[str, object]]) -> Any:
    """Create a real DeepEval test case with only redacted observable spans."""

    from deepeval.test_case import LLMTestCase

    return LLMTestCase(
        input="[redacted industrialops request]",
        actual_output="[redacted industrialops response]",
        name="industrialops-v07-framework-smoke",
        metadata={"scenario_id": scenario_id, "spans": list(spans)},
    )


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _text_list(value: object) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError("EVALUATION_FRAMEWORK_ROW_INVALID")
    return value
