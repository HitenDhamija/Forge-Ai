"""Memory data models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.repo_intelligence.schemas.analysis import AnalysisResult
from app.repo_intelligence.schemas.graph import SemanticGraph


class ChunkType(str, Enum):
    """Types of semantic chunks."""

    REPOSITORY = "repository"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ROUTE = "route"
    DATABASE = "database"
    CONFIG = "config"
    DOCUMENTATION = "documentation"


class SemanticChunk(BaseModel):
    """A semantic chunk of code or documentation."""

    id: str
    repository_id: str
    chunk_type: ChunkType
    content: str
    metadata: dict[str, Any] = {}
    embedding_model: str | None = None
    version: int = 1
    created_at: str


class ChunkMetadata(BaseModel):
    """Metadata for a semantic chunk."""

    repository_id: str
    repository_name: str
    language: str | None = None
    framework: str | None = None
    module_path: str | None = None
    class_name: str | None = None
    function_name: str | None = None
    purpose: str | None = None
    dependencies: list[str] = []
    related_apis: list[str] = []
    related_models: list[str] = []
    tags: list[str] = []
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None


class SearchResult(BaseModel):
    """A search result with score and rank."""

    chunk: SemanticChunk
    score: float
    rank: int
    explanation: str | None = None


class SearchRequest(BaseModel):
    """Request for semantic search."""

    query: str
    repository_id: str | None = None
    chunk_types: list[ChunkType] | None = None
    language: str | None = None
    framework: str | None = None
    tags: list[str] | None = None
    top_k: int = 20
    similarity_threshold: float = 0.3


class SearchResponse(BaseModel):
    """Response from semantic search."""

    query: str
    results: list[SearchResult]
    total_results: int
    search_time_ms: float
    query_classification: str | None = None


class ContextRequest(BaseModel):
    """Request for context building."""

    query: str
    repository_id: str | None = None
    max_tokens: int = 4096


class ContextResponse(BaseModel):
    """Response with optimized context."""

    query: str
    context: str
    chunks_used: list[SearchResult]
    query_classification: str
    token_count: int
    build_time_ms: float


class IndexRequest(BaseModel):
    """Request for indexing a repository."""

    repository_id: str
    repository_name: str
    analysis_result: AnalysisResult | None = None
    semantic_graph: SemanticGraph | None = None
    force_reindex: bool = False


class IndexResponse(BaseModel):
    """Response from indexing."""

    repository_id: str
    chunks_indexed: int
    collections_updated: list[str]
    index_time_ms: float


class CollectionStats(BaseModel):
    """Statistics for a collection."""

    name: str
    count: int
    size_bytes: int | None = None
    last_updated: str | None = None


class MemoryStats(BaseModel):
    """Overall memory statistics."""

    total_chunks: int
    total_repositories: int
    collections: list[CollectionStats]
    embedding_model: str
    embedding_dimension: int
    storage_size_bytes: int | None = None
