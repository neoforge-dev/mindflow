"""Tests for OAuth 2.1 Token Endpoint (/oauth/token)."""

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import pytest

from app.oauth.crud import OAuthAuthorizationCodeCRUD, OAuthClientCRUD, OAuthRefreshTokenCRUD
from app.oauth.jwks import ensure_keys_exist
from app.oauth.jwt import decode_access_token


@pytest.fixture(autouse=True)
def setup_keys():
    """Ensure RSA keys exist before tests."""
    ensure_keys_exist()


@pytest.fixture
async def test_oauth_client(db_session):
    """Create test OAuth client."""
    import secrets as sec

    client = await OAuthClientCRUD.create(
        db_session,
        {
            "client_id": f"test-client-{sec.token_hex(8)}",
            "client_secret": "test-client-secret",
            "client_name": "Test Client",
            "redirect_uris": "https://example.com/callback",
            "allowed_scopes": "tasks:read tasks:write openid profile email",
            "is_active": True,
        },
    )
    return client


@pytest.fixture
async def test_authorization_code(db_session, test_oauth_client, test_user):
    """Create test authorization code with PKCE."""
    # Generate PKCE challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )

    # Convert UUID to int for OAuth tables (workaround for model mismatch)
    user_id_int = hash(str(test_user.id)) & 0x7FFFFFFF  # Convert UUID to positive int32

    auth_code = await OAuthAuthorizationCodeCRUD.create(
        db_session,
        client_id=test_oauth_client.client_id,
        user_id=user_id_int,
        redirect_uri="https://example.com/callback",
        scope="tasks:read tasks:write",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )

    # Attach code_verifier and original user_id for testing
    auth_code.code_verifier = code_verifier
    auth_code.original_user_id = test_user.id
    return auth_code


class TestTokenEndpointAuthorizationCodeGrant:
    """Tests for authorization_code grant type."""

    @pytest.mark.asyncio
    async def test_token_exchange_success(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test successful authorization code exchange for tokens."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "refresh_token" in data
        assert "scope" in data

        # Verify token type and expiration
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600  # 1 hour
        assert data["scope"] == "tasks:read tasks:write"

        # Verify access token is valid JWT
        payload = decode_access_token(data["access_token"])
        assert str(payload["sub"]) == str(test_authorization_code.user_id)
        assert payload["client_id"] == test_oauth_client.client_id
        assert payload["scope"] == "tasks:read tasks:write"

    @pytest.mark.asyncio
    async def test_token_exchange_missing_code(self, test_client, test_oauth_client):
        """Test token exchange fails without authorization code."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": "test-verifier",
            },
        )

        assert response.status_code == 400
        assert "Missing required parameter: code" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_missing_redirect_uri(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test token exchange fails without redirect_uri."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response.status_code == 400
        assert "Missing required parameter: redirect_uri" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_missing_code_verifier(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test token exchange fails without PKCE code_verifier."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
            },
        )

        assert response.status_code == 400
        assert "Missing required parameter: code_verifier" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_invalid_client_credentials(
        self, test_client, test_authorization_code
    ):
        """Test token exchange fails with invalid client credentials."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": "invalid-client",
                "client_secret": "invalid-secret",
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response.status_code == 401
        assert "Client authentication failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_wrong_client_secret(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test token exchange fails with wrong client secret."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": "wrong-secret",
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_exchange_invalid_code(self, test_client, test_oauth_client):
        """Test token exchange fails with invalid authorization code."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid-code",
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": "test-verifier",
            },
        )

        assert response.status_code == 400
        assert "Invalid authorization code" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_wrong_redirect_uri(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test token exchange fails with wrong redirect_uri."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://wrong.com/callback",  # Wrong URI
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response.status_code == 400
        assert "Invalid authorization code" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_invalid_pkce_verifier(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test token exchange fails with invalid PKCE code_verifier."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": "wrong-verifier-that-wont-match-challenge-hash",
            },
        )

        assert response.status_code == 400
        assert "PKCE verification failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_expired_code(
        self, test_client, test_oauth_client, db_session, test_user
    ):
        """Test token exchange fails with expired authorization code."""
        # Create expired authorization code
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        # Convert UUID to int for OAuth tables
        user_id_int = hash(str(test_user.id)) & 0x7FFFFFFF

        from app.oauth.models import OAuthAuthorizationCode

        expired_code = OAuthAuthorizationCode(
            code=secrets.token_urlsafe(32),
            client_id=test_oauth_client.client_id,
            user_id=user_id_int,
            redirect_uri="https://example.com/callback",
            scope="tasks:read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.now(UTC) - timedelta(minutes=1),  # Expired
            is_used=False,
        )

        db_session.add(expired_code)
        await db_session.commit()

        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": expired_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": code_verifier,
            },
        )

        assert response.status_code == 400
        assert "Invalid authorization code" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_token_exchange_used_code_replay_attack(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test that authorization code can only be used once (replay attack prevention)."""
        # First request - should succeed
        response1 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response1.status_code == 200

        # Second request with same code - should fail
        response2 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response2.status_code == 400
        assert "Invalid authorization code" in response2.json()["detail"]


class TestTokenEndpointRefreshTokenGrant:
    """Tests for refresh_token grant type."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, test_client, test_oauth_client, test_authorization_code
    ):
        """Test successful refresh token exchange for new access token."""
        # First get tokens via authorization code
        response1 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        assert response1.status_code == 200
        refresh_token = response1.json()["refresh_token"]

        # Use refresh token to get new access token
        response2 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
            },
        )

        assert response2.status_code == 200
        data = response2.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "refresh_token" in data
        assert "scope" in data

        # Verify same refresh token returned (no rotation)
        assert data["refresh_token"] == refresh_token

        # Verify new access token is valid
        payload = decode_access_token(data["access_token"])
        assert str(payload["sub"]) == str(test_authorization_code.user_id)

    @pytest.mark.asyncio
    async def test_refresh_token_missing_token(self, test_client, test_oauth_client):
        """Test refresh token grant fails without refresh_token parameter."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
            },
        )

        assert response.status_code == 400
        assert "Missing required parameter: refresh_token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(self, test_client, test_oauth_client):
        """Test refresh token grant fails with invalid token."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "invalid-refresh-token",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
            },
        )

        assert response.status_code == 400
        assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_wrong_client(
        self, test_client, test_oauth_client, test_authorization_code, db_session
    ):
        """Test refresh token fails when used by different client."""
        # Get refresh token
        response1 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        refresh_token = response1.json()["refresh_token"]

        # Create different OAuth client
        import secrets as sec

        different_client = await OAuthClientCRUD.create(
            db_session,
            {
                "client_id": f"different-client-{sec.token_hex(8)}",
                "client_secret": "different-secret",
                "client_name": "Different Client",
                "redirect_uris": "https://other.com/callback",
                "allowed_scopes": "tasks:read",
                "is_active": True,
            },
        )

        # Try to use refresh token with different client
        response2 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": different_client.client_id,
                "client_secret": different_client.client_secret,
            },
        )

        assert response2.status_code == 400
        assert "Invalid refresh token" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_revoked(
        self, test_client, test_oauth_client, test_authorization_code, db_session
    ):
        """Test refresh token fails when revoked."""
        # Get refresh token
        response1 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
                "code_verifier": test_authorization_code.code_verifier,
            },
        )

        refresh_token = response1.json()["refresh_token"]

        # Revoke the refresh token
        await OAuthRefreshTokenCRUD.revoke(db_session, refresh_token)

        # Try to use revoked token
        response2 = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
            },
        )

        assert response2.status_code == 400
        assert "Invalid refresh token" in response2.json()["detail"]


class TestTokenEndpointErrors:
    """Tests for token endpoint error handling."""

    @pytest.mark.asyncio
    async def test_unsupported_grant_type(self, test_client, test_oauth_client):
        """Test that unsupported grant type returns error."""
        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "password",  # Unsupported
                "client_id": test_oauth_client.client_id,
                "client_secret": test_oauth_client.client_secret,
            },
        )

        assert response.status_code == 400
        assert "Unsupported grant type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_inactive_client(
        self, test_client, db_session, test_authorization_code, test_user
    ):
        """Test that inactive OAuth client cannot get tokens."""
        # Create inactive client
        import secrets as sec

        inactive_client = await OAuthClientCRUD.create(
            db_session,
            {
                "client_id": f"inactive-client-{sec.token_hex(8)}",
                "client_secret": "inactive-secret",
                "client_name": "Inactive Client",
                "redirect_uris": "https://example.com/callback",
                "allowed_scopes": "tasks:read",
                "is_active": False,  # Inactive
            },
        )

        response = await test_client.post(
            "/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": test_authorization_code.code,
                "redirect_uri": "https://example.com/callback",
                "client_id": inactive_client.client_id,
                "client_secret": inactive_client.client_secret,
                "code_verifier": "test-verifier",
            },
        )

        assert response.status_code == 401
        assert "Client authentication failed" in response.json()["detail"]
