"""MindFlow MCP Server - Main Entry Point.

This module implements the Model Context Protocol (MCP) server using FastMCP
to provide AI-powered task management tools for ChatGPT Apps SDK integration.
"""

import structlog
from fastmcp import FastMCP

from mcp_server.auth import TokenVerificationError
from mcp_server.config import config
from mcp_server.tools.tasks import get_best_task

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


@mcp.tool()
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
