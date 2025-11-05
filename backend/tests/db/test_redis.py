"""Tests for Redis client module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.redis import close_redis_client, get_redis_client


@pytest.fixture(autouse=True)
async def reset_redis_client():
    """Reset global Redis client before each test."""
    import app.db.redis

    app.db.redis._redis_client = None
    yield
    app.db.redis._redis_client = None


@pytest.mark.asyncio
async def test_get_redis_client_success():
    """Test successful Redis client creation."""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.aclose = AsyncMock()

    with patch("app.db.redis.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_client

        # Get client
        client = await get_redis_client()

        # Verify client was created and tested
        assert client is not None
        assert client is mock_client
        mock_from_url.assert_awaited_once()
        mock_client.ping.assert_awaited_once()

        # Clean up
        await close_redis_client()
        mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_redis_client_connection_error():
    """Test Redis connection failure."""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))

    with patch("app.db.redis.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_client

        # Should raise ConnectionError
        with pytest.raises(ConnectionError, match="Failed to connect to Redis"):
            await get_redis_client()


@pytest.mark.asyncio
async def test_get_redis_client_reuses_instance():
    """Test that get_redis_client reuses existing instance."""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.aclose = AsyncMock()

    with patch("app.db.redis.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_client

        # Get client twice
        client1 = await get_redis_client()
        client2 = await get_redis_client()

        # Should be same instance
        assert client1 is client2
        assert client1 is mock_client
        # from_url should only be called once
        assert mock_from_url.await_count == 1

        # Clean up
        await close_redis_client()


@pytest.mark.asyncio
async def test_close_redis_client():
    """Test closing Redis client."""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.aclose = AsyncMock()

    with patch("app.db.redis.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_client

        # Get and close client
        await get_redis_client()
        await close_redis_client()

        # Verify client was closed
        mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_redis_client_when_none():
    """Test closing Redis client when none exists."""
    # Should not raise error when closing non-existent client
    await close_redis_client()
