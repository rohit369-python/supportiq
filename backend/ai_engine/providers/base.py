"""Abstract LLM and Embedding provider interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw: Optional[dict] = None
    finish_reason: Optional[str] = None


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    model: str
    provider: str
    dimensions: int
    latency_ms: int = 0


class LLMProvider(ABC):
    """Provider-independent LLM interface."""

    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


class EmbeddingProvider(ABC):
    """Provider-independent embedding interface."""

    name: str = "base"
    dimensions: int = 384

    @abstractmethod
    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...