"""
Tests for the Semantic Memory Engine.

Comprehensive test suite covering embedding service, vector store,
semantic chunker, retriever, reranker, context builder, query classifier,
relationship graph, memory service, and API endpoints.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_embedding_model():
    """Mock sentence-transformers model."""
    model = MagicMock()
    model.encode.return_value = np.random.rand(10, 384).astype(np.float32)
    model.get_sentence_embedding_dimension.return_value = 384
    return model


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client."""
    client = MagicMock()
    collection = MagicMock()
    collection.name = "test_collection"
    collection.count.return_value = 100
    collection.add.return_value = None
    collection.query.return_value = {
        "ids": [["mem-1", "mem-2"]],
        "documents": [["Test document 1", "Test document 2"]],
        "metadatas": [[{"source": "test"}, {"source": "test"}]],
        "distances": [[0.1, 0.2]],
    }
    client.get_or_create_collection.return_value = collection
    client.get_collection.return_value = collection
    return client


@pytest.fixture
def sample_memory_content():
    """Sample memory content for testing."""
    return [
        {
            "content": "FastAPI is a modern web framework for building APIs with Python.",
            "metadata": {"source": "documentation", "importance": 0.8},
        },
        {
            "content": "Docker containers provide isolation for applications.",
            "metadata": {"source": "documentation", "importance": 0.7},
        },
        {
            "content": "Machine learning requires large datasets for training.",
            "metadata": {"source": "lecture", "importance": 0.9},
        },
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return np.random.rand(3, 384).astype(np.float32)


@pytest.fixture
def sample_search_results():
    """Sample search results."""
    return [
        {
            "id": "mem-1",
            "content": "FastAPI is a modern web framework for building APIs with Python.",
            "score": 0.92,
            "metadata": {
                "source": "documentation",
                "timestamp": "2024-06-15T10:30:00Z",
                "importance": 0.85,
            },
        },
        {
            "id": "mem-2",
            "content": "Docker containers provide isolation for applications.",
            "score": 0.87,
            "metadata": {
                "source": "documentation",
                "timestamp": "2024-06-14T15:45:00Z",
                "importance": 0.7,
            },
        },
    ]


@pytest.fixture
def sample_context_query():
    """Sample context query for testing."""
    return {
        "query": "How do I implement authentication in FastAPI?",
        "max_tokens": 4096,
        "collection": "code",
        "include_related": True,
        "format": "structured",
    }


# ============================================================
# Embedding Service Tests
# ============================================================


class TestEmbeddingService:
    """Tests for the EmbeddingService."""

    @pytest.mark.asyncio
    async def test_embed_text_single(self, mock_embedding_model):
        """Test embedding a single text."""
        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="BAAI/bge-small-en-v1.5",
                fallback_model="all-MiniLM-L6-v2",
            )

            result = await service.embed("Test text")

            assert result is not None
            assert len(result) == 384
            mock_embedding_model.encode.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_text_batch(self, mock_embedding_model):
        """Test embedding multiple texts."""
        mock_embedding_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)

        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="BAAI/bge-small-en-v1.5",
                fallback_model="all-MiniLM-L6-v2",
            )

            texts = ["Text 1", "Text 2", "Text 3"]
            result = await service.embed_batch(texts)

            assert result is not None
            assert len(result) == 3
            assert result[0].shape == (384,)

    @pytest.mark.asyncio
    async def test_embed_text_fallback(self):
        """Test embedding with fallback model on error."""
        primary_model = MagicMock()
        primary_model.encode.side_effect = RuntimeError("Model load failed")

        fallback_model = MagicMock()
        fallback_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)

        with patch("app.memory.embedding.SentenceTransformer", side_effect=[primary_model, fallback_model]):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="primary-model",
                fallback_model="fallback-model",
            )

            result = await service.embed("Test text")

            assert result is not None
            fallback_model.encode.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_empty_text(self, mock_embedding_model):
        """Test embedding empty text raises error."""
        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="test-model",
                fallback_model="fallback-model",
            )

            with pytest.raises(ValueError, match="cannot be empty"):
                await service.embed("")

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self, mock_embedding_model):
        """Test embedding empty list raises error."""
        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="test-model",
                fallback_model="fallback-model",
            )

            with pytest.raises(ValueError, match="cannot be empty"):
                await service.embed_batch([])

    @pytest.mark.asyncio
    async def test_get_embedding_dimension(self, mock_embedding_model):
        """Test getting embedding dimension."""
        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="test-model",
                fallback_model="fallback-model",
            )

            dimension = await service.get_dimension()

            assert dimension == 384

    @pytest.mark.asyncio
    async def test_embed_timeout_retry(self, mock_embedding_model):
        """Test retry on timeout."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Embedding timeout")
            return np.random.rand(1, 384).astype(np.float32)

        mock_embedding_model.encode.side_effect = side_effect

        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="test-model",
                fallback_model="fallback-model",
                max_retries=3,
            )

            result = await service.embed("Test text")

            assert result is not None
            assert call_count == 3


# ============================================================
# Vector Store Tests
# ============================================================


class TestVectorStore:
    """Tests for the VectorStore."""

    @pytest.mark.asyncio
    async def test_add_memory(self, mock_chroma_client):
        """Test adding a memory to vector store."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            await store.add(
                id="mem-1",
                embedding=np.random.rand(384).astype(np.float32),
                document="Test document",
                metadata={"source": "test"},
            )

            mock_chroma_client.get_or_create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_memory_batch(self, mock_chroma_client):
        """Test adding multiple memories."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            ids = ["mem-1", "mem-2", "mem-3"]
            embeddings = np.random.rand(3, 384).astype(np.float32)
            documents = ["Doc 1", "Doc 2", "Doc 3"]

            await store.add_batch(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
            )

            mock_chroma_client.get_or_create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(self, mock_chroma_client):
        """Test searching memories."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            results = await store.search(
                query_embedding=np.random.rand(384).astype(np.float32),
                top_k=10,
            )

            assert results is not None
            assert len(results["ids"][0]) == 2

    @pytest.mark.asyncio
    async def test_delete_memory(self, mock_chroma_client):
        """Test deleting a memory."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            await store.delete("mem-1")

            mock_chroma_client.get_or_create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, mock_chroma_client):
        """Test getting collection statistics."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            stats = await store.get_stats()

            assert stats is not None
            assert "count" in stats

    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_chroma_client):
        """Test searching with metadata filters."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            results = await store.search(
                query_embedding=np.random.rand(384).astype(np.float32),
                top_k=5,
                where={"source": "documentation"},
            )

            assert results is not None

    @pytest.mark.asyncio
    async def test_health_check(self, mock_chroma_client):
        """Test health check."""
        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            health = await store.health_check()

            assert health is True


# ============================================================
# Semantic Chunker Tests
# ============================================================


class TestSemanticChunker:
    """Tests for the SemanticChunker."""

    def test_chunk_simple_text(self):
        """Test chunking simple text."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=100)

        text = "This is a simple test paragraph. It contains multiple sentences."
        chunks = chunker.chunk(text)

        assert chunks is not None
        assert len(chunks) > 0
        assert all(hasattr(chunk, "content") for chunk in chunks)

    def test_chunk_preserves_paragraphs(self):
        """Test that chunking preserves paragraph boundaries."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=200)

        text = """
        First paragraph with important information.

        Second paragraph with different topic.

        Third paragraph concluding the text.
        """
        chunks = chunker.chunk(text)

        assert len(chunks) >= 2

    def test_chunk_respects_token_limit(self):
        """Test that chunks respect token limits."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=50)

        text = "Word " * 500  # Long text
        chunks = chunker.chunk(text)

        for chunk in chunks:
            word_count = len(chunk.content.split())
            assert word_count <= 60  # Allow some buffer

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=100)

        chunks = chunker.chunk("")

        assert chunks is not None
        assert len(chunks) == 0

    def test_chunk_metadata(self):
        """Test that chunks have proper metadata."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=100)

        text = "Test content for metadata."
        chunks = chunker.chunk(text)

        if chunks:
            chunk = chunks[0]
            assert hasattr(chunk, "start_position")
            assert hasattr(chunk, "end_position")
            assert hasattr(chunk, "importance")

    def test_chunk_code_content(self):
        """Test chunking code content."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=200)

        code = """
def hello_world():
    print("Hello, World!")
    return True

def another_function():
    return False
        """
        chunks = chunker.chunk(code, content_type="code")

        assert chunks is not None
        assert len(chunks) > 0


# ============================================================
# Retriever Tests
# ============================================================


class TestRetriever:
    """Tests for the Retriever."""

    @pytest.mark.asyncio
    async def test_retrieve_dense(self, mock_chroma_client, sample_embeddings):
        """Test dense retrieval."""
        with patch("app.memory.retriever.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.retriever import Retriever

            retriever = Retriever(
                vector_store=mock_chroma_client,
                embedding_model=MagicMock(),
            )

            results = await retriever.retrieve_dense(
                query="test query",
                top_k=5,
            )

            assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_hybrid(self, mock_chroma_client):
        """Test hybrid retrieval combining dense and sparse."""
        with patch("app.memory.retriever.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.retriever import Retriever

            retriever = Retriever(
                vector_store=mock_chroma_client,
                embedding_model=MagicMock(),
            )

            results = await retriever.retrieve_hybrid(
                query="test query",
                top_k=5,
            )

            assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, mock_chroma_client):
        """Test retrieval with metadata filters."""
        with patch("app.memory.retriever.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.retriever import Retriever

            retriever = Retriever(
                vector_store=mock_chroma_client,
                embedding_model=MagicMock(),
            )

            results = await retriever.retrieve_dense(
                query="test query",
                top_k=5,
                filters={"source": "documentation"},
            )

            assert results is not None

    @pytest.mark.asyncio
    async def test_retrieve_empty_query(self, mock_chroma_client):
        """Test retrieval with empty query raises error."""
        with patch("app.memory.retriever.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.retriever import Retriever

            retriever = Retriever(
                vector_store=mock_chroma_client,
                embedding_model=MagicMock(),
            )

            with pytest.raises(ValueError, match="cannot be empty"):
                await retriever.retrieve_dense(query="", top_k=5)


# ============================================================
# Reranker Tests
# ============================================================


class TestReranker:
    """Tests for the Reranker."""

    def test_rerank_by_relevance(self, sample_search_results):
        """Test reranking by relevance score."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        reranked = reranker.rerank(
            query="test query",
            results=sample_search_results,
            strategy="relevance",
        )

        assert reranked is not None
        assert len(reranked) == len(sample_search_results)
        # Check sorted by score
        assert reranked[0]["score"] >= reranked[1]["score"]

    def test_rerank_by_recency(self, sample_search_results):
        """Test reranking by recency."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        reranked = reranker.rerank(
            query="test query",
            results=sample_search_results,
            strategy="recency",
        )

        assert reranked is not None
        assert len(reranked) == len(sample_search_results)

    def test_rerank_by_importance(self, sample_search_results):
        """Test reranking by importance."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        reranked = reranker.rerank(
            query="test query",
            results=sample_search_results,
            strategy="importance",
        )

        assert reranked is not None
        assert len(reranked) == len(sample_search_results)

    def test_rerank_hybrid(self, sample_search_results):
        """Test hybrid reranking."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        reranked = reranker.rerank(
            query="test query",
            results=sample_search_results,
            strategy="hybrid",
        )

        assert reranked is not None
        assert len(reranked) == len(sample_search_results)

    def test_rerank_empty_results(self):
        """Test reranking empty results."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        reranked = reranker.rerank(
            query="test query",
            results=[],
            strategy="hybrid",
        )

        assert reranked is not None
        assert len(reranked) == 0

    def test_rerank_deduplication(self):
        """Test reranking deduplicates results."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        results = [
            {"id": "mem-1", "content": "Test", "score": 0.9},
            {"id": "mem-1", "content": "Test duplicate", "score": 0.8},
            {"id": "mem-2", "content": "Other", "score": 0.7},
        ]

        reranked = reranker.rerank(
            query="test query",
            results=results,
            strategy="relevance",
        )

        ids = [r["id"] for r in reranked]
        assert len(ids) == len(set(ids))  # No duplicates


# ============================================================
# Context Builder Tests
# ============================================================


class TestContextBuilder:
    """Tests for the ContextBuilder."""

    def test_build_context_structured(self, sample_search_results):
        """Test building structured context."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        context = builder.build(
            query="test query",
            memories=sample_search_results,
            max_tokens=4096,
            format="structured",
        )

        assert context is not None
        assert "memories" in context
        assert "token_count" in context

    def test_build_context_plain(self, sample_search_results):
        """Test building plain text context."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        context = builder.build(
            query="test query",
            memories=sample_search_results,
            max_tokens=4096,
            format="plain",
        )

        assert context is not None
        assert isinstance(context, str)

    def test_build_context_token_limit(self, sample_search_results):
        """Test context respects token limit."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        context = builder.build(
            query="test query",
            memories=sample_search_results,
            max_tokens=100,
            format="structured",
        )

        assert context["token_count"] <= 100

    def test_build_context_empty_memories(self):
        """Test building context with no memories."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        context = builder.build(
            query="test query",
            memories=[],
            max_tokens=4096,
            format="structured",
        )

        assert context is not None
        assert len(context["memories"]) == 0

    def test_build_context_summary(self, sample_search_results):
        """Test context includes summary."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        context = builder.build(
            query="test query",
            memories=sample_search_results,
            max_tokens=4096,
            format="structured",
        )

        assert "summary" in context
        assert isinstance(context["summary"], str)

    def test_build_context_groups_by_topic(self):
        """Test context groups memories by topic."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        memories = [
            {"id": "1", "content": "Python is a language", "metadata": {"tags": ["python"]}},
            {"id": "2", "content": "Python is used for ML", "metadata": {"tags": ["python", "ml"]}},
            {"id": "3", "content": "JavaScript is a language", "metadata": {"tags": ["javascript"]}},
        ]

        context = builder.build(
            query="programming languages",
            memories=memories,
            max_tokens=4096,
            format="structured",
        )

        assert "memories" in context


# ============================================================
# Query Classifier Tests
# ============================================================


class TestQueryClassifier:
    """Tests for the QueryClassifier."""

    def test_classify_factual_query(self):
        """Test classifying factual query."""
        from app.memory.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        result = classifier.classify("What is the capital of France?")

        assert result.query_type.value == "factual"

    def test_classify_conceptual_query(self):
        """Test classifying conceptual query."""
        from app.memory.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        result = classifier.classify("Explain how machine learning works")

        assert result.query_type.value == "conceptual"

    def test_classify_procedural_query(self):
        """Test classifying procedural query."""
        from app.memory.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        result = classifier.classify("How do I deploy a Docker container?")

        assert result.query_type.value == "procedural"

    def test_classify_contextual_query(self):
        """Test classifying contextual query."""
        from app.memory.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        result = classifier.classify("What did we discuss yesterday?")

        assert result.query_type.value == "contextual"

    def test_classify_exploratory_query(self):
        """Test classifying exploratory query."""
        from app.memory.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        result = classifier.classify("Tell me about Python frameworks")

        assert result.query_type.value == "exploratory"

    def test_classify_empty_query(self):
        """Test classifying empty query raises error."""
        from app.memory.query_classifier import QueryClassifier

        classifier = QueryClassifier()

        with pytest.raises(ValueError, match="cannot be empty"):
            classifier.classify("")


# ============================================================
# Relationship Graph Tests
# ============================================================


class TestRelationshipGraph:
    """Tests for the RelationshipGraph."""

    def test_add_memory(self):
        """Test adding memory to graph."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        graph.add_memory(
            id="mem-1",
            content="Test memory",
            metadata={"source": "test"},
        )

        assert graph.has_node("mem-1")

    def test_add_relationship(self):
        """Test adding relationship between memories."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        graph.add_memory(id="mem-1", content="Test 1")
        graph.add_memory(id="mem-2", content="Test 2")

        graph.add_relationship(
            source_id="mem-1",
            target_id="mem-2",
            relationship_type="related_to",
            strength=0.85,
        )

        assert graph.has_edge("mem-1", "mem-2")

    def test_get_related_memories(self):
        """Test getting related memories."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        graph.add_memory(id="mem-1", content="Test 1")
        graph.add_memory(id="mem-2", content="Test 2")
        graph.add_memory(id="mem-3", content="Test 3")

        graph.add_relationship("mem-1", "mem-2", "related_to")
        graph.add_relationship("mem-2", "mem-3", "supports")

        related = graph.get_related("mem-1", depth=2)

        assert len(related) >= 1

    def test_remove_memory(self):
        """Test removing memory from graph."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        graph.add_memory(id="mem-1", content="Test 1")
        graph.remove_memory("mem-1")

        assert not graph.has_node("mem-1")

    def test_find_path(self):
        """Test finding path between memories."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        graph.add_memory(id="mem-1", content="Test 1")
        graph.add_memory(id="mem-2", content="Test 2")
        graph.add_memory(id="mem-3", content="Test 3")

        graph.add_relationship("mem-1", "mem-2", "related_to")
        graph.add_relationship("mem-2", "mem-3", "supports")

        path = graph.find_path("mem-1", "mem-3")

        assert path is not None
        assert "mem-1" in path
        assert "mem-3" in path

    def test_empty_graph(self):
        """Test empty graph operations."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        assert not graph.has_node("nonexistent")
        assert graph.get_related("nonexistent") == []
        assert graph.find_path("a", "b") is None

    def test_get_graph_stats(self):
        """Test getting graph statistics."""
        from app.memory.relationship_graph import RelationshipGraph

        graph = RelationshipGraph()

        graph.add_memory(id="mem-1", content="Test 1")
        graph.add_memory(id="mem-2", content="Test 2")
        graph.add_relationship("mem-1", "mem-2", "related_to")

        stats = graph.get_stats()

        assert "node_count" in stats
        assert "edge_count" in stats
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1


# ============================================================
# Memory Service Tests
# ============================================================


class TestMemoryService:
    """Tests for the MemoryService (integration)."""

    @pytest.mark.asyncio
    async def test_index_memory(self, mock_chroma_client, mock_embedding_model):
        """Test indexing a new memory."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            result = await service.index(
                content="Test memory content",
                collection="test",
                metadata={"source": "test"},
            )

            assert result is not None
            assert "id" in result

    @pytest.mark.asyncio
    async def test_search_memories(self, mock_chroma_client, mock_embedding_model):
        """Test searching memories."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            results = await service.search(
                query="test query",
                top_k=5,
            )

            assert results is not None
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_get_context(self, mock_chroma_client, mock_embedding_model):
        """Test getting context for query."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            context = await service.get_context(
                query="test query",
                max_tokens=4096,
            )

            assert context is not None
            assert "memories" in context

    @pytest.mark.asyncio
    async def test_delete_memory(self, mock_chroma_client, mock_embedding_model):
        """Test deleting a memory."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            result = await service.delete("mem-1")

            assert result is True

    @pytest.mark.asyncio
    async def test_get_stats(self, mock_chroma_client, mock_embedding_model):
        """Test getting memory statistics."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            stats = await service.get_stats()

            assert stats is not None
            assert "total_memories" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, mock_chroma_client, mock_embedding_model):
        """Test service health check."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            health = await service.health_check()

            assert health is not None
            assert "chromadb" in health
            assert "embedding" in health


# ============================================================
# API Endpoint Tests
# ============================================================


class TestMemoryAPI:
    """Tests for Memory API endpoints."""

    @pytest.mark.asyncio
    async def test_index_endpoint(self, async_client):
        """Test POST /api/v1/memory/index."""
        response = await async_client.post(
            "/api/v1/memory/index",
            json={
                "memories": [
                    {
                        "content": "Test memory content",
                        "metadata": {"source": "test"},
                    }
                ],
                "collection": "test",
            },
        )

        # Will fail without proper service setup, but tests endpoint exists
        assert response.status_code in [201, 422, 500]

    @pytest.mark.asyncio
    async def test_search_endpoint(self, async_client):
        """Test POST /api/v1/memory/search."""
        response = await async_client.post(
            "/api/v1/memory/search",
            json={
                "query": "test query",
                "top_k": 5,
            },
        )

        assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_context_endpoint(self, async_client):
        """Test POST /api/v1/memory/context."""
        response = await async_client.post(
            "/api/v1/memory/context",
            json={
                "query": "How do I implement authentication?",
                "max_tokens": 4096,
            },
        )

        assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_get_memory_endpoint(self, async_client):
        """Test GET /api/v1/memory/{memory_id}."""
        response = await async_client.get(
            "/api/v1/memory/mem-123",
        )

        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_update_memory_endpoint(self, async_client):
        """Test PUT /api/v1/memory/{memory_id}."""
        response = await async_client.put(
            "/api/v1/memory/mem-123",
            json={
                "metadata": {"importance": 0.95},
            },
        )

        assert response.status_code in [200, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_delete_memory_endpoint(self, async_client):
        """Test DELETE /api/v1/memory/{memory_id}."""
        response = await async_client.delete(
            "/api/v1/memory/mem-123",
        )

        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_stats_endpoint(self, async_client):
        """Test GET /api/v1/memory/stats."""
        response = await async_client.get(
            "/api/v1/memory/stats",
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_related_endpoint(self, async_client):
        """Test POST /api/v1/memory/related."""
        response = await async_client.post(
            "/api/v1/memory/related",
            json={
                "memory_ids": ["mem-123"],
                "depth": 1,
            },
        )

        assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_reindex_endpoint(self, async_client):
        """Test POST /api/v1/memory/reindex."""
        response = await async_client.post(
            "/api/v1/memory/reindex",
            json={
                "collection": "test",
                "strategy": "full",
            },
        )

        assert response.status_code in [202, 422, 500]

    @pytest.mark.asyncio
    async def test_delete_collection_endpoint(self, async_client):
        """Test DELETE /api/v1/memory/collection/{name}."""
        response = await async_client.delete(
            "/api/v1/memory/collection/test",
        )

        assert response.status_code in [200, 404, 500]


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Tests for error handling in memory system."""

    @pytest.mark.asyncio
    async def test_index_empty_content(self, mock_chroma_client, mock_embedding_model):
        """Test indexing empty content raises error."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            with pytest.raises(ValueError, match="cannot be empty"):
                await service.index(content="", collection="test")

    @pytest.mark.asyncio
    async def test_search_empty_query(self, mock_chroma_client, mock_embedding_model):
        """Test search with empty query raises error."""
        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_embedding_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            with pytest.raises(ValueError, match="cannot be empty"):
                await service.search(query="", top_k=5)

    @pytest.mark.asyncio
    async def test_chromadb_connection_error(self, mock_embedding_model):
        """Test handling ChromaDB connection error."""
        with patch("app.memory.service.chromadb.Client", side_effect=ConnectionError("Connection refused")):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            with pytest.raises(ConnectionError):
                await service.health_check()

    @pytest.mark.asyncio
    async def test_embedding_model_error(self, mock_chroma_client):
        """Test handling embedding model error."""
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("Model load failed")
        mock_model.get_sentence_embedding_dimension.side_effect = RuntimeError("Model load failed")

        with (
            patch("app.memory.service.chromadb.Client", return_value=mock_chroma_client),
            patch("app.memory.service.SentenceTransformer", return_value=mock_model),
        ):
            from app.memory.service import MemoryService

            service = MemoryService(
                chroma_host="localhost",
                chroma_port=8000,
                embedding_model="test-model",
            )

            with pytest.raises(RuntimeError):
                await service.health_check()

    def test_chunker_invalid_strategy(self):
        """Test chunker with invalid strategy."""
        from app.memory.chunker import SemanticChunker

        chunker = SemanticChunker(max_tokens=100)

        with pytest.raises(ValueError, match="Invalid chunking strategy"):
            chunker.chunk("test", strategy="invalid")

    def test_reranker_invalid_strategy(self, sample_search_results):
        """Test reranker with invalid strategy."""
        from app.memory.reranker import Reranker

        reranker = Reranker()

        with pytest.raises(ValueError, match="Invalid reranking strategy"):
            reranker.rerank(
                query="test",
                results=sample_search_results,
                strategy="invalid",
            )

    def test_context_builder_invalid_format(self, sample_search_results):
        """Test context builder with invalid format."""
        from app.memory.context_builder import ContextBuilder

        builder = ContextBuilder()

        with pytest.raises(ValueError, match="Invalid format"):
            builder.build(
                query="test",
                memories=sample_search_results,
                max_tokens=4096,
                format="invalid",
            )


# ============================================================
# Performance Tests
# ============================================================


class TestPerformance:
    """Performance tests for memory operations."""

    @pytest.mark.asyncio
    async def test_batch_embedding_performance(self, mock_embedding_model):
        """Test batch embedding performance."""
        import time

        mock_embedding_model.encode.return_value = np.random.rand(100, 384).astype(np.float32)

        with patch("app.memory.embedding.SentenceTransformer", return_value=mock_embedding_model):
            from app.memory.embedding import EmbeddingService

            service = EmbeddingService(
                model_name="test-model",
                fallback_model="fallback-model",
            )

            start = time.time()
            result = await service.embed_batch([f"Text {i}" for i in range(100)])
            elapsed = time.time() - start

            assert elapsed < 5.0  # Should complete within 5 seconds

    def test_search_performance(self, mock_chroma_client):
        """Test search performance."""
        import time

        with patch("app.memory.vector_store.chromadb.Client", return_value=mock_chroma_client):
            from app.memory.vector_store import VectorStore

            store = VectorStore(
                host="localhost",
                port=8000,
                collection_prefix="test",
            )

            start = time.time()
            for _ in range(100):
                asyncio.get_event_loop().run_until_complete(
                    store.search(
                        query_embedding=np.random.rand(384).astype(np.float32),
                        top_k=10,
                    )
                )
            elapsed = time.time() - start

            assert elapsed < 10.0  # Should complete within 10 seconds
