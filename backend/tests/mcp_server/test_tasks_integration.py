"""Integration tests for task tools with component rendering."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.oauth.jwt import create_access_token
from mcp_server.tools.tasks import get_best_task


class TestGetBestTaskIntegration:
    """Test get_best_task with component rendering."""

    @pytest.fixture
    def valid_token(self):
        """Create valid OAuth token."""
        return create_access_token(
            user_id=123,
            client_id="chatgpt-client",
            scope="tasks:read",
            expires_delta=timedelta(hours=1),
        )

    @pytest.fixture
    def mock_task_data(self):
        """Mock task data from backend API."""
        return {
            "task": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user-123",
                "title": "Complete documentation",
                "description": "Write comprehensive docs",
                "priority": 4,
                "status": "pending",
                "due_date": "2024-02-01T10:00:00Z",
                "effort_estimate_minutes": 120,
                "tags": "docs,high-priority",
                "created_at": "2024-01-15T08:00:00Z",
                "updated_at": "2024-01-15T08:00:00Z",
                "completed_at": None,
                "snoozed_until": None,
            },
            "score": 8.5,
            "reasoning": {
                "deadline_urgency": 2.5,
                "priority_score": 40,
                "effort_bonus": 10,
                "total_score": 8.5,
                "recommendation": "High priority task",
            },
        }

    @pytest.mark.asyncio
    async def test_renders_task_with_component(self, valid_token, mock_task_data):
        """Should return task data with embedded component."""
        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_task_data
        mock_response.raise_for_status = MagicMock()

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Call tool
            result = await get_best_task(f"Bearer {valid_token}")

            # Should preserve original data
            assert result["task"] == mock_task_data["task"]
            assert result["score"] == mock_task_data["score"]
            assert result["reasoning"] == mock_task_data["reasoning"]

            # Should have _meta field with component
            assert "_meta" in result
            assert "openai/outputTemplate" in result["_meta"]
            assert "openai/displayMode" in result["_meta"]
            assert "openai/widgetId" in result["_meta"]

            # Should use inline mode
            assert result["_meta"]["openai/displayMode"] == "inline"

            # Should auto-generate widget ID
            assert result["_meta"]["openai/widgetId"] == "task-550e8400-e29b-41d4-a716-446655440000"

            # Component template should exist
            template = result["_meta"]["openai/outputTemplate"]
            assert len(template) > 0

    @pytest.mark.asyncio
    async def test_handles_api_errors(self, valid_token):
        """Should raise exception on API errors."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "No tasks"}

        mock_error = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("mcp_server.tools.tasks.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_response.raise_for_status = MagicMock(side_effect=mock_error)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Should raise exception
            with pytest.raises(Exception):
                await get_best_task(f"Bearer {valid_token}")

    @pytest.mark.asyncio
    async def test_requires_valid_token(self):
        """Should require valid OAuth token."""
        from mcp_server.auth import TokenVerificationError

        with pytest.raises(TokenVerificationError):
            await get_best_task("Bearer invalid-token")
