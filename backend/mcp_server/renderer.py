"""Component Renderer for ChatGPT Apps SDK.

Clean, elegant component embedding for MCP responses.
"""

from pathlib import Path
from typing import Any, Literal

DisplayMode = Literal["inline", "carousel", "fullscreen"]


class ComponentRenderer:
    """Renders React components in MCP tool responses."""

    def __init__(self, assets_dir: Path | None = None):
        """Initialize renderer with assets directory.

        Args:
            assets_dir: Path to component assets (defaults to ./assets)
        """
        self._assets_dir = assets_dir or Path(__file__).parent / "assets"
        self._cache: dict[str, str] = {}

    def load_component(self, name: str) -> str:
        """Load compiled component code.

        Args:
            name: Component name (e.g., "taskwidget")

        Returns:
            Component JavaScript code

        Raises:
            FileNotFoundError: If component not found
        """
        if name in self._cache:
            return self._cache[name]

        component_path = self._assets_dir / f"{name}.js"
        if not component_path.exists():
            raise FileNotFoundError(
                f"Component '{name}' not found at {component_path}\n"
                f"Build it first: cd frontend && npm run deploy"
            )

        code = component_path.read_text(encoding="utf-8")
        self._cache[name] = code
        return code

    def render(
        self,
        data: dict[str, Any],
        *,
        component: str = "taskwidget",
        mode: DisplayMode = "inline",
        widget_id: str | None = None,
    ) -> dict[str, Any]:
        """Render data with embedded component.

        Args:
            data: Tool output data
            component: Component name
            mode: Display mode (inline/carousel/fullscreen)
            widget_id: Widget ID for state persistence

        Returns:
            Data with _meta field for ChatGPT rendering
        """
        component_code = self.load_component(component)

        # Auto-generate widget ID from task data if not provided
        if widget_id is None and "task" in data and isinstance(data["task"], dict):
            task_id = data["task"].get("id", "default")
            widget_id = f"task-{task_id}"
        elif widget_id is None:
            widget_id = f"{component}-default"

        return {
            **data,
            "_meta": {
                "openai/outputTemplate": component_code,
                "openai/displayMode": mode,
                "openai/widgetId": widget_id,
            },
        }

    def clear_cache(self) -> None:
        """Clear component code cache."""
        self._cache.clear()


# Global renderer instance
_renderer: ComponentRenderer | None = None


def get_renderer() -> ComponentRenderer:
    """Get global renderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = ComponentRenderer()
    return _renderer


def render_task(data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to render task data.

    Args:
        data: Task output from backend API

    Returns:
        Rendered data with component
    """
    return get_renderer().render(data, component="taskwidget", mode="inline")
