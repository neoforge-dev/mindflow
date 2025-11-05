"""Redis client for shared state management."""

import os

from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.logging_config import get_logger

logger = get_logger(__name__)

# Global Redis client instance
_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """
    Get or create Redis client instance.

    Returns:
        Redis: Async Redis client

    Raises:
        ConnectionError: If Redis connection fails
    """
    global _redis_client

    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            _redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Test connection
            await _redis_client.ping()
            logger.info("redis_connected", url=redis_url)
        except Exception as e:
            logger.error("redis_connection_failed", url=redis_url, error=str(e))
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e

    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_disconnected")
