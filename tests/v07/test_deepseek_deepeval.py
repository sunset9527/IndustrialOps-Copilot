from __future__ import annotations

import importlib

import pytest


def test_deepeval_model_uses_explicit_json_mode_and_disables_thinking() -> None:
    pytest.importorskip("deepeval")
    module = importlib.import_module("industrialops.evaluation.v07.deepseek_deepeval")
    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "choices": [
                    {"message": {"content": '{"verdicts": []}'}, "finish_reason": "stop"}
                ]
            }

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, *, headers, json):
            captured["url"] = url
            captured["authorization"] = headers["Authorization"]
            captured["payload"] = json
            return Response()

    class Schema:
        @classmethod
        def model_validate_json(cls, content):
            return {"validated": content}

    model = module.create_deepseek_deepeval_model(
        base_url="https://judge.example.test/v1",
        api_key="private-key",
        model="deepseek-chat",
        client_factory=Client,
    )
    result = model.generate("Return JSON.", schema=Schema)

    assert result == {"validated": '{"verdicts": []}'}
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
