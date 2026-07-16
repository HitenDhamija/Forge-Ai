"""Semantic memory configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class MemorySettings(BaseSettings):
    """Semantic memory configuration."""

    model_config = SettingsConfigDict(env_prefix="MEMORY_")

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "/tmp/forgeai/chroma"

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_FALLBACK_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    CHUNK_MAX_TOKENS: int = 512
    CHUNK_OVERLAP_TOKENS: int = 50

    SEARCH_TOP_K: int = 20
    SEARCH_SIMILARITY_THRESHOLD: float = 0.3
    RERANK_TOP_K: int = 10

    CONTEXT_MAX_TOKENS: int = 4096

    COLLECTION_REPOSITORIES: str = "repositories"
    COLLECTION_MODULES: str = "modules"
    COLLECTION_FUNCTIONS: str = "functions"
    COLLECTION_CLASSES: str = "classes"
    COLLECTION_DOCUMENTATION: str = "documentation"


@lru_cache
def get_memory_settings() -> MemorySettings:
    """Return cached memory settings instance."""
    return MemorySettings()
