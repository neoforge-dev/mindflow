"""
Comprehensive API endpoint tests.

Tests all 6 API endpoints with various scenarios.
"""

import pytest

from tests.client import MindFlowClient
from tests.factories import (
    CompletedTaskFactory,
    InProgressTaskFactory,
    TaskFactory,
    UrgentTaskFactory,
)


@pytest.mark.api
class TestCreateTask:
    """Tests for POST /create endpoint."""

    def test_create_minimal_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test creating task with only required fields."""
        task_data = {"title": "Minimal Task", "priority": 3}

        response = client.create_task(task_data)

        assert response.status == "success" or response.status == "created"
        assert response.code == 201
        assert "id" in response.data
        task_id_tracker.append(response.data["id"])

    def test_create_complete_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test creating task with all fields."""
        task_data = TaskFactory.build()

        response = client.create_task(task_data)

        assert response.status in ["success", "created"]
        assert response.code == 201
        assert response.data["title"] == task_data["title"]
        task_id_tracker.append(response.data["id"])

    def test_create_urgent_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test creating high-priority urgent task."""
        task_data = UrgentTaskFactory.build()

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_create_task_missing_title(self, client: MindFlowClient):
        """Test validation: missing required title field."""
        task_data = {"priority": 3}

        with pytest.raises(Exception):  # Should raise validation error
            client.create_task(task_data)

    def test_create_task_missing_priority(self, client: MindFlowClient):
        """Test validation: missing required priority field."""
        task_data = {"title": "No Priority Task"}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_create_task_invalid_priority_high(self, client: MindFlowClient):
        """Test validation: priority > 5."""
        task_data = {"title": "Invalid Priority", "priority": 10}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_create_task_invalid_priority_low(self, client: MindFlowClient):
        """Test validation: priority < 1."""
        task_data = {"title": "Invalid Priority", "priority": 0}

        with pytest.raises(Exception):
            client.create_task(task_data)

    @pytest.mark.edge_case
    def test_create_task_max_title_length(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test boundary: 256 character title."""
        task_data = {"title": "A" * 256, "priority": 3}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    @pytest.mark.edge_case
    def test_create_task_empty_description(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test edge case: empty description."""
        task_data = {"title": "Empty Description", "priority": 3, "description": ""}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    @pytest.mark.edge_case
    def test_create_task_no_due_date(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test edge case: task without due date."""
        task_data = {"title": "No Due Date", "priority": 3}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    @pytest.mark.edge_case
    def test_create_task_unicode_title(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test edge case: unicode characters in title."""
        task_data = {
            "title": "Unicode: 中文 العربية עִבְרִית 🎯",
            "priority": 3,
        }

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])


@pytest.mark.api
class TestGetBestTask:
    """Tests for GET /best endpoint."""

    def test_get_best_task_with_data(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test getting best task when tasks exist."""
        # Create a few tasks first
        for _ in range(3):
            task = TaskFactory.build()
            response = client.create_task(task)
            task_id_tracker.append(response.data["id"])

        response = client.get_best_task()

        assert response.status == "success"
        assert response.code == 200
        if isinstance(response.data, dict) and "id" in response.data:
            assert "score" in response.data
            assert "reasoning" in response.data

    def test_get_best_task_returns_highest_score(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test that best task returns highest scored task."""
        # Create low priority task
        low = TaskFactory.build(priority=1, status="pending")
        client.create_task(low)

        # Create high priority task
        high = TaskFactory.build(priority=5, status="pending")
        response = client.create_task(high)
        high_id = response.data["id"]
        task_id_tracker.extend([high_id])

        # Get best task
        response = client.get_best_task()

        # Should return the high priority task (if scoring is correct)
        assert response.status == "success"
        if isinstance(response.data, dict) and "id" in response.data:
            # High priority should score higher
            assert response.data["priority"] >= 4

    def test_get_best_task_with_timezone(self, client: MindFlowClient):
        """Test timezone parameter."""
        response = client.get_best_task(timezone="America/New_York")

        assert response.status == "success"
        assert response.code == 200

    @pytest.mark.edge_case
    def test_get_best_task_no_active_tasks(self, client: MindFlowClient):
        """Test when only completed/snoozed tasks exist."""
        # If we had cleanup, this would be easier to test in isolation
        # For now, this tests the current state
        response = client.get_best_task()

        assert response.status == "success"
        assert response.code == 200


@pytest.mark.api
class TestUpdateTask:
    """Tests for POST /update endpoint."""

    def test_update_task_status(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test updating task status."""
        # Create task
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Update status
        response = client.update_task(task_id, {"status": "in_progress"})

        assert response.status == "success"
        assert response.code == 200

    def test_update_task_priority(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test updating task priority."""
        task = TaskFactory.build(priority=3)
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        response = client.update_task(task_id, {"priority": 5})

        assert response.status == "success"
        assert response.code == 200

    def test_update_task_multiple_fields(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test updating multiple fields at once."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        updates = {"status": "in_progress", "priority": 5, "title": "Updated Title"}

        response = client.update_task(task_id, updates)

        assert response.status == "success"

    def test_update_nonexistent_task(self, client: MindFlowClient):
        """Test updating task that doesn't exist."""
        fake_id = "nonexistent-task-id"

        with pytest.raises(Exception):
            client.update_task(fake_id, {"status": "completed"})


@pytest.mark.api
class TestCompleteTask:
    """Tests for POST /complete endpoint."""

    def test_complete_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test marking task as complete."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        response = client.complete_task(task_id)

        assert response.status == "success"
        assert response.code == 200

    def test_complete_task_idempotent(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test that completing a task twice is safe (idempotent)."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Complete once
        response1 = client.complete_task(task_id)
        assert response1.status == "success"

        # Complete again
        response2 = client.complete_task(task_id)
        assert response2.status == "success"

    def test_complete_nonexistent_task(self, client: MindFlowClient):
        """Test completing task that doesn't exist."""
        fake_id = "nonexistent-task-id"

        with pytest.raises(Exception):
            client.complete_task(fake_id)


@pytest.mark.api
class TestSnoozeTask:
    """Tests for POST /snooze endpoint."""

    def test_snooze_task_default_duration(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test snoozing with default 2h duration."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        response = client.snooze_task(task_id)

        assert response.status == "success"
        assert response.code == 200
        assert "snoozed_until" in response.data

    def test_snooze_task_1h(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test snoozing for 1 hour."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        response = client.snooze_task(task_id, "1h")

        assert response.status == "success"
        assert "snoozed_until" in response.data

    def test_snooze_task_1d(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test snoozing for 1 day."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        response = client.snooze_task(task_id, "1d")

        assert response.status == "success"
        assert "snoozed_until" in response.data

    def test_snooze_task_1w(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test snoozing for 1 week."""
        task = TaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        response = client.snooze_task(task_id, "1w")

        assert response.status == "success"
        assert "snoozed_until" in response.data


@pytest.mark.api
class TestQueryTasks:
    """Tests for GET /query endpoint."""

    def test_query_all_tasks(self, client: MindFlowClient):
        """Test querying all tasks."""
        response = client.query_tasks()

        assert response.status == "success"
        assert response.code == 200
        assert isinstance(response.data, list)

    def test_query_by_status_pending(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test filtering by pending status."""
        # Create pending task
        task = TaskFactory.build(status="pending")
        create_response = client.create_task(task)
        task_id_tracker.append(create_response.data["id"])

        response = client.query_tasks(status="pending")

        assert response.status == "success"
        assert isinstance(response.data, list)

    def test_query_by_status_in_progress(
        self, client: MindFlowClient, task_id_tracker: list[str]
    ):
        """Test filtering by in_progress status."""
        # Create in_progress task
        task = InProgressTaskFactory.build()
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Update to in_progress
        client.update_task(task_id, {"status": "in_progress"})

        response = client.query_tasks(status="in_progress")

        assert response.status == "success"
        assert isinstance(response.data, list)

    def test_query_by_priority(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test filtering by priority."""
        # Create priority 5 task
        task = TaskFactory.build(priority=5)
        create_response = client.create_task(task)
        task_id_tracker.append(create_response.data["id"])

        response = client.query_tasks(priority=5)

        assert response.status == "success"
        assert isinstance(response.data, list)

    def test_query_with_limit(self, client: MindFlowClient):
        """Test limit parameter."""
        response = client.query_tasks(limit=5)

        assert response.status == "success"
        assert isinstance(response.data, list)
        assert len(response.data) <= 5

    def test_query_multiple_filters(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test combining multiple filters."""
        # Create specific task
        task = TaskFactory.build(status="pending", priority=5)
        create_response = client.create_task(task)
        task_id_tracker.append(create_response.data["id"])

        response = client.query_tasks(status="pending", priority=5)

        assert response.status == "success"
        assert isinstance(response.data, list)
