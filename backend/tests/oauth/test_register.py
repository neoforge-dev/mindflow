"""Tests for OAuth 2.1 client registration endpoint (RFC 7591)."""

import pytest
import pytest_asyncio

from app.oauth.models import OAuthClient


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    """Ensure database connections are cleaned up after each test."""
    yield
    # Force garbage collection to close any lingering connections
    import gc
    gc.collect()


@pytest.fixture
def valid_registration_data():
    """Valid OAuth client registration request data."""
    return {
        "client_name": "ChatGPT MindFlow Integration",
        "redirect_uris": ["https://chat.openai.com/aip/callback"],
        "logo_uri": "https://openai.com/logo.png",
        "policy_uri": "https://openai.com/privacy",
        "tos_uri": "https://openai.com/terms",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "scope": "tasks:read tasks:write openid profile email",
    }


@pytest.mark.asyncio
async def test_register_oauth_client_success(valid_registration_data, db_session, test_client):
    """Test successful OAuth client registration."""
    response = await test_client.post("/oauth/register", json=valid_registration_data)

    assert response.status_code == 201
    data = response.json()

    # Verify response structure per RFC 7591
    assert "client_id" in data
    assert "client_secret" in data
    assert data["client_name"] == valid_registration_data["client_name"]
    assert data["redirect_uris"] == valid_registration_data["redirect_uris"]
    assert data["grant_types"] == valid_registration_data["grant_types"]
    assert data["response_types"] == valid_registration_data["response_types"]
    assert data["scope"] == valid_registration_data["scope"]
    assert "client_id_issued_at" in data

    # Verify client ID and secret are secure
    assert len(data["client_id"]) == 32  # 128-bit hex
    assert len(data["client_secret"]) == 64  # 256-bit hex

    # Verify database persistence
    from sqlalchemy import select

    result = await db_session.execute(
        select(OAuthClient).filter(OAuthClient.client_id == data["client_id"])
    )
    db_client = result.scalar_one_or_none()
    assert db_client is not None
    assert db_client.client_name == valid_registration_data["client_name"]
    assert db_client.is_active is True


@pytest.mark.skip(reason="BaseHTTPMiddleware event loop conflict - see tests/oauth/TEST_ISSUES.md")
@pytest.mark.asyncio
async def test_register_oauth_client_with_minimal_data(db_session, test_client):
    """Test registration with minimal required fields."""
    minimal_data = {
        "client_name": "Minimal Client",
        "redirect_uris": ["https://example.com/callback"],
    }

    response = await test_client.post("/oauth/register", json=minimal_data)

    assert response.status_code == 201
    data = response.json()

    # Verify defaults are applied
    assert data["grant_types"] == ["authorization_code", "refresh_token"]
    assert data["response_types"] == ["code"]
    assert "tasks:read" in data["scope"]
    assert data["logo_uri"] is None
    assert data["policy_uri"] is None


@pytest.mark.asyncio
async def test_register_oauth_client_invalid_grant_type(test_client):
    """Test registration with invalid grant type."""
    invalid_data = {
        "client_name": "Invalid Client",
        "redirect_uris": ["https://example.com/callback"],
        "grant_types": ["implicit", "client_credentials"],  # Not allowed
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 400
    assert "Invalid grant types" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_oauth_client_invalid_response_type(test_client):
    """Test registration with invalid response type."""
    invalid_data = {
        "client_name": "Invalid Client",
        "redirect_uris": ["https://example.com/callback"],
        "response_types": ["token", "id_token"],  # Not allowed
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 400
    assert "Invalid response types" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_oauth_client_invalid_scope(test_client):
    """Test registration with invalid scope."""
    invalid_data = {
        "client_name": "Invalid Client",
        "redirect_uris": ["https://example.com/callback"],
        "scope": "tasks:read tasks:delete admin:all",  # tasks:delete and admin:all not allowed
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 400
    assert "Invalid scopes" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_oauth_client_missing_client_name(test_client):
    """Test registration without required client_name."""
    invalid_data = {
        "redirect_uris": ["https://example.com/callback"],
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_register_oauth_client_missing_redirect_uris(test_client):
    """Test registration without required redirect_uris."""
    invalid_data = {
        "client_name": "Invalid Client",
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_register_oauth_client_empty_redirect_uris(test_client):
    """Test registration with empty redirect_uris array."""
    invalid_data = {
        "client_name": "Invalid Client",
        "redirect_uris": [],
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_register_oauth_client_invalid_url_format(test_client):
    """Test registration with invalid URL format."""
    invalid_data = {
        "client_name": "Invalid Client",
        "redirect_uris": ["not-a-valid-url"],
    }

    response = await test_client.post("/oauth/register", json=invalid_data)

    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.skip(reason="BaseHTTPMiddleware event loop conflict - see tests/oauth/TEST_ISSUES.md")
@pytest.mark.asyncio
async def test_client_id_uniqueness(valid_registration_data, db_session, test_client):
    """Test that each registration generates unique client IDs."""
    # Register first client
    response1 = await test_client.post("/oauth/register", json=valid_registration_data)
    client_id_1 = response1.json()["client_id"]

    # Register second client with same data
    response2 = await test_client.post("/oauth/register", json=valid_registration_data)
    client_id_2 = response2.json()["client_id"]

    # Verify unique client IDs
    assert client_id_1 != client_id_2

    # Verify both exist in database
    from sqlalchemy import select

    result = await db_session.execute(
        select(OAuthClient).filter(OAuthClient.client_id.in_([client_id_1, client_id_2]))
    )
    clients = result.scalars().all()
    assert len(clients) == 2


@pytest.mark.skip(reason="BaseHTTPMiddleware event loop conflict - see tests/oauth/TEST_ISSUES.md")
@pytest.mark.asyncio
async def test_client_secret_uniqueness(valid_registration_data, db_session, test_client):
    """Test that each registration generates unique client secrets."""
    response1 = await test_client.post("/oauth/register", json=valid_registration_data)
    secret_1 = response1.json()["client_secret"]

    response2 = await test_client.post("/oauth/register", json=valid_registration_data)
    secret_2 = response2.json()["client_secret"]

    # Verify unique secrets
    assert secret_1 != secret_2
