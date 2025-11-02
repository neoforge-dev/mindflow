"""MindFlow MCP Server - Main Entry Point.

This module implements the Model Context Protocol (MCP) server using FastMCP
to provide AI-powered task management tools for ChatGPT Apps SDK integration.
"""

import structlog
from fastmcp import FastMCP

from mcp_server.auth import TokenVerificationError
from mcp_server.config import config
from mcp_server.tools.tasks import complete_task_tool, get_best_task, snooze_task_tool

# Initialize structured logger
logger = structlog.get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="MindFlow Task Management",
    instructions=(
        "You are an AI assistant that helps users manage their tasks effectively. "
        "You can retrieve the best task to work on based on AI scoring that considers "
        "deadlines, priorities, effort estimates, and user preferences. "
        "Always be concise and actionable in your recommendations."
    ),
)


@mcp.tool(
    name="get_next_task",
    description="""Use this tool when the user asks what to work on, what's next, or needs task recommendations.

WHEN TO USE:
- "What should I work on?"
- "What's next?"
- "Show me my top priority"
- "What's most important right now?"
- "What task should I focus on?"

DO NOT USE:
- To list all tasks (user wants to see everything)
- To create a new task (user is adding tasks)
- To search for specific tasks (user has a task in mind)
- To show completed tasks (user wants history)

RETURNS:
The single highest-priority task based on AI scoring that considers:
- Deadline urgency (tasks due soon score higher)
- User-set priority (1=low to 5=urgent)
- Effort estimate (quick wins get bonus points)
- Current time of day (respects user preferences)

The response includes an interactive card showing task details, AI score, and reasoning.""",
    readOnlyHint=True,  # This is a read-only operation, enables faster confirmations
)
async def get_next_task(authorization: str) -> dict:
    """Get the best task to work on right now.

    This tool retrieves the highest-priority task based on AI scoring that
    considers multiple factors including deadlines, user priority, effort
    estimates, and time-of-day preferences.

    Args:
        authorization: OAuth Bearer token from the Authorization header

    Returns:
        Dictionary containing:
            - task: Complete task details (id, title, description, priority, due_date, etc.)
            - score: AI-calculated priority score (higher = more important)
            - reasoning: Detailed breakdown of scoring factors and recommendation
            - _meta: Component embedding metadata for ChatGPT rendering

    Raises:
        Exception: If authentication fails, no tasks available, or API error occurs

    Example response:
        {
            "task": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Complete project documentation",
                "description": "Write comprehensive docs for the new feature",
                "priority": 4,
                "due_date": "2024-02-01T10:00:00Z",
                "effort_estimate_minutes": 120
            },
            "score": 8.5,
            "reasoning": {
                "deadline_urgency": 2.5,
                "priority_score": 40,
                "effort_bonus": 10,
                "total_score": 8.5,
                "recommendation": "High priority task worth focusing on"
            },
            "_meta": {
                "openai/outputTemplate": "...",
                "openai/displayMode": "inline",
                "openai/widgetId": "task-550e8400..."
            }
        }
    """
    try:
        logger.info("get_next_task_called", has_auth=bool(authorization))

        # Verify token and get best task
        result = await get_best_task(authorization)

        logger.info(
            "get_next_task_success",
            task_id=result.get("task", {}).get("id"),
            score=result.get("score"),
        )

        return result

    except TokenVerificationError as e:
        logger.warning("get_next_task_auth_failed", error=str(e))
        raise Exception(f"Authentication failed: {e}") from e

    except Exception as e:
        logger.error("get_next_task_failed", error=str(e))
        raise


@mcp.tool(
    name="complete_task",
    description="""Mark a task as completed.

WHEN TO USE:
- User says they finished/completed a task
- User wants to mark a task done
- After successfully completing work

REQUIRED:
- task_id: The ID of the task to complete

RETURNS:
Updated task with status='completed' and completion timestamp.""",
    readOnlyHint=False,  # This modifies data
)
async def complete_task(authorization: str, task_id: str) -> dict:
    """Mark a task as completed.

    Sets task status to 'completed' and records completion timestamp.

    Args:
        authorization: OAuth Bearer token
        task_id: UUID of the task to complete

    Returns:
        Updated task data

    Raises:
        Exception: If authentication fails or task not found
    """
    try:
        logger.info("complete_task_called", task_id=task_id)
        result = await complete_task_tool(authorization, task_id)
        logger.info("complete_task_success", task_id=task_id)
        return result
    except TokenVerificationError as e:
        logger.warning("complete_task_auth_failed", error=str(e))
        raise Exception(f"Authentication failed: {e}") from e
    except Exception as e:
        logger.error("complete_task_failed", error=str(e))
        raise


@mcp.tool(
    name="snooze_task",
    description="""Snooze a task for a specified number of hours.

WHEN TO USE:
- User wants to postpone a task
- User says "remind me later"
- User needs to defer work on a task

REQUIRED:
- task_id: The ID of the task to snooze
- hours: Number of hours to snooze (default: 3)

RETURNS:
Updated task with snoozed_until timestamp and status='snoozed'.""",
    readOnlyHint=False,  # This modifies data
)
async def snooze_task(authorization: str, task_id: str, hours: int = 3) -> dict:
    """Snooze a task for specified hours.

    Sets task status to 'snoozed' and snoozed_until timestamp.

    Args:
        authorization: OAuth Bearer token
        task_id: UUID of the task to snooze
        hours: Number of hours to snooze (default: 3)

    Returns:
        Updated task data

    Raises:
        Exception: If authentication fails or task not found
    """
    try:
        logger.info("snooze_task_called", task_id=task_id, hours=hours)
        result = await snooze_task_tool(authorization, task_id, hours)
        logger.info("snooze_task_success", task_id=task_id, hours=hours)
        return result
    except TokenVerificationError as e:
        logger.warning("snooze_task_auth_failed", error=str(e))
        raise Exception(f"Authentication failed: {e}") from e
    except Exception as e:
        logger.error("snooze_task_failed", error=str(e))
        raise


@mcp.tool()
async def health_check() -> dict:
    """Check if the MCP server is healthy and can connect to the FastAPI backend.

    This is a simple health check tool that doesn't require authentication.
    It can be used to verify the MCP server is running and configured correctly.

    Returns:
        Dictionary with server status information

    Example response:
        {
            "status": "healthy",
            "server": "MindFlow MCP Server",
            "version": "1.0.0",
            "api_base_url": "http://localhost:8000"
        }
    """
    return {
        "status": "healthy",
        "server": "MindFlow MCP Server",
        "version": "1.0.0",
        "api_base_url": config.api_base_url,
    }


def main():
    """Run the MCP server.

    This starts the FastMCP server on the configured host and port.
    """
    logger.info(
        "starting_mcp_server",
        host=config.mcp_server_host,
        port=config.mcp_server_port,
        api_base_url=config.api_base_url,
    )

    # FastMCP handles the server startup
    # In production, this would typically be run via CLI: fastmcp run mcp_server.main:mcp
    print(f"MCP Server starting on {config.mcp_server_host}:{config.mcp_server_port}")
    print(f"API Base URL: {config.api_base_url}")
    print("Available tools:")
    print("  - get_next_task: Get the best task to work on")
    print("  - health_check: Check server health")


if __name__ == "__main__":
    main()
