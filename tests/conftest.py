"""
Root conftest.py - Common fixtures and test configuration for ForgeAI.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio


# ============================================================
# Event Loop Configuration
# ============================================================
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
# Application Fixtures
# ============================================================
@pytest_asyncio.fixture(scope="session")
async def app():
    """Create application instance for testing."""
    from app.main import app as fastapi_app
    yield fastapi_app


@pytest_asyncio.fixture(scope="session")
async def client(app):
    """Create async HTTP client for testing."""
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ============================================================
# Database Fixtures
# ============================================================
@pytest_asyncio.fixture(scope="session")
async def db_session():
    """Create database session for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    # Use test database URL - override in CI/CD
    test_db_url = "postgresql+asyncpg://forgeai:forgeai_dev_password@localhost:5432/forgeai_test"

    engine = create_async_engine(test_db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def setup_db(db_session):
    """Set up test database tables."""
    from app.models.base import Base

    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================
# Mock Fixtures
# ============================================================
@pytest.fixture
def mock_settings():
    """Mock application settings."""
    from app.config import Settings

    return Settings(
        APP_ENV="testing",
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///test.db",
        JWT_SECRET_KEY="test-secret-key",
    )


# ============================================================
# Sample Data Fixtures
# ============================================================
@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "email": "test@forgeai.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_login():
    """Sample login credentials for testing."""
    return {
        "username": "test@forgeai.com",
        "password": "TestPassword123!",
    }


# ============================================================
# Utility Fixtures
# ============================================================
@pytest.fixture
def random_string():
    """Generate a random string for unique test data."""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def current_timestamp():
    """Get current timestamp."""
    import time
    return time.time()
