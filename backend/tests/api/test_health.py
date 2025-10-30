"""Health check endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_health_check_returns_200(test_client):
    """GET /health returns 200 with healthy status."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"


@pytest.mark.asyncio
async def test_openapi_docs_accessible(test_client):
    """GET /docs returns 200 with OpenAPI documentation."""
    response = await test_client.get("/docs")

    assert response.status_code == 200
    assert b"swagger" in response.content.lower() or b"openapi" in response.content.lower()
