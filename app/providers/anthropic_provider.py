import httpx

from .base import ProviderResponse


class AnthropicProvider:
    async def generate(self, prompt: str, model: str, api_key: str) -> ProviderResponse:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        content = "".join(block["text"] for block in data["content"])
        return ProviderResponse(content=content)
