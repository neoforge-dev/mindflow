"""Tests for MCP server OAuth token verification."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.oauth.jwt import create_access_token
from mcp_server.auth import TokenVerificationError, verify_bearer_token


class TestTokenVerification:
    """Test OAuth token verification for MCP server."""

    def test_verify_valid_token(self):
        """Test verification of valid access token."""
        # Create a valid token
        token = create_access_token(
            user_id=123,
            client_id="chatgpt-client",
            scope="tasks:read tasks:write",
            expires_delta=timedelta(hours=1),
        )

        # Verify token
        payload = verify_bearer_token(f"Bearer {token}")

        # Assertions
        assert payload["sub"] == "123"
        assert payload["client_id"] == "chatgpt-client"
        assert "tasks:read" in payload["scope"]
        assert "tasks:write" in payload["scope"]
        assert payload["aud"] == "mindflow-api"

    def test_verify_token_without_bearer_prefix(self):
        """Test verification accepts token without 'Bearer ' prefix."""
        token = create_access_token(
            user_id=123,
            client_id="chatgpt-client",
            scope="tasks:read",
        )

        # Should work with or without Bearer prefix
        payload1 = verify_bearer_token(f"Bearer {token}")
        payload2 = verify_bearer_token(token)

        assert payload1["sub"] == payload2["sub"]

    def test_verify_expired_token(self):
        """Test verification fails for expired token."""
        # Create expired token
        token = create_access_token(
            user_id=123,
            client_id="chatgpt-client",
            scope="tasks:read",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        # Should raise TokenVerificationError
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_bearer_token(f"Bearer {token}")

        assert "expired" in str(exc_info.value).lower()

    def test_verify_invalid_signature(self, tmp_path):
        """Test verification fails for token with invalid signature."""
        # Create token with different private key
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Generate new private key (different from the one used by app)
        different_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        now = datetime.now(UTC)
        expire = now + timedelta(hours=1)

        payload = {
            "sub": "123",
            "client_id": "chatgpt-client",
            "scope": "tasks:read",
            "iss": "https://mindflow.example.com",
            "aud": "mindflow-api",
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }

        # Sign with different key
        invalid_token = jwt.encode(payload, different_key, algorithm="RS256")

        # Should raise TokenVerificationError
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_bearer_token(f"Bearer {invalid_token}")

        assert "signature" in str(exc_info.value).lower()

    def test_verify_missing_token(self):
        """Test verification fails for missing token."""
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_bearer_token("")

        assert "missing" in str(exc_info.value).lower() or "empty" in str(
            exc_info.value
        ).lower()

    def test_verify_malformed_token(self):
        """Test verification fails for malformed token."""
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_bearer_token("Bearer invalid.token.here")

        assert "invalid" in str(exc_info.value).lower() or "malformed" in str(
            exc_info.value
        ).lower()

    def test_verify_wrong_audience(self):
        """Test verification fails for wrong audience."""
        from app.oauth.jwks import load_public_key

        private_key_path = "app/oauth/keys/private_key.pem"
        with open(private_key_path, "rb") as f:
            private_key_pem = f.read()

        private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=default_backend()
        )

        now = datetime.now(UTC)
        expire = now + timedelta(hours=1)

        payload = {
            "sub": "123",
            "client_id": "chatgpt-client",
            "scope": "tasks:read",
            "iss": "https://mindflow.example.com",
            "aud": "wrong-audience",  # Wrong audience
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
        }

        token = jwt.encode(payload, private_key, algorithm="RS256")

        # Should raise TokenVerificationError
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_bearer_token(f"Bearer {token}")

        assert "audience" in str(exc_info.value).lower()

    def test_extract_user_id(self):
        """Test extracting user ID from token."""
        token = create_access_token(
            user_id=456,
            client_id="chatgpt-client",
            scope="tasks:read",
        )

        payload = verify_bearer_token(f"Bearer {token}")
        user_id = int(payload["sub"])

        assert user_id == 456

    def test_extract_scopes(self):
        """Test extracting scopes from token."""
        token = create_access_token(
            user_id=123,
            client_id="chatgpt-client",
            scope="tasks:read tasks:write tasks:delete",
        )

        payload = verify_bearer_token(f"Bearer {token}")
        scopes = payload["scope"].split()

        assert "tasks:read" in scopes
        assert "tasks:write" in scopes
        assert "tasks:delete" in scopes
        assert len(scopes) == 3
