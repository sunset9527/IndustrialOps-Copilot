from __future__ import annotations

import httpx

from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.schemas import Citation


def _citation() -> Citation:
    return Citation(
        evidence_id="evidence-1",
        pack_id="cnc_pack_v1.0.0",
        source_id="HAAS-TEST",
        document_revision="2025",
        page_number=3,
        evidence_locator="HAAS-TEST:p.3",
    )


def test_deepseek_generator_returns_only_fields_with_approved_evidence_ids() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": '{"confirmed_facts": [{"text": "Alarm is active", "evidence_ids": ["evidence-1"]}], "candidate_causes": [], "inspection_steps": []}'
                        },
                    }
                ]
            },
        )
    )
    generator = DeepSeekAnswerGenerator.from_settings(
        api_key="test-key",
        model="deepseek-flash",
        timeout_seconds=2,
        max_tokens=100,
        transport=transport,
    )

    result = generator.generate(
        question="What does alarm mean?",
        approved_evidence={"evidence-1": "Alarm evidence"},
        citations={"evidence-1": _citation()},
        allowed_fields=("confirmed_facts",),
    )

    assert result.provider == "deepseek"
    assert result.fallback_reason is None
    assert result.items["confirmed_facts"] == (("Alarm is active", ("evidence-1",)),)


def test_deepseek_generator_rejects_an_unapproved_evidence_id_without_exposing_model_output() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": '{"confirmed_facts": [{"text": "Invented", "evidence_ids": ["unknown"]}]}'
                        },
                    }
                ]
            },
        )
    )
    generator = DeepSeekAnswerGenerator.from_settings(
        api_key="test-key", model="deepseek-flash", timeout_seconds=2, max_tokens=100, transport=transport
    )

    result = generator.generate(
        question="question",
        approved_evidence={"evidence-1": "Evidence"},
        citations={"evidence-1": _citation()},
        allowed_fields=("confirmed_facts",),
    )

    assert result.provider == "evidence_fallback"
    assert result.fallback_reason == "LLM_EVIDENCE_ID_INVALID"
    assert result.items["confirmed_facts"] == (("Evidence", ("evidence-1",)),)


def test_deepseek_generator_uses_evidence_fallback_when_api_key_is_absent() -> None:
    generator = DeepSeekAnswerGenerator.from_settings(
        api_key=None, model="deepseek-flash", timeout_seconds=2, max_tokens=100
    )

    result = generator.generate(
        question="question",
        approved_evidence={"evidence-1": "Evidence"},
        citations={"evidence-1": _citation()},
        allowed_fields=("confirmed_facts",),
    )

    assert result.provider == "evidence_fallback"
    assert result.fallback_reason == "DEEPSEEK_API_KEY_MISSING"


def test_deepseek_generator_falls_back_when_model_returns_no_evidence_bound_content() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]},
        )
    )
    generator = DeepSeekAnswerGenerator.from_settings(
        api_key="test-key", model="deepseek-flash", timeout_seconds=2, max_tokens=100, transport=transport
    )

    result = generator.generate(
        question="question",
        approved_evidence={"evidence-1": "Evidence"},
        citations={"evidence-1": _citation()},
        allowed_fields=("candidate_causes",),
    )

    assert result.provider == "evidence_fallback"
    assert result.fallback_reason == "LLM_OUTPUT_EMPTY"
    assert result.items["candidate_causes"] == (("Evidence", ("evidence-1",)),)
