"""Provider factory – returns configured LLM / Embedding providers."""

from functools import lru_cache

from app.config.settings import settings
from ai_engine.providers.base import LLMProvider, EmbeddingProvider
from ai_engine.providers.mock_provider import MockLLMProvider, MockEmbeddingProvider
from ai_engine.providers.openai_provider import OpenAILLMProvider, OpenAIEmbeddingProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider = (settings.llm_provider or "mock").lower()
    if provider == "openai" and settings.openai_api_key:
        return OpenAILLMProvider()
    return MockLLMProvider()


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    provider = (settings.embedding_provider or "mock").lower()
    if provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddingProvider()
    return MockEmbeddingProvider()


def reset_providers() -> None:
    """Clear cached providers (useful in tests)."""
    get_llm_provider.cache_clear()
    get_embedding_provider.cache_clear()