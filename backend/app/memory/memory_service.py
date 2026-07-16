"""Main semantic memory service."""

import time
from typing import Any

from app.core.logging import get_logger
from app.memory.chunker import SemanticChunker
from app.memory.config import MemorySettings
from app.memory.context_builder import ContextBuilder
from app.memory.embedding_service import EmbeddingService
from app.memory.exceptions import IndexingException
from app.memory.query_classifier import QueryClassifier
from app.memory.relationship_graph import RelationshipGraph
from app.memory.reranker import Reranker
from app.memory.retriever import Retriever
from app.memory.schemas.memory import (
    ChunkMetadata,
    CollectionStats,
    ContextRequest,
    ContextResponse,
    IndexRequest,
    IndexResponse,
    MemoryStats,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.memory.vector_store import VectorStore
from app.repo_intelligence.schemas.analysis import AnalysisResult
from app.repo_intelligence.schemas.graph import SemanticGraph

logger = get_logger(__name__)


class MemoryService:
    """Main semantic memory service orchestrating all components."""

    def __init__(self, settings: MemorySettings):
        self._settings = settings
        self._embedding_service = EmbeddingService(settings)
        self._vector_store = VectorStore(settings)
        self._chunker = SemanticChunker(settings)
        self._retriever = Retriever(self._vector_store, self._embedding_service, settings)
        self._reranker = Reranker(settings)
        self._context_builder = ContextBuilder(settings)
        self._query_classifier = QueryClassifier()
        self._relationship_graph = RelationshipGraph(self._vector_store)

    async def index_repository(
        self,
        repository_id: str,
        repository_name: str,
        analysis: AnalysisResult,
        graph: SemanticGraph | None = None,
        force_reindex: bool = False,
    ) -> IndexResponse:
        """Index a repository into memory."""
        start_time = time.monotonic()

        try:
            # 1. Delete existing chunks if reindexing
            if force_reindex:
                await self._vector_store.delete_documents(
                    self._settings.COLLECTION_REPOSITORIES,
                    {"repository_id": repository_id},
                )

            # 2. Create semantic chunks
            chunks = self._chunker.chunk_repository(repository_id, repository_name, analysis)

            # 3. Generate embeddings
            texts = [c.content for c in chunks]
            embeddings = await self._embedding_service.embed(texts)

            # 4. Prepare metadata
            ids = [c.id for c in chunks]
            metadatas: list[dict[str, Any]] = [c.metadata for c in chunks]
            for i, chunk in enumerate(chunks):
                metadatas[i]["chunk_type"] = chunk.chunk_type.value
                metadatas[i]["repository_id"] = repository_id
                metadatas[i]["repository_name"] = repository_name
                metadatas[i]["embedding_model"] = self._embedding_service.get_model_name()
                metadatas[i]["created_at"] = chunk.created_at

            # 5. Store in ChromaDB
            await self._vector_store.add_documents(
                collection_name=self._settings.COLLECTION_REPOSITORIES,
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            # 6. Build relationships
            await self._relationship_graph.build_relationships(repository_id, chunks, graph)

            elapsed_ms = (time.monotonic() - start_time) * 1000

            logger.info(
                "Repository indexed: repo=%s chunks=%d time=%.1fms",
                repository_id,
                len(chunks),
                elapsed_ms,
            )

            return IndexResponse(
                repository_id=repository_id,
                chunks_indexed=len(chunks),
                collections_updated=[self._settings.COLLECTION_REPOSITORIES],
                index_time_ms=round(elapsed_ms, 1),
            )

        except Exception as e:
            raise IndexingException(f"Failed to index repository: {e}") from e

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search memory."""
        start_time = time.monotonic()

        # 1. Classify query
        classification = self._query_classifier.classify(request.query)

        # 2. Get search hints
        hints = self._query_classifier.get_search_hints(classification)

        # 3. Enhance request with hints
        if "chunk_types" in hints and not request.chunk_types:
            from app.memory.schemas.memory import ChunkType

            request.chunk_types = [ChunkType(ct) for ct in hints["chunk_types"]]

        # 4. Retrieve
        results = await self._retriever.search(request)

        # 5. Rerank
        reranked = self._reranker.rerank(request.query, results, classification)

        elapsed_ms = (time.monotonic() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=reranked,
            total_results=len(reranked),
            search_time_ms=round(elapsed_ms, 1),
            query_classification=classification,
        )

    async def get_context(self, request: ContextRequest) -> ContextResponse:
        """Get optimized context for a query."""
        # 1. Search
        search_request = SearchRequest(
            query=request.query,
            repository_id=request.repository_id,
            top_k=self._settings.SEARCH_TOP_K,
        )
        search_response = await self.search(search_request)

        # 2. Build context
        context = self._context_builder.build(
            query=request.query,
            results=search_response.results,
            query_classification=search_response.query_classification,
            max_tokens=request.max_tokens,
        )

        return context

    async def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        stats = await self._vector_store.get_stats()

        collections: list[CollectionStats] = []
        for col in stats.get("collections", []):
            collections.append(
                CollectionStats(
                    name=col["name"],
                    count=col["count"],
                )
            )

        # Count unique repositories
        total_repos = 0
        collection = await self._vector_store.get_collection(
            self._settings.COLLECTION_REPOSITORIES
        )
        all_data = collection.get(include=["metadatas"])
        repo_ids: set[str] = set()
        for meta in all_data.get("metadatas", []):
            repo_id = meta.get("repository_id", "")
            if repo_id:
                repo_ids.add(repo_id)
        total_repos = len(repo_ids)

        return MemoryStats(
            total_chunks=stats.get("total_documents", 0),
            total_repositories=total_repos,
            collections=collections,
            embedding_model=self._embedding_service.get_model_name(),
            embedding_dimension=self._embedding_service.get_dimension(),
        )

    async def delete_repository(self, repository_id: str) -> bool:
        """Delete all memory for a repository."""
        await self._vector_store.delete_documents(
            self._settings.COLLECTION_REPOSITORIES,
            {"repository_id": repository_id},
        )
        return True

    async def list_repositories(self) -> list[dict[str, Any]]:
        """List all indexed repositories."""
        collection = await self._vector_store.get_collection(
            self._settings.COLLECTION_REPOSITORIES
        )
        all_data = collection.get(include=["metadatas"])
        repos: dict[str, dict[str, str]] = {}
        for meta in all_data.get("metadatas", []):
            repo_id = meta.get("repository_id", "")
            repo_name = meta.get("repository_name", "")
            if repo_id and repo_id not in repos:
                repos[repo_id] = {"id": repo_id, "name": repo_name}
        return list(repos.values())
