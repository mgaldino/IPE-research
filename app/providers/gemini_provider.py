import re

import httpx

from .base import ProviderResponse


class GeminiProvider:
    def _normalize_model(self, model: str) -> str:
        raw = (model or "").strip()
        if not raw:
            return model
        lowered = raw.lower()
        cleaned = re.sub(r"[^\w]+", "-", lowered).strip("-")
        cleaned = re.sub(r"-+", "-", cleaned)
        aliases = {
            "gemini-2-5-flash": "gemini-2.5-flash",
            "gemini-2-5-pro": "gemini-2.5-pro",
            "gemini-25-flash": "gemini-2.5-flash",
            "gemini-25-pro": "gemini-2.5-pro",
            "gemini-1-5-flash": "gemini-1.5-flash",
            "gemini-1-5-pro": "gemini-1.5-pro",
            "gemini-15-flash": "gemini-1.5-flash",
            "gemini-15-pro": "gemini-1.5-pro",
            "gemini-flash": "gemini-2.5-flash",
            "gemini-pro": "gemini-2.5-pro",
        }
        return aliases.get(cleaned, cleaned)

    async def generate(self, prompt: str, model: str, api_key: str) -> ProviderResponse:
        normalized = self._normalize_model(model)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{normalized}:generateContent"
        params = {"key": api_key}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {"temperature": 0.7},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates", [])
        content = candidates[0]["content"]["parts"][0]["text"] if candidates else ""
        return ProviderResponse(content=content)
