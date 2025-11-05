"""Tests for Redis-backed CSRF token storage."""

from unittest.mock import AsyncMock, patch

import pytest

from app.oauth.csrf import CSRFTokenStorage


@pytest.mark.asyncio
async def test_generate_token_creates_token():
    """Test that generate_token creates a token and stores data."""
    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()

    with patch("app.oauth.csrf.get_redis_client", return_value=mock_redis):
        data = {
            "client_id": "test_client",
            "user_id": "123",
            "scope": "tasks:read tasks:write",
        }

        token = await CSRFTokenStorage.generate_token(data)

        # Verify token was generated
        assert token is not None
        assert len(token) > 0

        # Verify data was stored in Redis
        mock_redis.hset.assert_awaited_once()
        assert mock_redis.hset.call_args[0][0] == f"csrf:{token}"
        assert mock_redis.hset.call_args[1]["mapping"] == data

        # Verify expiry was set
        mock_redis.expire.assert_awaited_once()
        assert mock_redis.expire.call_args[0][0] == f"csrf:{token}"
        assert mock_redis.expire.call_args[0][1] == CSRFTokenStorage.TOKEN_EXPIRY_SECONDS


@pytest.mark.asyncio
async def test_validate_and_consume_valid_token():
    """Test validating and consuming a valid CSRF token."""
    mock_redis = AsyncMock()
    stored_data = {
        "client_id": "test_client",
        "user_id": "123",
        "scope": "tasks:read",
    }
    mock_redis.hgetall = AsyncMock(return_value=stored_data)
    mock_redis.delete = AsyncMock()

    with patch("app.oauth.csrf.get_redis_client", return_value=mock_redis):
        token = "test_token_12345"

        data = await CSRFTokenStorage.validate_and_consume(token)

        # Verify data was retrieved
        assert data == stored_data
        mock_redis.hgetall.assert_awaited_once_with(f"csrf:{token}")

        # Verify token was deleted (one-time use)
        mock_redis.delete.assert_awaited_once_with(f"csrf:{token}")


@pytest.mark.asyncio
async def test_validate_and_consume_invalid_token():
    """Test validating an invalid/expired CSRF token."""
    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={})  # Empty dict = token not found
    mock_redis.delete = AsyncMock()

    with patch("app.oauth.csrf.get_redis_client", return_value=mock_redis):
        token = "invalid_token"

        data = await CSRFTokenStorage.validate_and_consume(token)

        # Verify None was returned
        assert data is None
        mock_redis.hgetall.assert_awaited_once_with(f"csrf:{token}")

        # Verify delete was not called (no token to delete)
        mock_redis.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_validate_and_consume_is_one_time_use():
    """Test that tokens can only be used once."""
    mock_redis = AsyncMock()
    stored_data = {"client_id": "test_client"}

    # First call returns data, second call returns empty
    mock_redis.hgetall = AsyncMock(side_effect=[stored_data, {}])
    mock_redis.delete = AsyncMock()

    with patch("app.oauth.csrf.get_redis_client", return_value=mock_redis):
        token = "test_token"

        # First use succeeds
        data1 = await CSRFTokenStorage.validate_and_consume(token)
        assert data1 == stored_data
        assert mock_redis.delete.await_count == 1

        # Second use fails
        data2 = await CSRFTokenStorage.validate_and_consume(token)
        assert data2 is None


@pytest.mark.asyncio
async def test_cleanup_expired_counts_tokens():
    """Test cleanup_expired counts existing tokens."""
    mock_redis = AsyncMock()

    # Mock scan_iter to return 3 token keys
    async def mock_scan_iter(match):
        for key in ["csrf:token1", "csrf:token2", "csrf:token3"]:
            yield key

    mock_redis.scan_iter = mock_scan_iter

    with patch("app.oauth.csrf.get_redis_client", return_value=mock_redis):
        count = await CSRFTokenStorage.cleanup_expired()

        # Verify count matches number of keys
        assert count == 3


@pytest.mark.asyncio
async def test_generate_token_uses_secure_random():
    """Test that generated tokens are sufficiently random."""
    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()

    with patch("app.oauth.csrf.get_redis_client", return_value=mock_redis):
        data = {"client_id": "test"}

        # Generate multiple tokens
        tokens = set()
        for _ in range(10):
            token = await CSRFTokenStorage.generate_token(data)
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 10

        # Tokens should be long enough (32 bytes URL-safe = ~43 chars)
        for token in tokens:
            assert len(token) >= 40
