"""Tests for OAuth 2.1 discovery endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_oauth_discovery_endpoint_returns_required_metadata():
    """Test that discovery endpoint returns all required OAuth 2.1 metadata."""
    response = client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    data = response.json()

    # Required fields per RFC 8414
    assert "issuer" in data
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "jwks_uri" in data

    # Verify endpoint URLs
    assert data["authorization_endpoint"].endswith("/oauth/authorize")
    assert data["token_endpoint"].endswith("/oauth/token")
    assert data["jwks_uri"].endswith("/.well-known/jwks.json")


@pytest.mark.asyncio
async def test_oauth_discovery_includes_required_scopes():
    """Test that discovery endpoint lists all required scopes for Apps SDK."""
    response = client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    data = response.json()

    scopes = data["scopes_supported"]
    assert "tasks:read" in scopes
    assert "tasks:write" in scopes
    assert "openid" in scopes
    assert "profile" in scopes


@pytest.mark.asyncio
async def test_oauth_discovery_supports_pkce():
    """Test that PKCE (S256) is supported for security."""
    response = client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    data = response.json()

    assert "code_challenge_methods_supported" in data
    assert "S256" in data["code_challenge_methods_supported"]


@pytest.mark.asyncio
async def test_oauth_discovery_supports_authorization_code_flow():
    """Test that authorization code grant type is supported."""
    response = client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    data = response.json()

    assert "authorization_code" in data["grant_types_supported"]
    assert "refresh_token" in data["grant_types_supported"]
    assert "code" in data["response_types_supported"]


@pytest.mark.asyncio
async def test_oauth_discovery_issuer_matches_base_url():
    """Test that issuer URL matches configured API base URL."""
    response = client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    data = response.json()

    # Issuer should match the configured base URL
    assert data["issuer"] == "http://localhost:8000"
