"""Unit tests for password hashing and JWT token functions."""

from datetime import timedelta

import pytest
from jose import JWTError

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_generates_unique_salt_each_time(self):
        """Same password hashed twice produces different hashes due to unique salt."""
        password = "mySecurePassword123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes due to unique salt
        assert hash1 != hash2
        # Both should be valid bcrypt hashes (start with $2b$)
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_verify_password_returns_true_for_correct_password(self):
        """Correct password verifies successfully against its hash."""
        password = "correctPassword123"
        hashed = hash_password(password)

        # Verification should succeed
        assert verify_password(password, hashed) is True

    def test_verify_password_returns_false_for_wrong_password(self):
        """Wrong password verification returns False without raising exception."""
        correct_password = "correctPassword123"
        wrong_password = "wrongPassword456"
        hashed = hash_password(correct_password)

        # Verification should fail
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_handles_invalid_hash_gracefully(self):
        """Invalid hash format returns False instead of raising exception."""
        password = "somePassword123"
        invalid_hash = "not-a-valid-bcrypt-hash"

        # Should return False, not crash
        assert verify_password(password, invalid_hash) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token_returns_valid_jwt(self):
        """Generated JWT can be decoded and contains expected payload."""
        data = {"sub": "user_123"}

        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Should be decodable
        decoded = decode_access_token(token)
        assert decoded["sub"] == "user_123"

    def test_create_access_token_includes_expiration(self):
        """JWT includes exp claim set to future timestamp."""
        import time

        data = {"sub": "user_123"}
        expires_delta = timedelta(hours=1)

        token = create_access_token(data, expires_delta=expires_delta)
        decoded = decode_access_token(token)

        # Should have expiration in future
        assert "exp" in decoded
        assert decoded["exp"] > time.time()

    def test_create_access_token_includes_issued_at(self):
        """JWT includes iat claim for issued timestamp."""
        data = {"sub": "user_123"}

        token = create_access_token(data)
        decoded = decode_access_token(token)

        # Should have issued_at timestamp
        assert "iat" in decoded

    def test_decode_access_token_returns_payload(self):
        """Valid JWT decodes successfully and returns original payload data."""
        data = {"sub": "user_456", "custom": "data"}

        token = create_access_token(data)
        decoded = decode_access_token(token)

        # Should return original payload
        assert decoded["sub"] == "user_456"
        assert decoded["custom"] == "data"

    def test_decode_access_token_raises_on_expired_token(self):
        """Expired JWT raises JWTError when decoded."""
        data = {"sub": "user_789"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)  # Already expired

        token = create_access_token(data, expires_delta=expires_delta)

        # Should raise JWTError on expired token
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_decode_access_token_raises_on_invalid_signature(self):
        """JWT with wrong signature raises JWTError when decoded."""
        # Create a token
        data = {"sub": "user_abc"}
        token = create_access_token(data)

        # Tamper with signature (change last character)
        tampered_token = token[:-1] + ("X" if token[-1] != "X" else "Y")

        # Should raise JWTError
        with pytest.raises(JWTError):
            decode_access_token(tampered_token)

    def test_decode_access_token_raises_on_malformed_token(self):
        """Malformed JWT raises JWTError when decoded."""
        malformed_token = "not.a.valid.jwt.token"

        # Should raise JWTError
        with pytest.raises(JWTError):
            decode_access_token(malformed_token)
