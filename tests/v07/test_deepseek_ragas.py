from __future__ import annotations

import asyncio

import pytest

from industrialops.evaluation.v07 import deepseek_ragas
from industrialops.evaluation.v07.deepseek_ragas import parse_structured_response
from industrialops.evaluation.v07.deepseek_ragas import request_non_thinking_json

class Schema:
    @classmethod
    def model_validate_json(cls, content):
        return {"validated": content}

def test_parses_deepseek_json_with_the_ragas_schema():
    assert parse_structured_response(content='{"ok":true}', response_model=Schema) == {"validated": '{"ok":true}'}


def test_structured_request_uses_explicit_deepseek_json_mode_with_thinking_disabled() -> None:
    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"statements": ["supported"]}'},
                    }
                ]
            }

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            captured["url"] = url
            captured["authorization"] = headers["Authorization"]
            captured["payload"] = json
            return Response()

    async def execute():
        return await request_non_thinking_json(
            base_url="https://judge.example.test/v1",
            api_key="private-key",
            model="deepseek-chat",
            prompt="Return JSON.",
            response_model=Schema,
            client_factory=Client,
        )

    result = asyncio.run(execute())

    assert result == {"validated": '{"statements": ["supported"]}'}
    assert captured["url"] == "https://judge.example.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer private-key"
    assert captured["payload"] == {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Return JSON."}],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 8192,
        "stream": False,
    }


def test_ragas_adapter_returns_a_real_llm_result_without_default_provider() -> None:
    pytest.importorskip("ragas")
    prompt_values = pytest.importorskip("langchain_core.prompt_values")

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"statements": ["supported"]}'},
                    }
                ]
            }

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            return Response()

    llm = deepseek_ragas.create_deepseek_ragas_llm(
        base_url="https://judge.example.test/v1",
        api_key="private-key",
        model="deepseek-chat",
        client_factory=Client,
    )
    result = asyncio.run(
        llm.agenerate_text(prompt_values.StringPromptValue(text="Return JSON."))
    )

    assert result.generations[0][0].text == '{"statements": ["supported"]}'
    assert llm.is_finished(result) is True
