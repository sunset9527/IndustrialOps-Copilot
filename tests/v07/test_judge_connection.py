from __future__ import annotations

import httpx
import json

from industrialops.evaluation.v07.judge_connection import verify_judge_connection


def test_judge_connection_accepts_a_nonempty_model_reply_without_returning_its_text() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "JUDGE_CONNECTION_OK."}}]})

    result = verify_judge_connection(
        base_url="https://judge.example.test/v1",
        api_key="private-test-key",
        model="judge-model",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert result.status == "passed"
    assert result.response_present is True
    assert "private-test-key" not in repr(result)
    assert captured["authorization"] == "Bearer private-test-key"
    assert captured["payload"] == {
        "model": "judge-model",
        "messages": [{"role": "user", "content": "Reply with exactly: JUDGE_CONNECTION_OK"}],
        "temperature": 0,
        "max_tokens": 64,
        "stream": False,
    }
