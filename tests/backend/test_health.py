"""
Tests for the health endpoint.
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_health_returns_200():
    """Test that GET /health returns HTTP 200."""
    async with httpx.AsyncClient(app=None, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_structure():
    """Test that health endpoint returns correct response structure."""
    async with httpx.AsyncClient(app=None, base_url="http://testserver") as client:
        response = await client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"
        assert "service" in data
        assert data["service"] == "forgeai"
        assert "version" in data


@pytest.mark.asyncio
async def test_health_response_content_type():
    """Test that health endpoint returns JSON content type."""
    async with httpx.AsyncClient(app=None, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_health_database_status():
    """Test that health endpoint reports database status."""
    async with httpx.AsyncClient(app=None, base_url="http://testserver") as client:
        response = await client.get("/health")
        data = response.json()

        assert "database" in data
        assert isinstance(data["database"], dict)
        assert "status" in data["database"]


@pytest.mark.asyncio
async def test_health_uptime():
    """Test that health endpoint includes uptime information."""
    async with httpx.AsyncClient(app=None, base_url="http://testserver") as client:
        response = await client.get("/health")
        data = response.json()

        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))
        assert data["uptime"] >= 0


@pytest.mark.asyncio
async def test_health_timestamp():
    """Test that health endpoint includes timestamp."""
    async with httpx.AsyncClient(app=None, base_url="http://testserver") as client:
        response = await client.get("/health")
        data = response.json()

        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)
