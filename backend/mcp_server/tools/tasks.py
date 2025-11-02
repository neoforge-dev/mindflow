"""Task management tools for MCP server.

This module provides MCP tools for interacting with the MindFlow task API.
"""

import asyncio
from typing import Any

import httpx

from mcp_server.auth import verify_bearer_token
from mcp_server.component_loader import embed_component
from mcp_server.config import config


async def get_best_task(authorization: str) -> dict[str, Any]:
    """Get the best task to work on right now.

    This tool calls the FastAPI backend's /api/tasks/best endpoint to get
    the AI-scored best task for the authenticated user.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Dictionary containing:
            - task: Task details (id, title, description, priority, due_date, etc.)
            - score: AI-calculated score for the task
            - reasoning: Breakdown of scoring factors and recommendation

    Raises:
        TokenVerificationError: If token is invalid or expired
        Exception: If API call fails or no tasks available

    Example:
        >>> result = await get_best_task("Bearer eyJhbGc...")
        >>> print(result["task"]["title"])
        "Complete project documentation"
        >>> print(result["score"])
        8.5
        >>> print(result["reasoning"]["recommendation"])
        "High priority task worth focusing on"
    """
    # Verify token first (raises TokenVerificationError if invalid)
    verify_bearer_token(authorization)

    # Extract token (with or without Bearer prefix)
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    # Call FastAPI backend with retry logic
    url = f"{config.api_base_url}/api/tasks/best"
    headers = {"Authorization": f"Bearer {token}"}

    result = await _call_api_with_retry(
        method="GET",
        url=url,
        headers=headers,
    )

    # Embed React component for ChatGPT Apps SDK
    # This adds the _meta field with the compiled TaskCard component
    return embed_component(
        data=result,
        component_name="taskcard",
        display_mode="inline",
        # widget_id auto-generated from task.id
    )


async def _call_api_with_retry(
    method: str,
    url: str,
    headers: dict[str, str],
    max_retries: int | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Call FastAPI backend with exponential backoff retry.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to call
        headers: HTTP headers
        max_retries: Maximum retry attempts (defaults to config value)
        **kwargs: Additional arguments for httpx request

    Returns:
        Response JSON data

    Raises:
        Exception: If all retries fail or non-retryable error occurs
    """
    if max_retries is None:
        max_retries = config.max_retries

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs,
                )

                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()

                return response.json()

        except httpx.HTTPStatusError as e:
            # Don't retry client errors (4xx), only server errors (5xx)
            if e.response.status_code < 500:
                # Extract error message from response
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except Exception:
                    error_detail = str(e)

                if e.response.status_code == 404:
                    raise Exception(f"No pending tasks available: {error_detail}") from None
                elif e.response.status_code == 401:
                    raise Exception(f"Unauthorized: {error_detail}") from None
                else:
                    msg = f"API error ({e.response.status_code}): {error_detail}"
                    raise Exception(msg) from None

            # Server error - retry
            last_error = e

        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Network/timeout errors - retry
            last_error = e

        # Exponential backoff (skip on last attempt)
        if attempt < max_retries:
            delay = config.retry_base_delay * (config.retry_backoff_factor**attempt)
            await asyncio.sleep(delay)

    # All retries failed
    error_msg = f"API call failed after {max_retries + 1} attempts"
    if last_error:
        error_msg += f": {last_error}"
    raise Exception(error_msg)
