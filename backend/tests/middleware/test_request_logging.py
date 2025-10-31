"""Tests for request logging middleware."""

import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.middleware.request_logging import RequestIDMiddleware


class TestRequestIDMiddleware:
    """Test request ID middleware functionality."""

    @pytest_asyncio.fixture
    async def app_with_logging(self) -> FastAPI:
        """Create test app with request ID middleware."""
        app = FastAPI()

        # Add middleware
        app.add_middleware(RequestIDMiddleware)

        # Add exception handler to convert errors to responses
        @app.exception_handler(ValueError)
        async def value_error_handler(_request: Request, _exc: ValueError) -> JSONResponse:
            """Handle ValueError."""
            return JSONResponse(status_code=500, content={"error": "Internal error"})

        @app.get("/test")
        async def test_endpoint() -> dict[str, str]:
            """Test endpoint."""
            return {"message": "success"}

        @app.get("/error")
        async def error_endpoint() -> None:
            """Endpoint that raises an error."""
            raise ValueError("Test error")

        return app

    @pytest.mark.asyncio
    async def test_request_id_added_to_response_headers(
        self, app_with_logging: FastAPI
    ) -> None:
        """Test that X-Request-ID header is added to response."""
        async with AsyncClient(
            transport=ASGITransport(app=app_with_logging), base_url="http://test"
        ) as client:
            response = await client.get("/test")
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers
            # Validate UUID format
            request_id = response.headers["X-Request-ID"]
            uuid.UUID(request_id)  # Should not raise

    @pytest.mark.asyncio
    async def test_existing_request_id_preserved(
        self, app_with_logging: FastAPI
    ) -> None:
        """Test that existing X-Request-ID in request is preserved."""
        custom_id = str(uuid.uuid4())
        async with AsyncClient(
            transport=ASGITransport(app=app_with_logging), base_url="http://test"
        ) as client:
            response = await client.get("/test", headers={"X-Request-ID": custom_id})
            assert response.status_code == 200
            assert response.headers["X-Request-ID"] == custom_id

    @pytest.mark.asyncio
    async def test_different_requests_get_different_ids(
        self, app_with_logging: FastAPI
    ) -> None:
        """Test that different requests get different request IDs."""
        async with AsyncClient(
            transport=ASGITransport(app=app_with_logging), base_url="http://test"
        ) as client:
            response1 = await client.get("/test")
            response2 = await client.get("/test")

            id1 = response1.headers["X-Request-ID"]
            id2 = response2.headers["X-Request-ID"]

            assert id1 != id2

    @pytest.mark.asyncio
    async def test_request_id_present_on_error_response(
        self, app_with_logging: FastAPI
    ) -> None:
        """Test that X-Request-ID is present even when endpoint errors."""
        async with AsyncClient(
            transport=ASGITransport(app=app_with_logging), base_url="http://test"
        ) as client:
            response = await client.get("/error")
            # Should still have request ID even though endpoint errored
            assert response.status_code == 500
            assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_logging_handles_successful_requests(
        self, app_with_logging: FastAPI
    ) -> None:
        """Test that middleware handles successful requests."""
        async with AsyncClient(
            transport=ASGITransport(app=app_with_logging), base_url="http://test"
        ) as client:
            response = await client.get("/test")
            assert response.status_code == 200
            assert response.json() == {"message": "success"}
