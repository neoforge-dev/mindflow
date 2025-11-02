"""Tests for component renderer module."""

from pathlib import Path

import pytest

from mcp_server.renderer import (
    ComponentRenderer,
    get_renderer,
    render_task,
)


class TestComponentRenderer:
    """Test ComponentRenderer class."""

    def test_init_default_assets_dir(self):
        """Should use default assets directory."""
        renderer = ComponentRenderer()
        expected = Path(__file__).parent.parent.parent / "mcp_server" / "assets"
        assert renderer._assets_dir == expected

    def test_init_custom_assets_dir(self, tmp_path):
        """Should use custom assets directory."""
        renderer = ComponentRenderer(assets_dir=tmp_path)
        assert renderer._assets_dir == tmp_path

    def test_load_component_success(self, tmp_path):
        """Should load component code."""
        # Create test component
        component_path = tmp_path / "test.js"
        component_path.write_text("// Test component code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        code = renderer.load_component("test")

        assert code == "// Test component code"

    def test_load_component_caching(self, tmp_path):
        """Should cache component code."""
        component_path = tmp_path / "test.js"
        component_path.write_text("// Original code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)

        # First load
        code1 = renderer.load_component("test")
        assert code1 == "// Original code"

        # Modify file
        component_path.write_text("// Modified code", encoding="utf-8")

        # Second load should return cached version
        code2 = renderer.load_component("test")
        assert code2 == "// Original code"  # Still cached

    def test_load_component_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing component."""
        renderer = ComponentRenderer(assets_dir=tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            renderer.load_component("nonexistent")

        assert "Component 'nonexistent' not found" in str(exc_info.value)
        assert "npm run deploy" in str(exc_info.value)

    def test_clear_cache(self, tmp_path):
        """Should clear component cache."""
        component_path = tmp_path / "test.js"
        component_path.write_text("// Original code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)

        # Load and cache
        code1 = renderer.load_component("test")
        assert code1 == "// Original code"

        # Clear cache
        renderer.clear_cache()

        # Modify file
        component_path.write_text("// New code", encoding="utf-8")

        # Should load fresh version
        code2 = renderer.load_component("test")
        assert code2 == "// New code"

    def test_render_basic(self, tmp_path):
        """Should render data with component."""
        component_path = tmp_path / "taskwidget.js"
        component_path.write_text("// Component code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        data = {
            "task": {"id": "123", "title": "Test"},
            "score": 8.5,
            "reasoning": {"recommendation": "Do this"},
        }

        result = renderer.render(data)

        # Should include original data
        assert result["task"] == data["task"]
        assert result["score"] == data["score"]
        assert result["reasoning"] == data["reasoning"]

        # Should include _meta
        assert "_meta" in result
        assert result["_meta"]["openai/outputTemplate"] == "// Component code"
        assert result["_meta"]["openai/displayMode"] == "inline"
        assert result["_meta"]["openai/widgetId"] == "task-123"

    def test_render_custom_widget_id(self, tmp_path):
        """Should use custom widget ID."""
        component_path = tmp_path / "taskwidget.js"
        component_path.write_text("// Code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        data = {"task": {"id": "123"}}

        result = renderer.render(data, widget_id="custom-widget")

        assert result["_meta"]["openai/widgetId"] == "custom-widget"

    def test_render_custom_display_mode(self, tmp_path):
        """Should use custom display mode."""
        component_path = tmp_path / "taskwidget.js"
        component_path.write_text("// Code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        data = {"task": {"id": "123"}}

        result = renderer.render(data, mode="fullscreen")

        assert result["_meta"]["openai/displayMode"] == "fullscreen"

    def test_render_auto_widget_id_from_task(self, tmp_path):
        """Should auto-generate widget ID from task ID."""
        component_path = tmp_path / "taskwidget.js"
        component_path.write_text("// Code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        data = {"task": {"id": "abc-xyz-123"}, "score": 7.0}

        result = renderer.render(data)

        assert result["_meta"]["openai/widgetId"] == "task-abc-xyz-123"

    def test_render_fallback_widget_id(self, tmp_path):
        """Should use fallback widget ID when no task."""
        component_path = tmp_path / "taskwidget.js"
        component_path.write_text("// Code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        data = {"score": 7.0}  # No task

        result = renderer.render(data)

        assert result["_meta"]["openai/widgetId"] == "taskwidget-default"

    def test_render_custom_component(self, tmp_path):
        """Should render custom component."""
        component_path = tmp_path / "custom.js"
        component_path.write_text("// Custom code", encoding="utf-8")

        renderer = ComponentRenderer(assets_dir=tmp_path)
        data = {"data": "test"}

        result = renderer.render(data, component="custom")

        assert result["_meta"]["openai/outputTemplate"] == "// Custom code"
        assert result["_meta"]["openai/widgetId"] == "custom-default"


class TestGlobalRenderer:
    """Test global renderer functions."""

    def test_get_renderer_singleton(self):
        """Should return singleton instance."""
        renderer1 = get_renderer()
        renderer2 = get_renderer()

        assert renderer1 is renderer2

    def test_render_task_convenience(self, tmp_path, monkeypatch):
        """Should render task data with convenience function."""
        # Create test component
        component_path = tmp_path / "taskwidget.js"
        component_path.write_text("// Task widget", encoding="utf-8")

        # Create renderer with test assets
        test_renderer = ComponentRenderer(assets_dir=tmp_path)

        # Patch global renderer
        import mcp_server.renderer as renderer_module

        renderer_module._renderer = test_renderer

        try:
            data = {
                "task": {"id": "test-123", "title": "Test Task"},
                "score": 9.0,
                "reasoning": {"recommendation": "High priority"},
            }

            result = render_task(data)

            assert result["task"] == data["task"]
            assert result["score"] == data["score"]
            assert "_meta" in result
            assert result["_meta"]["openai/displayMode"] == "inline"
            assert result["_meta"]["openai/widgetId"] == "task-test-123"
        finally:
            # Reset global renderer
            renderer_module._renderer = None


class TestRealComponent:
    """Test with real deployed component."""

    def test_load_real_component(self):
        """Should load actually deployed component."""
        renderer = get_renderer()

        try:
            code = renderer.load_component("taskwidget")

            # Should be valid JavaScript
            assert len(code) > 0
            assert "TaskWidget" in code or "export" in code

            # Should be minified/optimized
            assert len(code) < 10000  # Should be under 10KB
        except FileNotFoundError:
            pytest.skip("Component not deployed yet - run 'npm run deploy'")

    def test_render_real_task_data(self):
        """Should render real task data."""
        renderer = get_renderer()

        data = {
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

        try:
            result = renderer.render(data)

            # Should preserve all data
            assert result["task"] == data["task"]
            assert result["score"] == data["score"]
            assert result["reasoning"] == data["reasoning"]

            # Should have proper _meta
            assert result["_meta"]["openai/displayMode"] == "inline"
            assert (
                result["_meta"]["openai/widgetId"]
                == "task-550e8400-e29b-41d4-a716-446655440000"
            )
            assert len(result["_meta"]["openai/outputTemplate"]) > 0
        except FileNotFoundError:
            pytest.skip("Component not deployed yet - run 'npm run deploy'")
