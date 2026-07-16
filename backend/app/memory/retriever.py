"""Hybrid retriever for semantic memory."""

from typing import Any

from app.core.logging import get_logger
from app.memory.config import MemorySettings
from app.memory.embedding_service import EmbeddingService
from app.memory.exceptions import SearchException
from app.memory.schemas.memory import ChunkType, SearchRequest, SearchResult, SemanticChunk
from app.memory.vector_store import VectorStore

logger = get_logger(__name__)


class Retriever:
    """Hybrid retrieval combining semantic, keyword, and metadata search."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        settings: MemorySettings,
    ):
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._settings = settings

    async def search(self, request: SearchRequest) -> list[SearchResult]:
        """Perform hybrid search."""
        try:
            # 1. Semantic search
            semantic_results = await self._semantic_search(request)

            # 2. Metadata filter search
            metadata_results = await self._metadata_search(request)

            # 3. Combine and deduplicate
            combined = self._combine_results(semantic_results, metadata_results)

            # 4. Filter by threshold
            filtered = [r for r in combined if r.score >= request.similarity_threshold]

            # 5. Return top_k
            return filtered[: request.top_k]

        except SearchException:
            raise
        except Exception as e:
            raise SearchException(f"Search failed: {e}") from e

    async def _semantic_search(self, request: SearchRequest) -> list[SearchResult]:
        """Vector similarity search."""
        embedding = await self._embedding_service.embed_single(request.query)

        where: dict[str, Any] = {}
        if request.repository_id:
            where["repository_id"] = request.repository_id
        if request.chunk_types:
            chunk_type_values = [ct.value for ct in request.chunk_types]
            if len(chunk_type_values) == 1:
                where["chunk_type"] = chunk_type_values[0]
            else:
                where["chunk_type"] = {"$in": chunk_type_values}
        if request.language:
            where["language"] = request.language

        results = await self._vector_store.search(
            collection_name=self._settings.COLLECTION_REPOSITORIES,
            query_embedding=embedding,
            top_k=request.top_k * 2,
            where=where if where else None,
        )

        return self._parse_results(results)

    async def _metadata_search(self, request: SearchRequest) -> list[SearchResult]:
        """Keyword-based metadata search."""
        # Search across all collections with keyword matching
        # This is a simplified version - in production, you'd use ChromaDB's
        # where_document for full-text search
        try:
            where: dict[str, Any] = {}
            if request.repository_id:
                where["repository_id"] = request.repository_id

            results = await self._vector_store.search(
                collection_name=self._settings.COLLECTION_REPOSITORIES,
                query_embedding=await self._embedding_service.embed_single(request.query),
                top_k=request.top_k,
                where=where if where else None,
            )

            return self._parse_results(results)
        except Exception:
            # Metadata search is supplementary, don't fail the whole search
            return []

    def _combine_results(
        self, *result_lists: list[SearchResult]
    ) -> list[SearchResult]:
        """Combine and deduplicate results."""
        seen: dict[str, SearchResult] = {}
        for results in result_lists:
            for result in results:
                chunk_id = result.chunk.id
                if chunk_id not in seen or result.score > seen[chunk_id].score:
                    seen[chunk_id] = result
        return sorted(seen.values(), key=lambda r: r.score, reverse=True)

    def _parse_results(self, raw_results: dict[str, Any]) -> list[SearchResult]:
        """Parse ChromaDB results into SearchResult objects."""
        results: list[SearchResult] = []

        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for i, chunk_id in enumerate(ids):
            try:
                metadata = metadatas[i] if i < len(metadatas) else {}
                document = documents[i] if i < len(documents) else ""
                distance = distances[i] if i < len(distances) else 0.0

                # Convert distance to similarity score (cosine distance)
                score = 1.0 - distance

                chunk = SemanticChunk(
                    id=chunk_id,
                    repository_id=metadata.get("repository_id", ""),
                    chunk_type=ChunkType(metadata.get("chunk_type", "repository")),
                    content=document,
                    metadata=metadata,
                    embedding_model=metadata.get("embedding_model"),
                    created_at=metadata.get("created_at", ""),
                )

                results.append(
                    SearchResult(
                        chunk=chunk,
                        score=score,
                        rank=i + 1,
                    )
                )
            except Exception as e:
                logger.warning("Failed to parse result %d: %s", i, str(e))
                continue

        return results
