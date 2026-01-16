from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderResponse:
    content: str


class LLMProvider(Protocol):
    async def generate(self, prompt: str, model: str, api_key: str) -> ProviderResponse:
        ...
