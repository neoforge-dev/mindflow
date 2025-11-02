"""Tests for OAuth 2.1 authorization endpoint."""

import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.oauth.crud import OAuthAuthorizationCodeCRUD, OAuthClientCRUD
from app.oauth.models import OAuthClient


@pytest_asyncio.fixture
async def oauth_client(db_session: AsyncSession) -> OAuthClient:
    """Create a test OAuth client."""
    # Use a unique client_id for each test to avoid conflicts
    unique_client_id = f"test_client_{secrets.token_urlsafe(8)}"

    client_data = {
        "client_id": unique_client_id,
        "client_secret": secrets.token_urlsafe(32),
        "client_name": "Test ChatGPT App",
        "redirect_uris": "https://chat.openai.com/aip/callback,https://chatgpt.com/callback",
        "allowed_scopes": "tasks:read tasks:write openid profile email",
        "grant_types": "authorization_code,refresh_token",
        "response_types": "code",
        "token_endpoint_auth_method": "client_secret_post",
        "logo_uri": "https://example.com/logo.png",
        "is_active": True,
    }

    client = await OAuthClientCRUD.create(db_session, client_data)
    return client


@pytest.mark.asyncio
async def test_authorize_get_success_shows_consent_screen(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
    db_session: AsyncSession,
):
    """Test successful authorization request shows consent screen."""
    # Prepare authorization request parameters
    params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read tasks:write openid",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",  # Mock user authentication
    }

    # Make authorization request
    response = await test_client.get("/oauth/authorize", params=params)

    # Should return consent screen HTML
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Authorization Request" in response.text
    assert oauth_client.client_name in response.text
    assert "tasks:read" in response.text or "View your tasks" in response.text
    assert "csrf_token" in response.text


@pytest.mark.asyncio
async def test_authorize_get_invalid_client_shows_error(
    test_client: AsyncClient,
):
    """Test authorization request with invalid client shows error page."""
    params = {
        "client_id": "invalid_client_id",
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    response = await test_client.get("/oauth/authorize", params=params)

    # Should return error page (not redirect)
    assert response.status_code == 400
    assert "Invalid Client" in response.text


@pytest.mark.asyncio
async def test_authorize_get_invalid_redirect_uri_shows_error(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test authorization request with invalid redirect_uri shows error page."""
    params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://evil.com/callback",  # Not registered
        "response_type": "code",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    response = await test_client.get("/oauth/authorize", params=params)

    # Should return error page (not redirect for security)
    assert response.status_code == 400
    assert "Invalid Redirect URI" in response.text


@pytest.mark.asyncio
async def test_authorize_get_invalid_scope_redirects_with_error(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test authorization request with invalid scope redirects with error."""
    params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read invalid_scope",  # invalid_scope not allowed
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    response = await test_client.get("/oauth/authorize", params=params, follow_redirects=False)

    # Should redirect to redirect_uri with error
    assert response.status_code == 303
    assert response.headers["location"].startswith("https://chat.openai.com/aip/callback")

    # Parse redirect URL
    parsed = urlparse(response.headers["location"])
    query_params = parse_qs(parsed.query)

    assert query_params["error"][0] == "invalid_scope"
    assert query_params["state"][0] == "random_state_123"


@pytest.mark.asyncio
async def test_authorize_get_unsupported_response_type_redirects_with_error(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test authorization request with unsupported response_type redirects with error."""
    params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "token",  # Not supported (must be "code")
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    response = await test_client.get("/oauth/authorize", params=params, follow_redirects=False)

    # Should redirect with error
    assert response.status_code == 303

    # Parse redirect URL
    parsed = urlparse(response.headers["location"])
    query_params = parse_qs(parsed.query)

    assert query_params["error"][0] == "unsupported_response_type"
    assert query_params["state"][0] == "random_state_123"


@pytest.mark.asyncio
async def test_authorize_get_missing_user_redirects_to_login(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test authorization request without user authentication redirects to login."""
    params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        # No user_id - not authenticated
    }

    response = await test_client.get("/oauth/authorize", params=params, follow_redirects=False)

    # Should redirect to login
    assert response.status_code == 303
    assert "/api/auth/login" in response.headers["location"]
    assert "return_to" in response.headers["location"]


@pytest.mark.asyncio
async def test_authorize_post_approve_generates_authorization_code(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
    db_session: AsyncSession,
):
    """Test POST approve generates authorization code and redirects."""
    # First, get consent screen to obtain CSRF token
    get_params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read tasks:write",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    get_response = await test_client.get("/oauth/authorize", params=get_params)
    assert get_response.status_code == 200

    # Extract CSRF token from HTML (simple extraction for testing)
    html = get_response.text
    csrf_token_start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
    csrf_token_end = html.find('"', csrf_token_start)
    csrf_token = html[csrf_token_start:csrf_token_end]

    # Submit approval form
    form_data = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "scope": "tasks:read tasks:write",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "approve": "true",
        "csrf_token": csrf_token,
    }

    response = await test_client.post("/oauth/authorize", data=form_data, follow_redirects=False)

    # Should redirect to redirect_uri with authorization code
    assert response.status_code == 303
    assert response.headers["location"].startswith("https://chat.openai.com/aip/callback")

    # Parse redirect URL
    parsed = urlparse(response.headers["location"])
    query_params = parse_qs(parsed.query)

    assert "code" in query_params
    assert query_params["state"][0] == "random_state_123"

    # Verify authorization code exists in database
    auth_code = await OAuthAuthorizationCodeCRUD.get_by_code(db_session, query_params["code"][0])
    assert auth_code is not None
    assert auth_code.client_id == oauth_client.client_id
    assert auth_code.user_id == 1
    assert auth_code.scope == "tasks:read tasks:write"
    assert auth_code.code_challenge == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    assert auth_code.code_challenge_method == "S256"
    assert auth_code.is_used is False
    assert auth_code.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_authorize_post_deny_redirects_with_error(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test POST deny redirects with access_denied error."""
    # First, get consent screen to obtain CSRF token
    get_params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    get_response = await test_client.get("/oauth/authorize", params=get_params)
    assert get_response.status_code == 200

    # Extract CSRF token
    html = get_response.text
    csrf_token_start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
    csrf_token_end = html.find('"', csrf_token_start)
    csrf_token = html[csrf_token_start:csrf_token_end]

    # Submit denial form
    form_data = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "approve": "false",
        "csrf_token": csrf_token,
    }

    response = await test_client.post("/oauth/authorize", data=form_data, follow_redirects=False)

    # Should redirect with access_denied error
    assert response.status_code == 303

    # Parse redirect URL
    parsed = urlparse(response.headers["location"])
    query_params = parse_qs(parsed.query)

    assert query_params["error"][0] == "access_denied"
    assert query_params["state"][0] == "random_state_123"


@pytest.mark.asyncio
async def test_authorize_post_invalid_csrf_token_redirects_with_error(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test POST with invalid CSRF token redirects with error."""
    form_data = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "approve": "true",
        "csrf_token": "invalid_csrf_token",
    }

    response = await test_client.post("/oauth/authorize", data=form_data, follow_redirects=False)

    # Should redirect with access_denied error
    assert response.status_code == 303

    # Parse redirect URL
    parsed = urlparse(response.headers["location"])
    query_params = parse_qs(parsed.query)

    assert query_params["error"][0] == "access_denied"
    assert "Invalid or expired CSRF token" in query_params["error_description"][0]


@pytest.mark.asyncio
async def test_authorize_post_csrf_data_mismatch_redirects_with_error(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
):
    """Test POST with CSRF data mismatch redirects with error."""
    # Get consent screen to obtain valid CSRF token
    get_params = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "response_type": "code",
        "scope": "tasks:read",
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "user_id": "1",
    }

    get_response = await test_client.get("/oauth/authorize", params=get_params)
    assert get_response.status_code == 200

    # Extract CSRF token
    html = get_response.text
    csrf_token_start = html.find('name="csrf_token" value="') + len('name="csrf_token" value="')
    csrf_token_end = html.find('"', csrf_token_start)
    csrf_token = html[csrf_token_start:csrf_token_end]

    # Submit form with modified scope (CSRF data mismatch)
    form_data = {
        "client_id": oauth_client.client_id,
        "redirect_uri": "https://chat.openai.com/aip/callback",
        "scope": "tasks:write",  # Different from GET request
        "state": "random_state_123",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        "code_challenge_method": "S256",
        "approve": "true",
        "csrf_token": csrf_token,
    }

    response = await test_client.post("/oauth/authorize", data=form_data, follow_redirects=False)

    # Should redirect with access_denied error
    assert response.status_code == 303

    # Parse redirect URL
    parsed = urlparse(response.headers["location"])
    query_params = parse_qs(parsed.query)

    assert query_params["error"][0] == "access_denied"
    assert "CSRF validation failed" in query_params["error_description"][0]


@pytest.mark.asyncio
async def test_authorization_code_expires_in_10_minutes(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
    db_session: AsyncSession,
):
    """Test that authorization codes expire in 10 minutes."""
    # Generate authorization code
    auth_code = await OAuthAuthorizationCodeCRUD.create(
        session=db_session,
        client_id=oauth_client.client_id,
        user_id=1,
        redirect_uri="https://chat.openai.com/aip/callback",
        scope="tasks:read",
        code_challenge="E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        code_challenge_method="S256",
    )

    # Check expiration time is approximately 10 minutes
    expected_expiry = datetime.now(UTC) + timedelta(minutes=10)
    time_diff = abs((auth_code.expires_at - expected_expiry).total_seconds())

    # Allow 5 seconds tolerance for test execution time
    assert time_diff < 5


@pytest.mark.asyncio
async def test_pkce_parameters_stored_with_authorization_code(
    test_client: AsyncClient,
    oauth_client: OAuthClient,
    db_session: AsyncSession,
):
    """Test that PKCE parameters are stored with authorization code."""
    code_challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    code_challenge_method = "S256"

    auth_code = await OAuthAuthorizationCodeCRUD.create(
        session=db_session,
        client_id=oauth_client.client_id,
        user_id=1,
        redirect_uri="https://chat.openai.com/aip/callback",
        scope="tasks:read",
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    # Verify PKCE parameters stored correctly
    assert auth_code.code_challenge == code_challenge
    assert auth_code.code_challenge_method == code_challenge_method
