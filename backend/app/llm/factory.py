"""Select the model client from the environment. Tests pass a client in directly."""

from app.config.settings import Settings
from app.llm.errors import LLMConfigError
from app.llm.mock import MockLLMClient
from app.llm.openai import OpenAIClient
from app.llm.types import LLMClient


def build_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.strip().lower()
    if provider == "mock":
        return MockLLMClient()
    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIClient(
            settings.openai_api_key,
            settings.openai_model,
            settings.llm_timeout_seconds,
        )
    raise LLMConfigError("LLM_PROVIDER must be 'mock' or 'openai'")
