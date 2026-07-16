"""AI module configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """AI module configuration loaded from environment variables with ``AI_`` prefix."""

    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 30
    OLLAMA_CONNECT_TIMEOUT: int = 5
    DEFAULT_MODEL: str = "qwen2.5:3b"
    MAX_CONTEXT_LENGTH: int = 4096
    MAX_RESPONSE_TOKENS: int = 2048
    MAX_PROMPT_LENGTH: int = 32000
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    TOP_K: int = 40
    STREAM_TIMEOUT: int = 120
    CONVERSATION_MAX_MESSAGES: int = 100
    CONVERSATION_MEMORY_ENABLED: bool = True


@lru_cache
def get_ai_settings() -> AISettings:
    """Return a cached ``AISettings`` instance."""
    return AISettings()
