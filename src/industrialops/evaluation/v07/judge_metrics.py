"""Explicit Ragas and DeepEval faithfulness scorers for v0.7 Judge runs."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from industrialops.evaluation.v07.judge_runner import JudgeObservation


def score_ragas_faithfulness(
    observation: JudgeObservation,
    *,
    llm: object,
    metric_factory: Callable[[object], object] | None = None,
    sample_factory: Callable[..., object] | None = None,
) -> float:
    """Score one completed system answer with an explicitly injected Ragas LLM."""

    if metric_factory is None:
        from ragas.metrics import Faithfulness

        metric_factory = lambda model: Faithfulness(llm=model)
    if sample_factory is None:
        from ragas import SingleTurnSample

        sample_factory = SingleTurnSample
    metric = metric_factory(llm)
    sample = sample_factory(
        user_input=observation.question,
        response=observation.answer,
        retrieved_contexts=list(observation.retrieved_contexts),
    )
    result = asyncio.run(metric.single_turn_ascore(sample))
    return float(result.value if hasattr(result, "value") else result)


def score_deepeval_faithfulness(
    observation: JudgeObservation,
    *,
    model: object,
    metric_factory: Callable[[object], object] | None = None,
    case_factory: Callable[..., object] | None = None,
) -> float:
    """Score the same answer and contexts with an explicit DeepEval model."""

    if metric_factory is None:
        from deepeval.metrics import FaithfulnessMetric

        metric_factory = lambda judge: FaithfulnessMetric(
            model=judge,
            async_mode=False,
            include_reason=True,
        )
    if case_factory is None:
        from deepeval.test_case import LLMTestCase

        case_factory = LLMTestCase
    case = case_factory(
        input=observation.question,
        actual_output=observation.answer,
        retrieval_context=list(observation.retrieved_contexts),
    )
    metric = metric_factory(model)
    return float(metric.measure(case, _show_indicator=False))
