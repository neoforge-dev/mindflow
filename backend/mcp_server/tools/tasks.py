"""Task management tools for MCP server.

Clean, elegant task tools using the component renderer.
"""

import asyncio
from typing import Any

import httpx

from mcp_server.auth import verify_bearer_token
from mcp_server.config import config
from mcp_server.renderer import render_task


async def get_best_task(authorization: str) -> dict[str, Any]:
    """Get the best task to work on right now.

    Fetches AI-scored task from backend and renders with React component.

    Args:
        authorization: OAuth Bearer token

    Returns:
        Task data with embedded React component

    Raises:
        TokenVerificationError: If token invalid
        Exception: If API call fails
    """
    # Verify token
    verify_bearer_token(authorization)

    # Extract token
    token = authorization[7:] if authorization.startswith("Bearer ") else authorization

    # Fetch task data
    url = f"{config.api_base_url}/api/tasks/best"
    headers = {"Authorization": f"Bearer {token}"}

    data = await _call_api(url, headers)

    # Render with component
    return render_task(data)


async def _call_api(url: str, headers: dict[str, str]) -> dict[str, Any]:
    """Call backend API with retry logic.

    Args:
        url: API endpoint URL
        headers: HTTP headers

    Returns:
        Response JSON data

    Raises:
        Exception: If request fails
    """
    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data

        except httpx.HTTPStatusError as e:
            # Don't retry client errors (4xx)
            if e.response.status_code < 500:
                detail = _extract_error(e.response)

                if e.response.status_code == 404:
                    raise Exception(f"No pending tasks available: {detail}") from None
                elif e.response.status_code == 401:
                    raise Exception(f"Unauthorized: {detail}") from None
                else:
                    raise Exception(f"API error ({e.response.status_code}): {detail}") from None

            # Retry server errors (5xx)
            last_error = e

        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Retry network/timeout errors
            last_error = e

        # Exponential backoff
        if attempt < config.max_retries:
            delay = config.retry_base_delay * (config.retry_backoff_factor**attempt)
            await asyncio.sleep(delay)

    # All retries failed
    raise Exception(f"API call failed after {config.max_retries + 1} attempts: {last_error}")


def _extract_error(response: httpx.Response) -> str:
    """Extract error message from response.

    Args:
        response: HTTP response

    Returns:
        Error message
    """
    try:
        data: dict[str, Any] = response.json()
        detail: str = data.get("detail", str(response))
        return detail
    except Exception:
        return str(response)


async def complete_task_tool(authorization: str, task_id: str) -> dict[str, Any]:
    """Complete a task via backend API.

    Args:
        authorization: OAuth Bearer token
        task_id: Task UUID to complete

    Returns:
        Updated task data

    Raises:
        TokenVerificationError: If token invalid
        Exception: If API call fails
    """
    # Verify token
    verify_bearer_token(authorization)

    # Extract token
    token = authorization[7:] if authorization.startswith("Bearer ") else authorization

    # Call complete endpoint
    url = f"{config.api_base_url}/api/tasks/{task_id}/complete"
    headers = {"Authorization": f"Bearer {token}"}

    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data

        except httpx.HTTPStatusError as e:
            # Don't retry client errors (4xx)
            if e.response.status_code < 500:
                detail = _extract_error(e.response)

                if e.response.status_code == 404:
                    raise Exception(f"Task not found: {detail}") from None
                elif e.response.status_code == 401:
                    raise Exception(f"Unauthorized: {detail}") from None
                else:
                    raise Exception(f"API error ({e.response.status_code}): {detail}") from None

            # Retry server errors (5xx)
            last_error = e

        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Retry network/timeout errors
            last_error = e

        # Exponential backoff
        if attempt < config.max_retries:
            delay = config.retry_base_delay * (config.retry_backoff_factor**attempt)
            await asyncio.sleep(delay)

    # All retries failed
    raise Exception(f"API call failed after {config.max_retries + 1} attempts: {last_error}")


async def snooze_task_tool(authorization: str, task_id: str, hours: int = 3) -> dict[str, Any]:
    """Snooze a task for specified hours via backend API.

    Args:
        authorization: OAuth Bearer token
        task_id: Task UUID to snooze
        hours: Number of hours to snooze (default: 3)

    Returns:
        Updated task data

    Raises:
        TokenVerificationError: If token invalid
        Exception: If API call fails
    """
    # Verify token
    verify_bearer_token(authorization)

    # Extract token
    token = authorization[7:] if authorization.startswith("Bearer ") else authorization

    # Call snooze endpoint
    url = f"{config.api_base_url}/api/tasks/{task_id}/snooze"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"hours": hours}

    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, params=params)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data

        except httpx.HTTPStatusError as e:
            # Don't retry client errors (4xx)
            if e.response.status_code < 500:
                detail = _extract_error(e.response)

                if e.response.status_code == 404:
                    raise Exception(f"Task not found: {detail}") from None
                elif e.response.status_code == 401:
                    raise Exception(f"Unauthorized: {detail}") from None
                else:
                    raise Exception(f"API error ({e.response.status_code}): {detail}") from None

            # Retry server errors (5xx)
            last_error = e

        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Retry network/timeout errors
            last_error = e

        # Exponential backoff
        if attempt < config.max_retries:
            delay = config.retry_base_delay * (config.retry_backoff_factor**attempt)
            await asyncio.sleep(delay)

    # All retries failed
    raise Exception(f"API call failed after {config.max_retries + 1} attempts: {last_error}")
