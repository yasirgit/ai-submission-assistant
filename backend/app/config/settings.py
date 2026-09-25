"""Runtime settings. Secrets come from the environment, never from source."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://finlex:finlex@localhost:5432/finlex"
    log_level: str = "INFO"
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 20.0
    retriever: str = "memory"
    retrieval_k: int = 5
    tool_timeout_seconds: float = 2.0
