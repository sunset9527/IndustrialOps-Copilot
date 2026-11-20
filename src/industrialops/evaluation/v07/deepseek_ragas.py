"""Direct DeepSeek JSON adapter for Ragas structured metrics."""
from __future__ import annotations
import httpx

def parse_structured_response(*, content: str, response_model: object):
    """Parse a non-thinking DeepSeek JSON completion into Ragas' schema."""
    return response_model.model_validate_json(content)

async def request_non_thinking_json(*, base_url: str, api_key: str, model: str, prompt: str, response_model: object):
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(base_url.rstrip('/') + '/chat/completions', headers={'Authorization': f'Bearer {api_key}'}, json={'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'thinking': {'type': 'disabled'}, 'response_format': {'type': 'json_object'}, 'temperature': 0, 'max_tokens': 8192})
    response.raise_for_status()
    return parse_structured_response(content=response.json()['choices'][0]['message']['content'], response_model=response_model)
