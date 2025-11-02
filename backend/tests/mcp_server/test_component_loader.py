"""Tests for component loader module.

Tests the loading and embedding of React components for ChatGPT Apps SDK.
"""

import pytest
from pathlib import Path

from mcp_server.component_loader import (
    load_component_code,
    embed_component,
    clear_component_cache,
    _component_cache,
)


class TestComponentLoader:
    """Test component loading functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_component_cache()

    def test_load_component_code_success(self):
        """Test loading a component that exists."""
        # This test assumes the component has been built
        # If it doesn't exist, it should fail with a clear error
        try:
            code = load_component_code("taskcard")
            assert isinstance(code, str)
            assert len(code) > 0
            # Should contain React code
            assert "React" in code or "react" in code.lower()
        except FileNotFoundError as e:
            pytest.skip(
                f"Component not built yet: {e}\n"
                f"Run: cd frontend && npm run build && npm run deploy"
            )

    def test_load_component_code_caching(self):
        """Test that component code is cached."""
        try:
            # First load
            code1 = load_component_code("taskcard")
            assert "taskcard" in _component_cache

            # Second load should use cache
            code2 = load_component_code("taskcard")
            assert code1 == code2
            assert id(code1) == id(code2)  # Same object
        except FileNotFoundError:
            pytest.skip("Component not built yet")

    def test_load_component_code_nonexistent(self):
        """Test loading a component that doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_component_code("nonexistent-component")

        assert "Component file not found" in str(exc_info.value)
        assert "npm run build" in str(exc_info.value)

    def test_clear_component_cache(self):
        """Test clearing the component cache."""
        try:
            # Load component to populate cache
            load_component_code("taskcard")
            assert len(_component_cache) > 0

            # Clear cache
            clear_component_cache()
            assert len(_component_cache) == 0
        except FileNotFoundError:
            pytest.skip("Component not built yet")


class TestEmbedComponent:
    """Test component embedding functionality."""

    def test_embed_component_basic(self):
        """Test basic component embedding with minimal data."""
        data = {
            "task": {"id": "123", "title": "Test Task"},
            "score": 8.5,
            "reasoning": {"recommendation": "Do this task"},
        }

        # Mock the component loading to avoid file dependency
        import mcp_server.component_loader as loader_module

        original_load = loader_module.load_component_code

        def mock_load(name):
            return "// Mock React component code"

        loader_module.load_component_code = mock_load

        try:
            result = embed_component(data)

            # Should include original data
            assert result["task"] == data["task"]
            assert result["score"] == data["score"]
            assert result["reasoning"] == data["reasoning"]

            # Should include _meta field
            assert "_meta" in result
            assert "openai/outputTemplate" in result["_meta"]
            assert "openai/displayMode" in result["_meta"]
            assert "openai/widgetId" in result["_meta"]

            # Check defaults
            assert result["_meta"]["openai/displayMode"] == "inline"
            assert result["_meta"]["openai/widgetId"] == "task-123"
            assert result["_meta"]["openai/outputTemplate"] == "// Mock React component code"
        finally:
            loader_module.load_component_code = original_load

    def test_embed_component_custom_widget_id(self):
        """Test embedding with custom widget ID."""
        data = {"task": {"id": "123"}, "score": 8.5}

        import mcp_server.component_loader as loader_module

        original_load = loader_module.load_component_code
        loader_module.load_component_code = lambda name: "// Mock code"

        try:
            result = embed_component(data, widget_id="custom-widget-id")
            assert result["_meta"]["openai/widgetId"] == "custom-widget-id"
        finally:
            loader_module.load_component_code = original_load

    def test_embed_component_custom_display_mode(self):
        """Test embedding with custom display mode."""
        data = {"task": {"id": "123"}, "score": 8.5}

        import mcp_server.component_loader as loader_module

        original_load = loader_module.load_component_code
        loader_module.load_component_code = lambda name: "// Mock code"

        try:
            result = embed_component(data, display_mode="fullscreen")
            assert result["_meta"]["openai/displayMode"] == "fullscreen"
        finally:
            loader_module.load_component_code = original_load

    def test_embed_component_auto_widget_id(self):
        """Test auto-generation of widget ID from task ID."""
        data = {"task": {"id": "abc-123"}, "score": 7.0}

        import mcp_server.component_loader as loader_module

        original_load = loader_module.load_component_code
        loader_module.load_component_code = lambda name: "// Mock code"

        try:
            result = embed_component(data)
            assert result["_meta"]["openai/widgetId"] == "task-abc-123"
        finally:
            loader_module.load_component_code = original_load

    def test_embed_component_fallback_widget_id(self):
        """Test fallback widget ID when no task ID available."""
        data = {"score": 7.0}  # No task field

        import mcp_server.component_loader as loader_module

        original_load = loader_module.load_component_code
        loader_module.load_component_code = lambda name: "// Mock code"

        try:
            result = embed_component(data)
            assert result["_meta"]["openai/widgetId"] == "taskcard-default"
        finally:
            loader_module.load_component_code = original_load

    def test_embed_component_different_component_names(self):
        """Test embedding different component types."""
        data = {"task": {"id": "123"}, "score": 8.5}

        import mcp_server.component_loader as loader_module

        original_load = loader_module.load_component_code

        loaded_components = []

        def mock_load(name):
            loaded_components.append(name)
            return f"// {name} code"

        loader_module.load_component_code = mock_load

        try:
            result = embed_component(data, component_name="custom-component")
            assert "custom-component" in loaded_components
            assert result["_meta"]["openai/outputTemplate"] == "// custom-component code"
        finally:
            loader_module.load_component_code = original_load
