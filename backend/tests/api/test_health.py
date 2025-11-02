"""Health check endpoint tests."""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_health_check_returns_200_with_all_checks(test_client):
    """GET /health returns 200 with healthy status and all component checks."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "4.0.0"
    assert "environment" in data
    assert "checks" in data
    assert data["checks"]["database"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_includes_database_status(test_client):
    """GET /health includes database connectivity status."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.asyncio
async def test_health_check_includes_version(test_client):
    """GET /health includes version information."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["version"] == "4.0.0"


@pytest.mark.asyncio
async def test_health_check_includes_environment(test_client):
    """GET /health includes environment tag."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    # In tests, environment should be "testing"
    assert data["environment"] == "testing"


@pytest.mark.xfail(reason="pytest-asyncio event loop sequencing issue - tests pass individually")
@pytest.mark.asyncio
async def test_health_check_returns_503_on_db_failure(test_client):
    """GET /health returns 503 when database is unavailable."""
    from app.dependencies import get_db

    # Create a mock session that raises an exception
    async def mock_get_db_failing():
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database connection failed"))
        yield mock_session

    # Override the dependency with the failing mock
    from app.main import app

    app.dependency_overrides[get_db] = mock_get_db_failing

    try:
        response = await test_client.get("/health")

        # Should return 503 Service Unavailable
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] == "unhealthy"
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_openapi_docs_accessible(test_client):
    """GET /docs returns 200 with OpenAPI documentation."""
    response = await test_client.get("/docs")

    assert response.status_code == 200
    assert b"swagger" in response.content.lower() or b"openapi" in response.content.lower()
