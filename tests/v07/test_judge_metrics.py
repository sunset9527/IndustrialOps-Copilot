from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from industrialops.evaluation.v07.deepseek_ragas import create_deepseek_ragas_llm
from industrialops.evaluation.v07.deepseek_deepeval import create_deepseek_deepeval_model
from industrialops.evaluation.v07.judge_runner import JudgeObservation


def _observation() -> JudgeObservation:
    return JudgeObservation(
        question="如何检查冷却液液位？",
        status="answered",
        intent="manual_query",
        answer="请检查冷却液液位。",
        retrieved_contexts=("冷却液液位应在允许范围内。",),
        reference_contexts=("人工审核参考证据。",),
        citation_count=1,
        answer_provider="evidence_fallback",
    )


def test_ragas_faithfulness_receives_the_system_answer_and_retrieved_contexts() -> None:
    judge_metrics = importlib.import_module("industrialops.evaluation.v07.judge_metrics")
    captured: dict[str, object] = {}

    class Result:
        value = 0.75

    class Metric:
        async def single_turn_ascore(self, sample):
            captured.update(vars(sample))
            return Result()

    score = judge_metrics.score_ragas_faithfulness(
        _observation(),
        llm=object(),
        metric_factory=lambda llm: Metric(),
        sample_factory=lambda **kwargs: SimpleNamespace(**kwargs),
    )

    assert score == 0.75
    assert captured == {
        "user_input": "如何检查冷却液液位？",
        "response": "请检查冷却液液位。",
        "retrieved_contexts": ["冷却液液位应在允许范围内。"],
    }


def test_deepeval_faithfulness_receives_the_same_answer_and_contexts() -> None:
    judge_metrics = importlib.import_module("industrialops.evaluation.v07.judge_metrics")
    captured: dict[str, object] = {}

    class Metric:
        score = 0.625

        def measure(self, case, _show_indicator=False):
            captured["input"] = case.input
            captured["actual_output"] = case.actual_output
            captured["retrieval_context"] = case.retrieval_context
            return self.score

    score = judge_metrics.score_deepeval_faithfulness(
        _observation(),
        model=object(),
        metric_factory=lambda model: Metric(),
        case_factory=lambda **kwargs: SimpleNamespace(**kwargs),
    )

    assert score == 0.625
    assert captured == {
        "input": "如何检查冷却液液位？",
        "actual_output": "请检查冷却液液位。",
        "retrieval_context": ["冷却液液位应在允许范围内。"],
    }


def test_ragas_044_faithfulness_accepts_the_custom_deepseek_adapter() -> None:
    pytest.importorskip("ragas")
    judge_metrics = importlib.import_module("industrialops.evaluation.v07.judge_metrics")
    responses = [
        '{"statements": ["请检查冷却液液位。"]}',
        '{"statements": [{"statement": "请检查冷却液液位。", "reason": "证据直接支持。", "verdict": 1}]}',
    ]

    class Response:
        def __init__(self, content: str) -> None:
            self._content = content

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "choices": [
                    {"message": {"content": self._content}, "finish_reason": "stop"}
                ]
            }

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            return Response(responses.pop(0))

    llm = create_deepseek_ragas_llm(
        base_url="https://judge.example.test/v1",
        api_key="private-key",
        model="deepseek-chat",
        client_factory=Client,
    )

    score = judge_metrics.score_ragas_faithfulness(_observation(), llm=llm)

    assert score == 1.0
    assert responses == []


def test_deepeval_434_faithfulness_accepts_the_custom_deepseek_model() -> None:
    pytest.importorskip("deepeval")
    judge_metrics = importlib.import_module("industrialops.evaluation.v07.judge_metrics")
    responses = [
        '{"truths": ["冷却液液位应在允许范围内。"]}',
        '{"claims": ["请检查冷却液液位。"]}',
        '{"verdicts": [{"verdict": "yes", "reason": "证据直接支持。"}]}',
        '{"reason": "回答由检索证据支持。"}',
    ]

    class Response:
        def __init__(self, content: str) -> None:
            self._content = content

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": [{"message": {"content": self._content}}]}

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, *, headers, json):
            return Response(responses.pop(0))

    model = create_deepseek_deepeval_model(
        base_url="https://judge.example.test/v1",
        api_key="private-key",
        model="deepseek-chat",
        client_factory=Client,
    )

    score = judge_metrics.score_deepeval_faithfulness(
        _observation(),
        model=model,
    )

    assert score == 1.0
    assert responses == []
