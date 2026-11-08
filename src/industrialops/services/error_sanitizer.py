"""Helpers that prevent secrets and deployment details from reaching users."""

from __future__ import annotations

import re
from typing import Any


_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(?:mysql|postgres(?:ql)?|sqlite)(?:\+[\w-]+)?://[^\s'\";]+"), "[REDACTED_DATABASE_URL]"),
    (re.compile(r"(?i)(?:authorization\s*[:=]\s*)?bearer\s+[\w.\-~+/=]+"), "[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(?:x-api-key|api[_ -]?key|password|secret)\s*[:=]\s*[^\s;,]+"), "[REDACTED_SECRET]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]+\b"), "[REDACTED_SECRET]"),
    (re.compile(r"(?<![\w:])[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]*"), "[REDACTED_PATH]"),
)


def redact_sensitive_text(value: Any, *, max_length: int = 500) -> str:
    """Return a bounded diagnostic summary with common sensitive values removed."""

    result = str(value)
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result[:max_length]


def public_error(_exception: BaseException, *, request_id: str | None = None) -> dict[str, dict[str, str]]:
    """Return a stable user-facing failure envelope without inspecting exception text."""

    payload = {
        "code": "internal_error",
        "message": "Service could not process the request",
    }
    if request_id:
        payload["request_id"] = request_id
    return {"error": payload}
