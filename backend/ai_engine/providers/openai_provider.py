"""OpenAI-compatible LLM and Embedding providers."""

import time
from typing import Optional

from openai import AsyncOpenAI

from ai_engine.providers.base import LLMProvider, EmbeddingProvider, LLMResponse, EmbeddingResponse
from app.config.settings import settings


class OpenAILLMProvider(LLMProvider):
    name = "openai"

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key or "sk-missing",
            base_url=settings.openai_base_url,
            timeout=60.0,
        )
        self.model = settings.openai_model

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        start = time.perf_counter()
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = await self.client.chat.completions.create(**kwargs)
        latency = int((time.perf_counter() - start) * 1000)
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider=self.name,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency,
            finish_reason=choice.finish_reason,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
        )

    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key or "sk-missing",
            base_url=settings.openai_base_url,
            timeout=60.0,
        )
        self.model = settings.openai_embedding_model
        self.dimensions = settings.embedding_dimension

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        start = time.perf_counter()
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        latency = int((time.perf_counter() - start) * 1000)
        embeddings = [d.embedding for d in resp.data]
        dims = len(embeddings[0]) if embeddings else self.dimensions
        return EmbeddingResponse(
            embeddings=embeddings,
            model=resp.model,
            provider=self.name,
            dimensions=dims,
            latency_ms=latency,
        )

    async def health_check(self) -> bool:
        try:
            await self.embed(["health check"])
            return True
        except Exception:
            return False