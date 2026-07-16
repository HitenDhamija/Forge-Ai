"""Embedding service using sentence-transformers."""

from typing import Any

from app.core.logging import get_logger
from app.memory.config import MemorySettings
from app.memory.exceptions import EmbeddingException

logger = get_logger(__name__)


class EmbeddingService:
    """Generates embeddings using sentence-transformers."""

    def __init__(self, settings: MemorySettings):
        self._settings = settings
        self._model: Any = None
        self._model_name = settings.EMBEDDING_MODEL
        self._fallback_model_name = settings.EMBEDDING_FALLBACK_MODEL

    async def _load_model(self) -> None:
        """Load the embedding model (lazy loading)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name)
                logger.info("Loaded embedding model: %s", self._model_name)
            except Exception as e:
                logger.warning(
                    "Failed to load %s, falling back to %s: %s",
                    self._model_name,
                    self._fallback_model_name,
                    str(e),
                )
                try:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self._fallback_model_name)
                    self._model_name = self._fallback_model_name
                    logger.info("Loaded fallback embedding model: %s", self._fallback_model_name)
                except Exception as fallback_error:
                    raise EmbeddingException(
                        f"Failed to load any embedding model: {fallback_error}"
                    ) from fallback_error

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        try:
            await self._load_model()
            embeddings = self._model.encode(
                texts, batch_size=self._settings.EMBEDDING_BATCH_SIZE
            )
            return embeddings.tolist()
        except EmbeddingException:
            raise
        except Exception as e:
            raise EmbeddingException(f"Failed to generate embeddings: {e}") from e

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed([text])
        return results[0]

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self._settings.EMBEDDING_DIMENSION

    def get_model_name(self) -> str:
        """Get the current model name."""
        return self._model_name
