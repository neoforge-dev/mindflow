"""Redis-backed CSRF token storage for OAuth consent flow.

Provides secure, distributed CSRF token storage that works across
multiple application workers/servers.
"""

import secrets
from typing import Any

from app.db.redis import get_redis_client


class CSRFTokenStorage:
    """Redis-backed CSRF token storage for OAuth authorization flow."""

    # CSRF tokens expire after 10 minutes
    TOKEN_EXPIRY_SECONDS = 600

    @staticmethod
    async def generate_token(data: dict[str, Any]) -> str:
        """
        Generate and store a new CSRF token with associated data.

        Args:
            data: Dictionary containing authorization request data

        Returns:
            Generated CSRF token string

        Raises:
            ConnectionError: If Redis connection fails
        """
        token = secrets.token_urlsafe(32)
        redis = await get_redis_client()

        # Store token data with expiry
        key = f"csrf:{token}"
        # Convert dict to flat key-value pairs for Redis hset
        await redis.hset(key, mapping=data)  # type: ignore
        await redis.expire(key, CSRFTokenStorage.TOKEN_EXPIRY_SECONDS)

        return token

    @staticmethod
    async def validate_and_consume(token: str) -> dict[str, str] | None:
        """
        Validate CSRF token and return its data, consuming it (one-time use).

        Args:
            token: CSRF token to validate

        Returns:
            Dictionary containing stored data if token is valid, None otherwise

        Raises:
            ConnectionError: If Redis connection fails
        """
        redis = await get_redis_client()
        key = f"csrf:{token}"

        # Get all data for this token
        data = await redis.hgetall(key)

        if not data:
            return None

        # Delete token (one-time use)
        await redis.delete(key)

        return data

    @staticmethod
    async def cleanup_expired() -> int:
        """
        Cleanup expired CSRF tokens (maintenance task).

        Redis automatically expires keys, so this is mainly for monitoring.

        Returns:
            Number of tokens cleaned up

        Raises:
            ConnectionError: If Redis connection fails
        """
        redis = await get_redis_client()

        # Find all CSRF token keys
        keys = []
        async for key in redis.scan_iter(match="csrf:*"):
            keys.append(key)

        # Redis TTL will handle expiry automatically
        # This is just for counting what exists
        return len(keys)
