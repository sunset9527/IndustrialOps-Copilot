"""Narrow DeepSeek adapter with local evidence-bound output validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json

import httpx

from industrialops.diagnosis.schemas import Citation


@dataclass(frozen=True)
class GeneratedAnswer:
    provider: str
    model: str | None
    fallback_reason: str | None
    items: dict[str, tuple[tuple[str, tuple[str, ...]], ...]]


class DeepSeekAnswerGenerator:
    """Call DeepSeek only after deterministic policy and evidence checks complete."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
        base_url: str = "https://api.deepseek.com",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    @classmethod
    def from_settings(
        cls,
        *,
        api_key: str | None,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
        base_url: str = "https://api.deepseek.com",
        transport: httpx.BaseTransport | None = None,
    ) -> "DeepSeekAnswerGenerator":
        return cls(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_tokens=max_tokens,
            base_url=base_url,
            transport=transport,
        )

    def generate(
        self,
        *,
        question: str,
        approved_evidence: Mapping[str, str],
        citations: Mapping[str, Citation],
        allowed_fields: Sequence[str],
    ) -> GeneratedAnswer:
        if not self._api_key:
            return self._fallback(approved_evidence, allowed_fields, "DEEPSEEK_API_KEY_MISSING")
        response = self._request(question, approved_evidence, allowed_fields)
        if isinstance(response, str):
            return self._fallback(approved_evidence, allowed_fields, response)
        try:
            parsed = self._validate_output(
                response,
                approved_evidence=approved_evidence,
                citations=citations,
                allowed_fields=allowed_fields,
            )
        except ValueError as error:
            return self._fallback(approved_evidence, allowed_fields, str(error))
        return GeneratedAnswer("deepseek", self._model, None, parsed)

    def _request(
        self,
        question: str,
        approved_evidence: Mapping[str, str],
        allowed_fields: Sequence[str],
    ) -> dict[str, object] | str:
        payload = {
            "model": self._model,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "max_tokens": self._max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return JSON only. For each allowed field, return a list of objects with "
                        "text and evidence_ids. Never use evidence IDs outside approved_evidence. "
                        f"Allowed fields: {list(allowed_fields)}."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"question": question, "approved_evidence": dict(approved_evidence)},
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        for attempt in range(2):
            try:
                with httpx.Client(
                    base_url=self._base_url,
                    timeout=self._timeout_seconds,
                    transport=self._transport,
                ) as client:
                    response = client.post("/chat/completions", headers=headers, json=payload)
            except httpx.HTTPError:
                if attempt == 0:
                    continue
                return "DEEPSEEK_UNAVAILABLE"
            if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                continue
            if response.status_code >= 400:
                return "DEEPSEEK_REQUEST_REJECTED"
            try:
                body = response.json()
                choice = body["choices"][0]
                if choice.get("finish_reason") != "stop":
                    return "LLM_OUTPUT_INCOMPLETE"
                content = choice["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    return "LLM_OUTPUT_EMPTY"
                parsed = json.loads(content)
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
                return "LLM_OUTPUT_INVALID_JSON"
            return parsed if isinstance(parsed, dict) else "LLM_OUTPUT_INVALID_JSON"
        return "DEEPSEEK_UNAVAILABLE"

    @staticmethod
    def _validate_output(
        output: Mapping[str, object],
        *,
        approved_evidence: Mapping[str, str],
        citations: Mapping[str, Citation],
        allowed_fields: Sequence[str],
    ) -> dict[str, tuple[tuple[str, tuple[str, ...]], ...]]:
        allowed = set(allowed_fields)
        validated: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {}
        for field, raw_items in output.items():
            if field not in allowed:
                if raw_items:
                    raise ValueError("LLM_OUTPUT_FIELD_NOT_ALLOWED")
                continue
            if not isinstance(raw_items, list):
                raise ValueError("LLM_OUTPUT_SCHEMA_INVALID")
            items: list[tuple[str, tuple[str, ...]]] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    raise ValueError("LLM_OUTPUT_SCHEMA_INVALID")
                text = item.get("text")
                evidence_ids = item.get("evidence_ids")
                if not isinstance(text, str) or not text.strip() or not isinstance(evidence_ids, list) or not evidence_ids:
                    raise ValueError("LLM_OUTPUT_SCHEMA_INVALID")
                ids = tuple(evidence_ids)
                if not all(isinstance(item_id, str) and item_id in approved_evidence and item_id in citations for item_id in ids):
                    raise ValueError("LLM_EVIDENCE_ID_INVALID")
                items.append((text, ids))
            validated[field] = tuple(items)
        if not any(validated.values()):
            raise ValueError("LLM_OUTPUT_EMPTY")
        return validated

    def _fallback(
        self,
        approved_evidence: Mapping[str, str],
        allowed_fields: Sequence[str],
        reason: str,
    ) -> GeneratedAnswer:
        evidence_items = tuple((text, (evidence_id,)) for evidence_id, text in approved_evidence.items())
        return GeneratedAnswer(
            "evidence_fallback",
            None,
            reason,
            {field: evidence_items for field in allowed_fields},
        )
