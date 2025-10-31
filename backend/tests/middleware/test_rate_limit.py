"""Tests for rate limiting middleware."""

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest_asyncio.fixture
    async def limiter(self) -> Limiter:
        """Create a limiter instance for testing."""
        return Limiter(key_func=get_remote_address)

    @pytest_asyncio.fixture
    async def rate_limited_app(self, limiter: Limiter) -> FastAPI:
        """Create a test app with rate limiting."""
        app = FastAPI()

        @app.get("/test-task", dependencies=[])
        @limiter.limit("5/minute")
        async def test_task_endpoint(request: Request) -> dict[str, str]:
            """Test endpoint with task rate limit (60/min in prod, 5/min in test)."""
            return {"message": "success"}

        @app.get("/test-auth", dependencies=[])
        @limiter.limit("2/minute")
        async def test_auth_endpoint(request: Request) -> dict[str, str]:
            """Test endpoint with auth rate limit (10/min in prod, 2/min in test)."""
            return {"message": "success"}

        # Add exception handler for rate limit
        @app.exception_handler(RateLimitExceeded)
        async def rate_limit_handler(
            request: Request, exc: RateLimitExceeded
        ) -> JSONResponse:
            """Handle rate limit exceeded errors."""
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        # Store limiter on app state
        app.state.limiter = limiter

        return app

    @pytest.mark.asyncio
    async def test_task_endpoint_within_limit(self, rate_limited_app: FastAPI) -> None:
        """Test that requests within rate limit are allowed."""
        async with AsyncClient(
            transport=ASGITransport(app=rate_limited_app), base_url="http://test"
        ) as client:
            # Make 3 requests within limit
            for _ in range(3):
                response = await client.get("/test-task")
                assert response.status_code == 200
                assert response.json() == {"message": "success"}

    @pytest.mark.asyncio
    async def test_task_endpoint_exceeds_limit(self, rate_limited_app: FastAPI) -> None:
        """Test that requests exceeding rate limit are blocked."""
        async with AsyncClient(
            transport=ASGITransport(app=rate_limited_app), base_url="http://test"
        ) as client:
            # Make requests up to limit
            for _ in range(5):
                response = await client.get("/test-task")
                assert response.status_code == 200

            # Next request should be rate limited
            response = await client.get("/test-task")
            assert response.status_code == 429
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_auth_endpoint_rate_limit(self, rate_limited_app: FastAPI) -> None:
        """Test that auth endpoints have stricter rate limits."""
        async with AsyncClient(
            transport=ASGITransport(app=rate_limited_app), base_url="http://test"
        ) as client:
            # Make requests up to auth limit (2/min)
            for _ in range(2):
                response = await client.get("/test-auth")
                assert response.status_code == 200

            # Next request should be rate limited
            response = await client.get("/test-auth")
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_different_endpoints_separate_limits(
        self, rate_limited_app: FastAPI
    ) -> None:
        """Test that different endpoints have independent rate limits."""
        async with AsyncClient(
            transport=ASGITransport(app=rate_limited_app), base_url="http://test"
        ) as client:
            # Exhaust auth endpoint limit
            for _ in range(2):
                response = await client.get("/test-auth")
                assert response.status_code == 200

            # Task endpoint should still work
            response = await client.get("/test-task")
            assert response.status_code == 200
            assert response.json() == {"message": "success"}

    @pytest.mark.asyncio
    async def test_rate_limit_error_response_format(
        self, rate_limited_app: FastAPI
    ) -> None:
        """Test that rate limit errors return proper format."""
        async with AsyncClient(
            transport=ASGITransport(app=rate_limited_app), base_url="http://test"
        ) as client:
            # Exhaust limit
            for _ in range(5):
                await client.get("/test-task")

            # Get rate limited response
            response = await client.get("/test-task")
            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
