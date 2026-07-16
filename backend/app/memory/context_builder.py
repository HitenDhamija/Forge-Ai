"""Context builder for semantic memory."""

import time

from app.memory.config import MemorySettings
from app.memory.schemas.memory import ContextResponse, SearchResult


class ContextBuilder:
    """Builds optimized context from search results."""

    def __init__(self, settings: MemorySettings):
        self._settings = settings

    def build(
        self,
        query: str,
        results: list[SearchResult],
        query_classification: str | None = None,
        max_tokens: int | None = None,
    ) -> ContextResponse:
        """Build optimized context from search results."""
        start_time = time.monotonic()
        max_tokens = max_tokens or self._settings.CONTEXT_MAX_TOKENS

        # Sort by relevance
        sorted_results = sorted(results, key=lambda r: r.score, reverse=True)

        # Build context sections
        context_parts: list[str] = []
        tokens_used = 0
        chunks_used: list[SearchResult] = []

        for result in sorted_results:
            chunk_content = result.chunk.content
            chunk_tokens = len(chunk_content) // 4  # rough estimate

            if tokens_used + chunk_tokens > max_tokens:
                # Try to fit a truncated version
                remaining_tokens = max_tokens - tokens_used
                if remaining_tokens > 100:
                    truncated = chunk_content[: remaining_tokens * 4]
                    context_parts.append(truncated)
                    chunks_used.append(result)
                break

            context_parts.append(chunk_content)
            chunks_used.append(result)
            tokens_used += chunk_tokens

        context = "\n\n---\n\n".join(context_parts)

        elapsed_ms = (time.monotonic() - start_time) * 1000

        return ContextResponse(
            query=query,
            context=context,
            chunks_used=chunks_used,
            query_classification=query_classification or "general",
            token_count=tokens_used,
            build_time_ms=round(elapsed_ms, 1),
        )
