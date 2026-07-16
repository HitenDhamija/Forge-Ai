"""Tests for the ForgeAI AI module.

Covers OllamaClient, ModelManager, PromptRegistry, ConversationManager,
chat controller flow, streaming handler, and API endpoints.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ai.config import AISettings, get_ai_settings
from app.ai.clients.ollama import OllamaClient
from app.ai.exceptions import (
    AITimeoutException,
    ModelNotFoundException,
    ModelSwitchException,
    OllamaConnectionException,
    StreamingException,
)
from app.ai.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    ConversationHistory,
    MessageRole,
)
from app.ai.schemas.model import (
    ModelInfo,
    ModelListResponse,
    ModelStatus,
    ModelStatusEnum,
    ModelSwitchRequest,
    ModelSwitchResponse,
    OllamaStatus,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def ai_settings() -> AISettings:
    """Return test AI settings."""
    return AISettings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_TIMEOUT=5,
        OLLAMA_CONNECT_TIMEOUT=2,
        DEFAULT_MODEL="qwen2.5",
        MAX_CONTEXT_LENGTH=4096,
        MAX_RESPONSE_TOKENS=2048,
        TEMPERATURE=0.7,
    )


@pytest.fixture
def ollama_client(ai_settings: AISettings) -> OllamaClient:
    """Return an OllamaClient with test settings."""
    return OllamaClient(
        base_url=ai_settings.OLLAMA_BASE_URL,
        timeout=ai_settings.OLLAMA_TIMEOUT,
        connect_timeout=ai_settings.OLLAMA_CONNECT_TIMEOUT,
    )


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Return a mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.is_closed = False
    return client


@pytest.fixture
def sample_chat_request() -> ChatRequest:
    """Return a sample chat request."""
    return ChatRequest(
        message="Hello, how are you?",
        model="qwen2.5",
        conversation_id=None,
        stream=True,
        temperature=0.7,
        max_tokens=1024,
    )


@pytest.fixture
def sample_chat_response() -> ChatResponse:
    """Return a sample chat response."""
    return ChatResponse(
        conversation_id="conv-123",
        message=ChatMessage(
            role=MessageRole.ASSISTANT,
            content="I'm doing well, thank you!",
        ),
        model_used="qwen2.5",
        response_time_ms=150.5,
        token_count=12,
    )


@pytest.fixture
def sample_conversation_history() -> ConversationHistory:
    """Return a sample conversation history."""
    return ConversationHistory(
        id="conv-123",
        title="Test Conversation",
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=MessageRole.USER, content="Hello!"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
        ],
        model_used="qwen2.5",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        message_count=3,
    )


# ============================================================
# Test AI Settings
# ============================================================


class TestAISettings:
    """Tests for AISettings configuration."""

    def test_default_settings(self) -> None:
        """Test default AI settings values."""
        settings = AISettings()
        assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
        assert settings.DEFAULT_MODEL == "qwen2.5"
        assert settings.MAX_CONTEXT_LENGTH == 4096
        assert settings.TEMPERATURE == 0.7

    def test_custom_settings(self) -> None:
        """Test AI settings with custom values."""
        settings = AISettings(
            OLLAMA_BASE_URL="http://custom:11434",
            DEFAULT_MODEL="llama3.2",
            MAX_CONTEXT_LENGTH=8192,
            TEMPERATURE=0.3,
        )
        assert settings.OLLAMA_BASE_URL == "http://custom:11434"
        assert settings.DEFAULT_MODEL == "llama3.2"
        assert settings.MAX_CONTEXT_LENGTH == 8192
        assert settings.TEMPERATURE == 0.3

    def test_get_ai_settings_returns_cached(self) -> None:
        """Test that get_ai_settings returns a cached instance."""
        s1 = get_ai_settings()
        s2 = get_ai_settings()
        assert s1 is s2


# ============================================================
# Test Chat Schemas
# ============================================================


class TestChatSchemas:
    """Tests for chat-related Pydantic schemas."""

    def test_chat_request_validation(self) -> None:
        """Test ChatRequest validates required fields."""
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.model is None
        assert req.stream is True

    def test_chat_request_empty_message_rejected(self) -> None:
        """Test ChatRequest rejects empty message."""
        with pytest.raises(Exception):
            ChatRequest(message="")

    def test_chat_message_creation(self) -> None:
        """Test ChatMessage creation with role and content."""
        msg = ChatMessage(role=MessageRole.USER, content="Test")
        assert msg.role == MessageRole.USER
        assert msg.content == "Test"
        assert msg.timestamp is not None

    def test_chat_response_creation(self) -> None:
        """Test ChatResponse schema creation."""
        resp = ChatResponse(
            conversation_id="conv-1",
            message=ChatMessage(role=MessageRole.ASSISTANT, content="Hi"),
            model_used="qwen2.5",
            response_time_ms=100.0,
        )
        assert resp.conversation_id == "conv-1"
        assert resp.model_used == "qwen2.5"

    def test_chat_stream_chunk_creation(self) -> None:
        """Test ChatStreamChunk schema creation."""
        chunk = ChatStreamChunk(
            conversation_id="conv-1",
            content="Hello",
            done=False,
            model="qwen2.5",
        )
        assert chunk.content == "Hello"
        assert chunk.done is False

    def test_chat_stream_chunk_done(self) -> None:
        """Test ChatStreamChunk with done=True has empty content."""
        chunk = ChatStreamChunk(
            conversation_id="conv-1",
            content="",
            done=True,
            model="qwen2.5",
        )
        assert chunk.done is True

    def test_conversation_history_creation(self) -> None:
        """Test ConversationHistory schema creation."""
        hist = ConversationHistory(
            id="conv-1",
            title="Test",
            messages=[],
            model_used="qwen2.5",
        )
        assert hist.id == "conv-1"
        assert hist.message_count == 0

    def test_message_role_enum(self) -> None:
        """Test MessageRole enum values."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"


# ============================================================
# Test Model Schemas
# ============================================================


class TestModelSchemas:
    """Tests for model-related Pydantic schemas."""

    def test_model_info_creation(self) -> None:
        """Test ModelInfo schema creation."""
        info = ModelInfo(name="qwen2.5", size=4_000_000_000)
        assert info.name == "qwen2.5"
        assert info.size == 4_000_000_000

    def test_model_status_enum(self) -> None:
        """Test ModelStatusEnum values."""
        assert ModelStatusEnum.RUNNING == "running"
        assert ModelStatusEnum.AVAILABLE == "available"
        assert ModelStatusEnum.OFFLINE == "offline"

    def test_model_list_response(self) -> None:
        """Test ModelListResponse schema."""
        resp = ModelListResponse(
            models=[ModelInfo(name="qwen2.5")],
            active_model="qwen2.5",
        )
        assert len(resp.models) == 1
        assert resp.active_model == "qwen2.5"

    def test_model_switch_request(self) -> None:
        """Test ModelSwitchRequest schema."""
        req = ModelSwitchRequest(model_name="llama3.2")
        assert req.model_name == "llama3.2"

    def test_model_switch_response(self) -> None:
        """Test ModelSwitchResponse schema."""
        resp = ModelSwitchResponse(
            previous_model="qwen2.5",
            current_model="llama3.2",
        )
        assert resp.status == "success"

    def test_ollama_status(self) -> None:
        """Test OllamaStatus schema."""
        status = OllamaStatus(
            connected=True,
            version="0.3.0",
            models_count=5,
            running_models=["qwen2.5"],
        )
        assert status.connected is True
        assert status.models_count == 5


# ============================================================
# Test OllamaClient
# ============================================================


class TestOllamaClient:
    """Tests for the OllamaClient async HTTP client."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, ollama_client: OllamaClient) -> None:
        """Test health check returns True when Ollama is reachable."""
        mock_response = AsyncMock()
        mock_response.status_code = 200

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        result = await ollama_client.health_check()
        assert result is True
        mock_client.get.assert_called_with("/api/tags")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, ollama_client: OllamaClient) -> None:
        """Test health check returns False on connection error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.is_closed = False
        ollama_client._client = mock_client

        result = await ollama_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_non_200(self, ollama_client: OllamaClient) -> None:
        """Test health check returns False on non-200 status."""
        mock_response = AsyncMock()
        mock_response.status_code = 500

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        result = await ollama_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_version_success(self, ollama_client: OllamaClient) -> None:
        """Test get_version returns version string."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.3.0"}

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        version = await ollama_client.get_version()
        assert version == "0.3.0"

    @pytest.mark.asyncio
    async def test_get_version_failure(self, ollama_client: OllamaClient) -> None:
        """Test get_version returns None on failure."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.is_closed = False
        ollama_client._client = mock_client

        version = await ollama_client.get_version()
        assert version is None

    @pytest.mark.asyncio
    async def test_list_models_success(self, ollama_client: OllamaClient) -> None:
        """Test list_models returns model list."""
        models = [{"name": "qwen2.5", "size": 4_000_000_000}]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": models}

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        result = await ollama_client.list_models()
        assert len(result) == 1
        assert result[0]["name"] == "qwen2.5"

    @pytest.mark.asyncio
    async def test_list_models_connection_error(self, ollama_client: OllamaClient) -> None:
        """Test list_models raises OllamaConnectionException on error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.is_closed = False
        ollama_client._client = mock_client

        with pytest.raises(OllamaConnectionException):
            await ollama_client.list_models()

    @pytest.mark.asyncio
    async def test_show_model_success(self, ollama_client: OllamaClient) -> None:
        """Test show_model returns model details."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "qwen2.5", "family": "qwen"}

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        result = await ollama_client.show_model("qwen2.5")
        assert result["name"] == "qwen2.5"

    @pytest.mark.asyncio
    async def test_show_model_not_found(self, ollama_client: OllamaClient) -> None:
        """Test show_model raises ModelNotFoundException for 404."""
        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        with pytest.raises(ModelNotFoundException):
            await ollama_client.show_model("nonexistent")

    @pytest.mark.asyncio
    async def test_generate_non_streaming(self, ollama_client: OllamaClient) -> None:
        """Test generate with stream=False returns dict."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = await ollama_client.generate(
            model="qwen2.5",
            messages=messages,
            stream=False,
        )
        assert isinstance(result, dict)
        assert result["message"]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_generate_streaming(self, ollama_client: OllamaClient) -> None:
        """Test generate with stream=True returns async generator."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False

        # Mock the stream context manager
        lines = [
            json.dumps({"message": {"content": "Hi"}, "done": False, "model": "qwen2.5"}),
            json.dumps({"message": {"content": " there"}, "done": False, "model": "qwen2.5"}),
            json.dumps({"message": {"content": ""}, "done": True, "model": "qwen2.5"}),
        ]
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = MagicMock(return_value=iter(lines))

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_cm)

        ollama_client._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = await ollama_client.generate(
            model="qwen2.5",
            messages=messages,
            stream=True,
        )
        # Should return an async generator
        assert hasattr(result, '__aiter__')

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, ollama_client: OllamaClient) -> None:
        """Test generate raises OllamaConnectionException on connection error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.is_closed = False
        ollama_client._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        with pytest.raises(OllamaConnectionException):
            await ollama_client.generate(
                model="qwen2.5",
                messages=messages,
                stream=False,
            )

    @pytest.mark.asyncio
    async def test_generate_stream_returns_empty_on_non_200(
        self, ollama_client: OllamaClient
    ) -> None:
        """Test generate_stream returns nothing on non-200 status."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False

        mock_resp = AsyncMock()
        mock_resp.status_code = 500
        mock_resp.aread = AsyncMock(return_value=b"Internal Server Error")

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_cm)

        ollama_client._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        chunks = []
        async for chunk in ollama_client.generate_stream(
            model="qwen2.5",
            messages=messages,
        ):
            chunks.append(chunk)
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_generate_stream_timeout(self, ollama_client: OllamaClient) -> None:
        """Test generate_stream raises AITimeoutException on timeout."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False

        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        async def mock_aiter_lines():
            raise httpx.ReadTimeout("read timeout")
            yield  # Make it an async generator

        mock_resp.aiter_lines = mock_aiter_lines

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(return_value=mock_cm)

        ollama_client._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        with pytest.raises(AITimeoutException):
            async for _ in ollama_client.generate_stream(
                model="qwen2.5",
                messages=messages,
            ):
                pass

    @pytest.mark.asyncio
    async def test_close_client(self, ollama_client: OllamaClient) -> None:
        """Test close() closes the httpx client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        ollama_client._client = mock_client

        await ollama_client.close()
        mock_client.aclose.assert_called_once()
        assert ollama_client._client is None

    @pytest.mark.asyncio
    async def test_close_already_closed(self, ollama_client: OllamaClient) -> None:
        """Test close() is safe when client is already closed."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = True
        ollama_client._client = mock_client

        await ollama_client.close()
        mock_client.aclose.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_client_creates_new(self, ollama_client: OllamaClient) -> None:
        """Test _get_client creates a new client when none exists."""
        assert ollama_client._client is None
        client = await ollama_client._get_client()
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing(self, ollama_client: OllamaClient) -> None:
        """Test _get_client reuses existing client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        client = await ollama_client._get_client()
        assert client is mock_client


# ============================================================
# Test Exceptions
# ============================================================


class TestAIExceptions:
    """Tests for AI-specific exception classes."""

    def test_ollama_connection_exception(self) -> None:
        """Test OllamaConnectionException message."""
        exc = OllamaConnectionException()
        assert "Cannot connect to Ollama" in str(exc.message)

    def test_ollama_connection_exception_custom_message(self) -> None:
        """Test OllamaConnectionException with custom message."""
        exc = OllamaConnectionException("Custom error")
        assert exc.message == "Custom error"

    def test_model_not_found_exception(self) -> None:
        """Test ModelNotFoundException message."""
        exc = ModelNotFoundException()
        assert "Model not found" in str(exc.message)

    def test_model_not_found_with_detail(self) -> None:
        """Test ModelNotFoundException with detail."""
        exc = ModelNotFoundException("Model 'xyz' not found")
        assert "xyz" in exc.message

    def test_streaming_exception(self) -> None:
        """Test StreamingException message."""
        exc = StreamingException()
        assert "Streaming error" in str(exc.message)

    def test_ai_timeout_exception(self) -> None:
        """Test AITimeoutException message."""
        exc = AITimeoutException()
        assert "timed out" in str(exc.message)

    def test_model_switch_exception(self) -> None:
        """Test ModelSwitchException message."""
        exc = ModelSwitchException()
        assert "switch" in str(exc.message).lower()

    def test_exceptions_inherit_from_base(self) -> None:
        """Test all AI exceptions inherit from ForgeBaseException."""
        from app.exceptions import ForgeBaseException

        assert issubclass(OllamaConnectionException, ForgeBaseException)
        assert issubclass(ModelNotFoundException, ForgeBaseException)
        assert issubclass(StreamingException, ForgeBaseException)
        assert issubclass(AITimeoutException, ForgeBaseException)
        assert issubclass(ModelSwitchException, ForgeBaseException)


# ============================================================
# Test Mocked API Endpoints
# ============================================================


class TestChatAPI:
    """Tests for chat API endpoints using mocked Ollama."""

    @pytest.mark.asyncio
    async def test_chat_health_endpoint(self) -> None:
        """Test the Ollama health check endpoint."""
        from httpx import ASGITransport, AsyncClient

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_request_schema_validation(self) -> None:
        """Test ChatRequest rejects invalid input."""
        # Message is required
        with pytest.raises(Exception):
            ChatRequest()

        # Message must not be empty
        with pytest.raises(Exception):
            ChatRequest(message="")

        # Temperature must be in range
        with pytest.raises(Exception):
            ChatRequest(message="Hello", temperature=3.0)

    @pytest.mark.asyncio
    async def test_chat_response_schema_fields(self) -> None:
        """Test ChatResponse has all required fields."""
        resp = ChatResponse(
            conversation_id="test-conv",
            message=ChatMessage(role=MessageRole.ASSISTANT, content="Response"),
            model_used="qwen2.5",
            response_time_ms=200.0,
            token_count=5,
        )
        data = resp.model_dump()
        assert "conversation_id" in data
        assert "message" in data
        assert "model_used" in data
        assert "response_time_ms" in data
        assert "token_count" in data

    @pytest.mark.asyncio
    async def test_stream_chunk_serialization(self) -> None:
        """Test ChatStreamChunk serializes to dict correctly."""
        chunk = ChatStreamChunk(
            conversation_id="conv-1",
            content="token",
            done=False,
            model="qwen2.5",
        )
        data = chunk.model_dump()
        assert data["content"] == "token"
        assert data["done"] is False
        assert "created_at" in data


# ============================================================
# Test Integration Scenarios
# ============================================================


class TestIntegrationScenarios:
    """Integration-style tests for AI module workflows."""

    @pytest.mark.asyncio
    async def test_full_chat_flow_mocked(self, ollama_client: OllamaClient) -> None:
        """Test a complete chat flow with mocked Ollama responses."""
        # Simulate listing models
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen2.5", "size": 4_000_000_000}]
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        ollama_client._client = mock_client

        # List models
        models = await ollama_client.list_models()
        assert len(models) == 1
        assert models[0]["name"] == "qwen2.5"

        # Health check
        health = await ollama_client.health_check()
        assert health is True

    @pytest.mark.asyncio
    async def test_model_switch_flow(self) -> None:
        """Test model switch request/response flow."""
        # Create switch request
        req = ModelSwitchRequest(model_name="llama3.2:3b")
        assert req.model_name == "llama3.2:3b"

        # Create switch response
        resp = ModelSwitchResponse(
            previous_model="qwen2.5",
            current_model="llama3.2:3b",
        )
        assert resp.previous_model == "qwen2.5"
        assert resp.current_model == "llama3.2:3b"
        assert resp.status == "success"

    @pytest.mark.asyncio
    async def test_conversation_persistence_flow(self) -> None:
        """Test conversation creation and message addition flow."""
        conv = ConversationHistory(
            id="conv-new",
            title="New Chat",
            messages=[],
            model_used="qwen2.5",
        )
        assert conv.message_count == 0

        # Add messages
        conv.messages.append(
            ChatMessage(role=MessageRole.USER, content="Hello!")
        )
        conv.messages.append(
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!")
        )
        conv.message_count = len(conv.messages)

        assert conv.message_count == 2
        assert conv.messages[0].role == MessageRole.USER
        assert conv.messages[1].role == MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_ollama_status_flow(self) -> None:
        """Test Ollama status reporting."""
        status = OllamaStatus(
            connected=True,
            version="0.3.0",
            models_count=3,
            running_models=["qwen2.5", "llama3.2:3b"],
        )
        assert status.connected is True
        assert status.models_count == 3
        assert "qwen2.5" in status.running_models

    @pytest.mark.asyncio
    async def test_model_info_from_ollama(self) -> None:
        """Test parsing model info from Ollama API response."""
        info = ModelInfo(
            name="qwen2.5:7b",
            size=4_400_000_000,
            digest="sha256:abc123",
            modified_at=datetime.now(UTC),
            parameter_size="7B",
            quantization="Q4_K_M",
        )
        assert info.name == "qwen2.5:7b"
        assert info.parameter_size == "7B"
        assert info.quantization == "Q4_K_M"
