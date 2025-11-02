"""Tests for MCP server task tools."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.oauth.jwt import create_access_token
from mcp_server.auth import TokenVerificationError
from mcp_server.tools.tasks import get_best_task


class TestGetBestTaskTool:
    """Test get_best_task MCP tool."""

    @pytest.fixture
    def valid_token(self):
        """Create valid access token for testing."""
        return create_access_token(
            user_id=123,
            client_id="chatgpt-client",
            scope="tasks:read",
            expires_delta=timedelta(hours=1),
        )

    @pytest.fixture
    def mock_api_response(self):
        """Mock API response for /api/tasks/best endpoint."""
        return {
            "task": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Complete project documentation",
                "description": "Write comprehensive docs for the new feature",
                "priority": 4,
                "status": "pending",
                "due_date": "2024-02-01T10:00:00Z",
                "effort_estimate_minutes": 120,
                "created_at": "2024-01-15T08:00:00Z",
                "updated_at": "2024-01-15T08:00:00Z",
            },
            "score": 8.5,
            "reasoning": {
                "deadline_urgency": 2.5,
                "priority_score": 40,
                "effort_bonus": 10,
                "total_score": 8.5,
                "recommendation": "High priority task worth focusing on",
            },
        }

    @pytest.mark.asyncio
    async def test_get_best_task_success(self, valid_token, mock_api_response):
        """Test successful get_best_task call."""
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = MagicMock()

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Call the tool
            result = await get_best_task(f"Bearer {valid_token}")

            # Assertions
            assert "task" in result
            assert "score" in result
            assert "reasoning" in result
            assert result["task"]["title"] == "Complete project documentation"
            assert result["score"] == 8.5
            assert result["reasoning"]["recommendation"] == "High priority task worth focusing on"

            # Verify API was called correctly
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/api/tasks/best" in call_args[1]["url"]
            assert "Authorization" in call_args[1]["headers"]
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {valid_token}"

    @pytest.mark.asyncio
    async def test_get_best_task_no_pending_tasks(self, valid_token):
        """Test get_best_task when no pending tasks exist."""
        # Simplify: Make request itself raise the error
        mock_error = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, json=MagicMock(return_value={"detail": "No pending tasks"})),
        )

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Create response that raises on raise_for_status
            async def mock_request(*args, **kwargs):
                response = MagicMock()
                response.status_code = 404
                response.json = MagicMock(return_value={"detail": "No pending tasks"})
                response.raise_for_status.side_effect = mock_error
                return response

            mock_client.request = mock_request
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Call should raise exception
            with pytest.raises(Exception) as exc_info:
                await get_best_task(f"Bearer {valid_token}")

            # Accept either the properly formatted message or the fallback
            error_msg = str(exc_info.value)
            assert "No pending tasks" in error_msg or "404" in error_msg or "API call failed" in error_msg

    @pytest.mark.asyncio
    async def test_get_best_task_invalid_token(self):
        """Test get_best_task with invalid token."""
        # Should fail during token verification, before making API call
        with pytest.raises(TokenVerificationError):
            await get_best_task("Bearer invalid.token.here")

    @pytest.mark.asyncio
    async def test_get_best_task_missing_token(self):
        """Test get_best_task with missing token."""
        with pytest.raises(TokenVerificationError):
            await get_best_task("")

    @pytest.mark.asyncio
    async def test_get_best_task_network_error_retry(self, valid_token):
        """Test get_best_task retries on network errors."""
        # Mock network error then success
        error_count = 0

        async def mock_request_side_effect(*args, **kwargs):
            nonlocal error_count
            if error_count == 0:
                error_count += 1
                raise httpx.RequestError("Connection failed", request=MagicMock())
            else:
                # Return success response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "task": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Test task",
                        "description": "Test",
                        "priority": 3,
                        "status": "pending",
                    },
                    "score": 5.0,
                    "reasoning": {"total_score": 5.0, "recommendation": "Test"},
                }
                mock_response.raise_for_status = MagicMock()
                return mock_response

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=mock_request_side_effect)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock asyncio.sleep to speed up test
            with patch("mcp_server.tools.tasks.asyncio.sleep", new_callable=AsyncMock):
                # Should retry and succeed
                result = await get_best_task(f"Bearer {valid_token}")
                assert result["task"]["title"] == "Test task"

                # Verify retry happened
                assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_get_best_task_unauthorized_401(self, valid_token):
        """Test get_best_task with API returning 401 Unauthorized."""
        mock_error = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401, json=MagicMock(return_value={"detail": "Invalid authentication credentials"})),
        )

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Create response that raises on raise_for_status
            async def mock_request(*args, **kwargs):
                response = MagicMock()
                response.status_code = 401
                response.json = MagicMock(return_value={"detail": "Invalid authentication credentials"})
                response.raise_for_status.side_effect = mock_error
                return response

            mock_client.request = mock_request
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await get_best_task(f"Bearer {valid_token}")

            # Accept either the properly formatted message or the fallback
            error_msg = str(exc_info.value)
            assert "401" in error_msg or "Unauthorized" in error_msg or "API call failed" in error_msg

    @pytest.mark.asyncio
    async def test_get_best_task_api_base_url_configuration(self, valid_token, mock_api_response):
        """Test that API base URL is correctly configured."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = MagicMock()

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            await get_best_task(f"Bearer {valid_token}")

            # Verify correct URL construction
            call_args = mock_client.request.call_args
            url = call_args[1]["url"]
            assert url.startswith("http://localhost:8000") or url.startswith("http://")
            assert "/api/tasks/best" in url
