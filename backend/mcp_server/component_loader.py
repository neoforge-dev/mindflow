"""Component loader for ChatGPT Apps SDK.

This module handles loading and embedding React components
in MCP tool responses for ChatGPT Apps SDK integration.
"""

import os
from pathlib import Path
from typing import Any

# Cache for component code to avoid repeated file reads
_component_cache: dict[str, str] = {}


def load_component_code(component_name: str = "taskcard") -> str:
    """Load the compiled React component code from the assets directory.

    Args:
        component_name: Name of the component to load (default: "taskcard")

    Returns:
        String containing the compiled JavaScript code

    Raises:
        FileNotFoundError: If component file doesn't exist
    """
    # Return from cache if available
    if component_name in _component_cache:
        return _component_cache[component_name]

    # Determine assets directory (relative to this file)
    assets_dir = Path(__file__).parent / "assets"
    component_file = assets_dir / f"{component_name}.js"

    if not component_file.exists():
        raise FileNotFoundError(
            f"Component file not found: {component_file}\n"
            f"Make sure to build the frontend first: cd frontend && npm run build"
        )

    # Read and cache component code
    with open(component_file, "r", encoding="utf-8") as f:
        code = f.read()

    _component_cache[component_name] = code
    return code


def embed_component(
    data: dict[str, Any],
    component_name: str = "taskcard",
    display_mode: str = "inline",
    widget_id: str | None = None,
) -> dict[str, Any]:
    """Embed a React component in an MCP tool response.

    This adds the _meta field required by ChatGPT Apps SDK to render
    a custom React component instead of plain JSON output.

    Args:
        data: The tool output data (task, score, reasoning, etc.)
        component_name: Name of the component to embed (default: "taskcard")
        display_mode: How to display the component ("inline", "carousel", "fullscreen")
        widget_id: Unique ID for widget state persistence (auto-generated if None)

    Returns:
        Dictionary with original data + _meta field for component rendering

    Example:
        >>> task_data = {"task": {...}, "score": 8.5, "reasoning": {...}}
        >>> result = embed_component(task_data, widget_id="task-123")
        >>> print(result["_meta"]["openai/displayMode"])
        "inline"
    """
    # Load component code
    component_code = load_component_code(component_name)

    # Auto-generate widget ID from task ID if not provided
    if widget_id is None and "task" in data and "id" in data["task"]:
        widget_id = f"task-{data['task']['id']}"
    elif widget_id is None:
        widget_id = f"{component_name}-default"

    # Create response with _meta field
    return {
        **data,
        "_meta": {
            "openai/outputTemplate": component_code,
            "openai/displayMode": display_mode,
            "openai/widgetId": widget_id,
        },
    }


def clear_component_cache():
    """Clear the component code cache.

    Useful during development when components are being rebuilt frequently.
    """
    _component_cache.clear()
