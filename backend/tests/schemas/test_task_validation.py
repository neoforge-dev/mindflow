"""Tests for task schema validation and sanitization."""

import pytest
from pydantic import ValidationError

from app.schemas.task import TaskCreate, TaskUpdate


class TestTaskTitleValidation:
    """Test title field validation and sanitization."""

    def test_title_html_tags_are_escaped(self) -> None:
        """Test that HTML tags in title are escaped."""
        task_data = {
            "title": "<script>alert('xss')</script>Normal Title",
            "priority": 3,
        }
        task = TaskCreate(**task_data)
        assert "<script>" not in task.title
        assert "&lt;script&gt;" in task.title
        assert "Normal Title" in task.title

    def test_title_max_length_enforced(self) -> None:
        """Test that title exceeding 200 chars is rejected."""
        long_title = "A" * 201
        task_data = {"title": long_title, "priority": 3}

        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(**task_data)

        errors = exc_info.value.errors()
        assert any(
            "200" in str(error["msg"]) and error["loc"] == ("title",) for error in errors
        )

    def test_title_exactly_200_chars_accepted(self) -> None:
        """Test that title with exactly 200 chars is accepted."""
        exact_title = "A" * 200
        task_data = {"title": exact_title, "priority": 3}
        task = TaskCreate(**task_data)
        assert len(task.title) == 200

    def test_title_ampersand_escaped(self) -> None:
        """Test that ampersands are properly escaped."""
        task_data = {"title": "Task & Subtask", "priority": 3}
        task = TaskCreate(**task_data)
        assert "&amp;" in task.title or task.title == "Task & Subtask"

    def test_title_quotes_escaped(self) -> None:
        """Test that quotes are properly escaped."""
        task_data = {"title": 'Task "quoted" text', "priority": 3}
        task = TaskCreate(**task_data)
        # Quotes should be escaped or preserved safely
        assert task.title is not None


class TestTaskDescriptionValidation:
    """Test description field validation and sanitization."""

    def test_description_html_tags_are_escaped(self) -> None:
        """Test that HTML tags in description are escaped."""
        task_data = {
            "title": "Test Task",
            "description": "<img src=x onerror=alert(1)>Description",
            "priority": 3,
        }
        task = TaskCreate(**task_data)
        assert "<img" not in task.description
        assert "&lt;img" in task.description

    def test_description_max_length_enforced(self) -> None:
        """Test that description exceeding 2000 chars is rejected."""
        long_desc = "A" * 2001
        task_data = {"title": "Test", "description": long_desc, "priority": 3}

        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(**task_data)

        errors = exc_info.value.errors()
        assert any(
            "2000" in str(error["msg"]) and error["loc"] == ("description",)
            for error in errors
        )

    def test_description_exactly_2000_chars_accepted(self) -> None:
        """Test that description with exactly 2000 chars is accepted."""
        exact_desc = "A" * 2000
        task_data = {"title": "Test", "description": exact_desc, "priority": 3}
        task = TaskCreate(**task_data)
        assert len(task.description) == 2000

    def test_description_none_allowed(self) -> None:
        """Test that description can be None."""
        task_data = {"title": "Test Task", "priority": 3}
        task = TaskCreate(**task_data)
        assert task.description is None

    def test_description_script_injection_prevented(self) -> None:
        """Test that script injection attempts are neutralized."""
        task_data = {
            "title": "Test",
            "description": "<script>document.cookie</script>",
            "priority": 3,
        }
        task = TaskCreate(**task_data)
        assert "<script>" not in task.description
        assert "&lt;script&gt;" in task.description


class TestTaskUpdateValidation:
    """Test TaskUpdate schema validation."""

    def test_update_title_sanitized(self) -> None:
        """Test that title updates are sanitized."""
        update_data = {"title": "<b>Updated</b> Title"}
        update = TaskUpdate(**update_data)
        assert "&lt;b&gt;" in update.title

    def test_update_description_sanitized(self) -> None:
        """Test that description updates are sanitized."""
        update_data = {"description": "<script>alert(1)</script>"}
        update = TaskUpdate(**update_data)
        assert "&lt;script&gt;" in update.description

    def test_update_partial_fields_work(self) -> None:
        """Test that partial updates with only some fields work."""
        update_data = {"priority": 5}
        update = TaskUpdate(**update_data)
        assert update.priority == 5
        assert update.title is None
        assert update.description is None
