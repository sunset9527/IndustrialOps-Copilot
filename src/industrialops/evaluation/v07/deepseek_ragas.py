"""Direct DeepSeek JSON adapter for Ragas structured metrics."""
from __future__ import annotations

from collections.abc import Callable
import asyncio

import httpx


def parse_structured_response(*, content: str, response_model: object):
    """Parse a non-thinking DeepSeek JSON completion into Ragas' schema."""
    return response_model.model_validate_json(content)


def create_deepseek_ragas_llm(
    *,
    base_url: str,
    api_key: str,
    model: str,
    client_factory: Callable[[], object] | None = None,
):
    """Create a Ragas LLM that never falls back to a framework provider."""

    from langchain_core.outputs import Generation, LLMResult
    from ragas.llms import BaseRagasLLM

    class DeepSeekRagasLLM(BaseRagasLLM):
        def generate_text(self, prompt, n=1, temperature=0.01, stop=None, callbacks=None):
            return asyncio.run(
                self.agenerate_text(
                    prompt,
                    n=n,
                    temperature=temperature,
                    stop=stop,
                    callbacks=callbacks,
                )
            )

        async def agenerate_text(self, prompt, n=1, temperature=0.01, stop=None, callbacks=None):
            generations = []
            for _ in range(n):
                content, finish_reason = await _request_json_completion(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    prompt=prompt.to_string(),
                    client_factory=client_factory,
                )
                generations.append(
                    Generation(text=content, generation_info={"finish_reason": finish_reason})
                )
            return LLMResult(generations=[generations])

        def is_finished(self, response) -> bool:
            return all(
                generation.generation_info is None
                or generation.generation_info.get("finish_reason") in {"stop", "STOP"}
                for group in response.generations
                for generation in group
            )

    return DeepSeekRagasLLM()


async def request_non_thinking_json(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    response_model: object,
    client_factory: Callable[[], object] | None = None,
):
    content, _ = await _request_json_completion(
        base_url=base_url,
        api_key=api_key,
        model=model,
        prompt=prompt,
        client_factory=client_factory,
    )
    return parse_structured_response(content=content, response_model=response_model)


async def _request_json_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    client_factory: Callable[[], object] | None,
) -> tuple[str, str | None]:
    factory = client_factory or (lambda: httpx.AsyncClient(timeout=90.0))
    async with factory() as client:
        response = await client.post(
            base_url.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
                "temperature": 0,
                "max_tokens": 8192,
                "stream": False,
            },
        )
    response.raise_for_status()
    choice = response.json()["choices"][0]
    return choice["message"]["content"], choice.get("finish_reason")
