"""Pytest fixtures for the ForgeAI backend AI test suite."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.ai.config import AISettings
from app.ai.clients.ollama import OllamaClient


# ============================================================
# Event Loop
# ============================================================


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# AI Settings Fixtures
# ============================================================


@pytest.fixture
def ai_settings() -> AISettings:
    """Return test AI settings with overridden values."""
    return AISettings(
        OLLAMA_BASE_URL="http://test-ollama:11434",
        OLLAMA_TIMEOUT=5,
        OLLAMA_CONNECT_TIMEOUT=2,
        DEFAULT_MODEL="qwen2.5",
        MAX_CONTEXT_LENGTH=4096,
        MAX_RESPONSE_TOKENS=2048,
        TEMPERATURE=0.7,
        TOP_P=0.9,
        TOP_K=40,
        CONVERSATION_MAX_MESSAGES=50,
        CONVERSATION_MEMORY_ENABLED=True,
    )


@pytest.fixture
def production_ai_settings() -> AISettings:
    """Return production-like AI settings."""
    return AISettings(
        OLLAMA_BASE_URL="http://ollama:11434",
        OLLAMA_TIMEOUT=60,
        OLLAMA_CONNECT_TIMEOUT=10,
        DEFAULT_MODEL="qwen2.5",
        MAX_CONTEXT_LENGTH=8192,
        MAX_RESPONSE_TOKENS=4096,
        TEMPERATURE=0.5,
    )


# ============================================================
# Ollama Client Fixtures
# ============================================================


@pytest.fixture
def ollama_client(ai_settings: AISettings) -> OllamaClient:
    """Return an OllamaClient configured for testing."""
    return OllamaClient(
        base_url=ai_settings.OLLAMA_BASE_URL,
        timeout=ai_settings.OLLAMA_TIMEOUT,
        connect_timeout=ai_settings.OLLAMA_CONNECT_TIMEOUT,
    )


@pytest.fixture
def mock_ollama_client() -> OllamaClient:
    """Return an OllamaClient with mocked httpx client."""
    client = OllamaClient(
        base_url="http://mock-ollama:11434",
        timeout=5,
        connect_timeout=2,
    )
    return client


# ============================================================
# Mock HTTP Client Fixtures
# ============================================================


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Return a mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.is_closed = False
    return client


@pytest.fixture
def mock_httpx_response() -> AsyncMock:
    """Return a mock httpx.Response with default 200 status."""
    response = AsyncMock()
    response.status_code = 200
    response.json.return_value = {}
    return response


@pytest.fixture
def mock_httpx_404_response() -> AsyncMock:
    """Return a mock httpx.Response with 404 status."""
    response = AsyncMock()
    response.status_code = 404
    return response


@pytest.fixture
def mock_httpx_500_response() -> AsyncMock:
    """Return a mock httpx.Response with 500 status."""
    response = AsyncMock()
    response.status_code = 500
    response.aread = AsyncMock(return_value=b"Internal Server Error")
    return response


# ============================================================
# Streaming Mock Fixtures
# ============================================================


@pytest.fixture
def mock_stream_lines() -> list[str]:
    """Return mock NDJSON lines for streaming responses."""
    return [
        '{"message": {"content": "Hello"}, "done": false, "model": "qwen2.5"}',
        '{"message": {"content": " world"}, "done": false, "model": "qwen2.5"}',
        '{"message": {"content": ""}, "done": true, "model": "qwen2.5"}',
    ]


@pytest.fixture
def mock_stream_response(mock_stream_lines: list[str]) -> AsyncMock:
    """Return a mock streaming response context manager."""
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = MagicMock(return_value=iter(mock_stream_lines))

    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_cm


# ============================================================
# FastAPI App and Client Fixtures
# ============================================================


@pytest_asyncio.fixture
async def app():
    """Create FastAPI application instance for testing."""
    from app.main import app as fastapi_app

    yield fastapi_app


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================
# Sample Data Fixtures
# ============================================================


@pytest.fixture
def sample_chat_request() -> dict[str, Any]:
    """Return a sample chat request payload."""
    return {
        "message": "What is the capital of France?",
        "model": "qwen2.5",
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 1024,
    }


@pytest.fixture
def sample_chat_messages() -> list[dict[str, str]]:
    """Return sample messages for Ollama API."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2 + 2?"},
    ]


@pytest.fixture
def sample_ollama_tags_response() -> dict[str, Any]:
    """Return a sample Ollama /api/tags response."""
    return {
        "models": [
            {
                "name": "qwen2.5:latest",
                "model": "qwen2.5:latest",
                "size": 4_400_000_000,
                "digest": "sha256:abc123def456",
                "modified_at": "2025-01-01T00:00:00Z",
            },
            {
                "name": "llama3.2:3b",
                "model": "llama3.2:3b",
                "size": 2_200_000_000,
                "digest": "sha256:789ghi012jkl",
                "modified_at": "2025-01-02T00:00:00Z",
            },
        ]
    }


@pytest.fixture
def sample_ollama_chat_response() -> dict[str, Any]:
    """Return a sample Ollama /api/chat response."""
    return {
        "model": "qwen2.5",
        "message": {
            "role": "assistant",
            "content": "The capital of France is Paris.",
        },
        "done": True,
        "total_duration": 1_500_000_000,
        "eval_count": 15,
    }


@pytest.fixture
def sample_ollama_version_response() -> dict[str, Any]:
    """Return a sample Ollama /api/version response."""
    return {"version": "0.3.0"}


@pytest.fixture
def sample_model_info() -> dict[str, Any]:
    """Return a sample Ollama /api/show response."""
    return {
        "name": "qwen2.5:latest",
        "family": "qwen",
        "parameter_size": "7B",
        "quantization_level": "Q4_K_M",
        "template": "{{ .System }}\n{{ .Prompt }}",
        "details": {
            "families": ["qwen"],
            "parameter_size": "7B",
        },
    }
