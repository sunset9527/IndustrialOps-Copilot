"""Minimal, data-free connectivity check for an explicitly configured Judge."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class JudgeConnectionResult:
    status: str
    response_present: bool


def verify_judge_connection(
    *,
    base_url: str,
    api_key: str,
    model: str,
    client: httpx.Client,
) -> JudgeConnectionResult:
    """Confirm an OpenAI-compatible endpoint returns a non-empty completion.

    The result deliberately excludes endpoint, model output, and credentials so
    it can be logged without exposing private configuration or model content.
    """

    response = client.post(
        base_url.rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: JUDGE_CONNECTION_OK"}],
            "temperature": 0,
            "thinking": {"type": "disabled"},
            "max_tokens": 64,
            "stream": False,
        },
    )
    response.raise_for_status()
    body = response.json()
    choices = body.get("choices") if isinstance(body, dict) else None
    if not isinstance(choices, list) or not choices:
        raise ValueError("EVALUATION_JUDGE_CONNECTION_RESPONSE_INVALID")
    first = choices[0]
    message = first.get("message") if isinstance(first, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("EVALUATION_JUDGE_CONNECTION_RESPONSE_INVALID")
    return JudgeConnectionResult(status="passed", response_present=True)
