"""Pytest fixtures for the ForgeAI test suite."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Return test-specific application settings."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/forgeai_test",
        DATABASE_ECHO=False,
        DEBUG=True,
        APP_ENV="development",
        LOG_LEVEL="DEBUG",
        LOG_FORMAT="console",
    )


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing FastAPI endpoints.

    Uses the ASGI transport to test the app without starting a real server.
    """
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
