"""Result reranker for semantic search."""

from app.memory.config import MemorySettings
from app.memory.schemas.memory import ChunkType, SearchResult


class Reranker:
    """Reranks search results based on multiple signals."""

    def __init__(self, settings: MemorySettings):
        self._settings = settings

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        query_classification: str | None = None,
    ) -> list[SearchResult]:
        """Rerank results using multiple scoring signals."""
        for result in results:
            # Base score from semantic similarity
            base_score = result.score

            # Architecture importance bonus
            arch_bonus = self._architecture_importance(result)

            # Relationship centrality bonus
            rel_bonus = self._relationship_centrality(result)

            # Metadata match bonus
            meta_bonus = self._metadata_match(result, query_classification)

            # Combined score
            result.score = base_score + arch_bonus + rel_bonus + meta_bonus

        # Sort by combined score
        results.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1

        return results[: self._settings.RERANK_TOP_K]

    def _architecture_importance(self, result: SearchResult) -> float:
        """Score based on architectural importance."""
        chunk_type = result.chunk.chunk_type
        weights = {
            ChunkType.REPOSITORY: 0.3,
            ChunkType.MODULE: 0.25,
            ChunkType.CLASS: 0.2,
            ChunkType.FUNCTION: 0.15,
            ChunkType.ROUTE: 0.2,
            ChunkType.DATABASE: 0.2,
            ChunkType.CONFIG: 0.1,
            ChunkType.DOCUMENTATION: 0.05,
        }
        return weights.get(chunk_type, 0.0) * 0.1

    def _relationship_centrality(self, result: SearchResult) -> float:
        """Score based on number of relationships."""
        deps = result.chunk.metadata.get("dependencies", [])
        rel_apis = result.chunk.metadata.get("related_apis", [])
        rel_models = result.chunk.metadata.get("related_models", [])
        total = len(deps) + len(rel_apis) + len(rel_models)
        return min(total * 0.01, 0.1)

    def _metadata_match(
        self, result: SearchResult, query_classification: str | None
    ) -> float:
        """Score based on metadata relevance to query type."""
        if query_classification is None:
            return 0.0
        # Boost chunks that match the query classification
        tags = result.chunk.metadata.get("tags", [])
        if query_classification.lower() in [t.lower() for t in tags]:
            return 0.05
        return 0.0
