import httpx

from .base import ProviderResponse


class OpenAIProvider:
    def _use_responses_api(self, model: str) -> bool:
        model_name = (model or "").lower()
        return model_name.startswith("gpt-5") or model_name.startswith("o1")

    def _extract_response_text(self, data: dict) -> str:
        if "output_text" in data and data["output_text"]:
            return data["output_text"]
        output = data.get("output", [])
        for item in output:
            if item.get("type") != "message":
                continue
            contents = item.get("content", [])
            parts = []
            for content in contents:
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
            if parts:
                return "\n".join(parts).strip()
        return ""

    async def generate(self, prompt: str, model: str, api_key: str) -> ProviderResponse:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            if self._use_responses_api(model):
                payload = {
                    "model": model,
                    "input": [
                        {
                            "role": "system",
                            "content": [{"type": "input_text", "text": "You are a careful research assistant."}],
                        },
                        {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
                    ],
                }
                response = await client.post("https://api.openai.com/v1/responses", json=payload, headers=headers)
                if response.status_code >= 400:
                    raise RuntimeError(f"OpenAI error {response.status_code}: {response.text}")
                data = response.json()
                content = self._extract_response_text(data)
            else:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a careful research assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                }
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if response.status_code >= 400:
                    raise RuntimeError(f"OpenAI error {response.status_code}: {response.text}")
                data = response.json()
                content = data["choices"][0]["message"]["content"]
        return ProviderResponse(content=content)
