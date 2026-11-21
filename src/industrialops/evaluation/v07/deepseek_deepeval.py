"""Explicit non-thinking DeepSeek model for DeepEval metrics."""

from __future__ import annotations

from collections.abc import Callable

import httpx


def create_deepseek_deepeval_model(
    *,
    base_url: str,
    api_key: str,
    model: str,
    client_factory: Callable[[], object] | None = None,
):
    """Create a DeepEval model bound only to the configured Judge endpoint."""

    from deepeval.models import DeepEvalBaseLLM

    class DeepSeekDeepEvalModel(DeepEvalBaseLLM):
        def load_model(self, *args, **kwargs):
            return self

        def get_model_name(self, *args, **kwargs) -> str:
            return model

        def supports_structured_outputs(self) -> bool:
            return True

        def supports_json_mode(self) -> bool:
            return True

        def generate(self, prompt: str, schema=None, *args, **kwargs):
            factory = client_factory or (lambda: httpx.Client(timeout=90.0))
            payload: dict[str, object] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "thinking": {"type": "disabled"},
                "temperature": 0,
                "max_tokens": 8192,
                "stream": False,
            }
            if schema is not None:
                payload["response_format"] = {"type": "json_object"}
            with factory() as client:
                response = client.post(
                    base_url.rstrip("/") + "/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return schema.model_validate_json(content) if schema is not None else content

        async def a_generate(self, prompt: str, schema=None, *args, **kwargs):
            return self.generate(prompt, schema=schema, *args, **kwargs)

    return DeepSeekDeepEvalModel(model)
