from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETS_DIR = Path("/run/secrets")


class ModelSettings(BaseModel):
    reply: str = "ollama:qwen3.5:9b"
    fast: str = "ollama:qwen3.5:9b"
    embedding: str = "BAAI/bge-m3"
    reranker: str = "BAAI/bge-reranker-v2-m3"
    ollama_base_url: str = "http://localhost:11434"
    ollama_reasoning: bool | None = False
    request_timeout_s: float = 60
    temperature: float = 0.2
    max_output_tokens: int = 800


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CONVOX_AI_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=_SECRETS_DIR if _SECRETS_DIR.is_dir() else None,
    )

    database_url: PostgresDsn
    kafka_bootstrap: str
    s3_endpoint: str | None = None
    s3_bucket: str
    s3_access_key: SecretStr
    s3_secret_key: SecretStr
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: SecretStr | None = None
    models: ModelSettings = ModelSettings()
    reply_concurrency: int = 8
    ingest_max_file_mb: int = 25


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()