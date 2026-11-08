from __future__ import annotations

import asyncio
import json

from industrialops.middleware.request_size import RequestBodyLimitMiddleware


async def _call_middleware(messages: list[dict], *, headers: list[tuple[bytes, bytes]] | None = None, limit: int = 10):
    received: list[dict] = []
    sent: list[dict] = []

    async def downstream(scope, receive, send) -> None:
        while True:
            message = await receive()
            received.append(message)
            if not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    queue = list(messages)

    async def receive() -> dict:
        return queue.pop(0)

    async def send(message: dict) -> None:
        sent.append(message)

    middleware = RequestBodyLimitMiddleware(downstream, max_bytes=limit)
    await middleware(
        {"type": "http", "method": "POST", "path": "/uploads", "headers": headers or []},
        receive,
        send,
    )
    return received, sent


def test_content_length_over_limit_is_rejected_before_downstream_receives_body() -> None:
    received, sent = asyncio.run(
        _call_middleware(
            [{"type": "http.request", "body": b"unused", "more_body": False}],
            headers=[(b"content-length", b"11")],
        )
    )

    assert received == []
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"]) == {
        "error": {"code": "request_too_large", "message": "Request body exceeds the server limit"}
    }


def test_chunked_body_is_rejected_when_its_cumulative_size_crosses_the_limit() -> None:
    received, sent = asyncio.run(
        _call_middleware(
            [
                {"type": "http.request", "body": b"123456", "more_body": True},
                {"type": "http.request", "body": b"78901", "more_body": False},
            ]
        )
    )

    assert len(received) == 1
    assert sent[0]["status"] == 413


def test_body_at_the_limit_reaches_downstream() -> None:
    received, sent = asyncio.run(
        _call_middleware(
            [
                {"type": "http.request", "body": b"12345", "more_body": True},
                {"type": "http.request", "body": b"67890", "more_body": False},
            ]
        )
    )

    assert len(received) == 2
    assert sent[0]["status"] == 204
