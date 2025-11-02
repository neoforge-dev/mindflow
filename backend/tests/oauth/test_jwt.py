"""Tests for OAuth 2.1 JWT utilities."""

import os
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.oauth.jwks import ensure_keys_exist
from app.oauth.jwt import create_access_token, decode_access_token, verify_token_claims


@pytest.fixture(autouse=True)
def setup_keys():
    """Ensure RSA keys exist before tests."""
    ensure_keys_exist()


class TestCreateAccessToken:
    """Tests for JWT access token creation."""

    def test_create_access_token_success(self):
        """Test successful JWT access token creation."""
        token = create_access_token(
            user_id=123, client_id="test-client", scope="tasks:read tasks:write"
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Token should have 3 parts (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_with_custom_expiration(self):
        """Test JWT creation with custom expiration."""
        token = create_access_token(
            user_id=456,
            client_id="test-client",
            scope="tasks:read",
            expires_delta=timedelta(minutes=30),
        )

        # Decode without verification to check claims
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["sub"] == "456"
        assert payload["client_id"] == "test-client"
        assert payload["scope"] == "tasks:read"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_includes_required_claims(self):
        """Test that JWT includes all required claims."""
        token = create_access_token(
            user_id=789, client_id="chatgpt-client", scope="openid profile email"
        )

        # Decode without verification
        payload = jwt.decode(token, options={"verify_signature": False})

        # Required claims (RFC 7519)
        assert "sub" in payload  # Subject (user ID)
        assert "client_id" in payload  # OAuth client
        assert "scope" in payload  # Granted scopes
        assert "iss" in payload  # Issuer
        assert "aud" in payload  # Audience
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at
        assert "jti" in payload  # JWT ID

        # Verify specific values
        assert payload["sub"] == "789"
        assert payload["client_id"] == "chatgpt-client"
        assert payload["scope"] == "openid profile email"
        assert payload["aud"] == "mindflow-api"

    def test_create_access_token_uses_rs256_algorithm(self):
        """Test that JWT uses RS256 algorithm."""
        token = create_access_token(user_id=100, client_id="test", scope="test")

        # Decode header without verification
        header = jwt.get_unverified_header(token)

        assert header["alg"] == "RS256"
        assert header["kid"] == "mindflow-2024"


class TestDecodeAccessToken:
    """Tests for JWT access token decoding and verification."""

    def test_decode_access_token_success(self):
        """Test successful JWT decoding with signature verification."""
        # Create token
        token = create_access_token(user_id=123, client_id="test-client", scope="tasks:read")

        # Decode and verify
        payload = decode_access_token(token)

        assert payload["sub"] == "123"
        assert payload["client_id"] == "test-client"
        assert payload["scope"] == "tasks:read"
        assert payload["aud"] == "mindflow-api"

    def test_decode_access_token_invalid_signature(self):
        """Test that invalid signature raises error."""
        # Create token
        token = create_access_token(user_id=123, client_id="test", scope="test")

        # Tamper with token signature (modify signature part only)
        parts = token.split(".")
        # Change middle of signature to avoid padding issues
        signature = parts[2]
        tampered_signature = signature[:10] + ("X" if signature[10] != "X" else "Y") + signature[11:]
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"

        # Should raise InvalidSignatureError or DecodeError (both acceptable for tampered tokens)
        with pytest.raises((jwt.InvalidSignatureError, jwt.DecodeError)):
            decode_access_token(tampered_token)

    def test_decode_access_token_expired(self):
        """Test that expired token raises error."""
        # Create token with negative expiration (already expired)
        token = create_access_token(
            user_id=123,
            client_id="test",
            scope="test",
            expires_delta=timedelta(seconds=-1),
        )

        # Should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_decode_access_token_wrong_audience(self):
        """Test that wrong audience raises error."""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        from app.oauth.jwt import load_private_key

        # Create token with wrong audience
        private_key_pem = load_private_key()
        private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=default_backend()
        )

        payload = {
            "sub": "123",
            "aud": "wrong-audience",  # Wrong audience
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
        }

        token = jwt.encode(payload, private_key, algorithm="RS256")  # type: ignore[arg-type]

        # Should raise InvalidAudienceError
        with pytest.raises(jwt.InvalidAudienceError):
            decode_access_token(token)

    def test_decode_access_token_malformed(self):
        """Test that malformed token raises error."""
        malformed_token = "not.a.valid.jwt"

        with pytest.raises(jwt.DecodeError):
            decode_access_token(malformed_token)


class TestVerifyTokenClaims:
    """Tests for JWT claims verification."""

    def test_verify_token_claims_success(self):
        """Test successful token claims verification."""
        token = create_access_token(
            user_id=123, client_id="test", scope="tasks:read tasks:write"
        )

        payload = verify_token_claims(token, required_scope="tasks:read")

        assert payload["sub"] == "123"
        assert "tasks:read" in payload["scope"]

    def test_verify_token_claims_without_scope_check(self):
        """Test claims verification without scope requirement."""
        token = create_access_token(user_id=456, client_id="test", scope="openid")

        payload = verify_token_claims(token, required_scope=None)

        assert payload["sub"] == "456"

    def test_verify_token_claims_missing_scope(self):
        """Test that missing required scope raises error."""
        token = create_access_token(user_id=789, client_id="test", scope="tasks:read")

        # Require scope that's not in token
        with pytest.raises(PermissionError, match="missing required scope"):
            verify_token_claims(token, required_scope="tasks:write")

    def test_verify_token_claims_multiple_scopes(self):
        """Test scope verification with multiple scopes."""
        token = create_access_token(
            user_id=100, client_id="test", scope="tasks:read tasks:write openid profile"
        )

        # Each individual scope should be verifiable
        verify_token_claims(token, required_scope="tasks:read")
        verify_token_claims(token, required_scope="tasks:write")
        verify_token_claims(token, required_scope="openid")
        verify_token_claims(token, required_scope="profile")

    def test_verify_token_claims_invalid_token(self):
        """Test that invalid token raises error."""
        with pytest.raises(jwt.InvalidTokenError):
            verify_token_claims("invalid.token.here", required_scope="tasks:read")


class TestJWTSecurity:
    """Tests for JWT security features."""

    def test_jwt_unique_identifiers(self):
        """Test that each JWT has unique identifier (jti claim)."""
        token1 = create_access_token(user_id=1, client_id="test", scope="test")
        token2 = create_access_token(user_id=1, client_id="test", scope="test")

        payload1 = jwt.decode(token1, options={"verify_signature": False})
        payload2 = jwt.decode(token2, options={"verify_signature": False})

        # JTI should be different even for identical parameters
        assert payload1["jti"] != payload2["jti"]

    def test_jwt_issuer_claim(self):
        """Test that JWT includes issuer claim."""
        token = create_access_token(user_id=123, client_id="test", scope="test")
        payload = jwt.decode(token, options={"verify_signature": False})

        # Should have issuer claim (from env or default)
        assert "iss" in payload
        expected_issuer = os.getenv("OAUTH_ISSUER", "https://mindflow.example.com")
        assert payload["iss"] == expected_issuer

    def test_jwt_expiration_claim(self):
        """Test that JWT expiration is set correctly."""
        token = create_access_token(
            user_id=123, client_id="test", scope="test", expires_delta=timedelta(hours=2)
        )
        payload = jwt.decode(token, options={"verify_signature": False})

        # Expiration should be ~2 hours from now
        import time

        current_time = time.time()
        expected_expiration = current_time + (2 * 3600)  # 2 hours in seconds

        # Allow 5 second tolerance for test execution time
        assert abs(payload["exp"] - expected_expiration) < 5

    def test_jwt_signature_verification_required(self):
        """Test that signature verification is enforced."""
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Generate different key pair
        different_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Create token with different key
        payload = {
            "sub": "123",
            "aud": "mindflow-api",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
        }

        token = jwt.encode(payload, different_key, algorithm="RS256")  # type: ignore[arg-type]

        # Should fail verification (signed with different key)
        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(token)
