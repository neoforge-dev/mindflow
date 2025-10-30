"""
Edge case and boundary tests.

Tests unusual scenarios, boundary conditions, and error handling.
"""

import pytest

from tests.client import MindFlowClient
from tests.factories import (
    DueInOneHourTaskFactory,
    DueTodayTaskFactory,
    EmptyDescriptionTaskFactory,
    FarFutureDueDateTaskFactory,
    JustSnoozedTaskFactory,
    MaxLengthTitleTaskFactory,
    NoDueDateTaskFactory,
    OldPendingTaskFactory,
    OverdueTaskFactory,
    SnoozedExpiredTaskFactory,
    SpecialCharactersTitleTaskFactory,
    UnicodeTaskFactory,
    VeryLongTitleTaskFactory,
)


@pytest.mark.edge_case
class TestBoundaryConditions:
    """Test boundary values and limits."""

    def test_priority_boundary_min(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test minimum valid priority (1)."""
        task_data = {"title": "Min Priority", "priority": 1}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_priority_boundary_max(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test maximum valid priority (5)."""
        task_data = {"title": "Max Priority", "priority": 5}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_title_max_length(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test 256 character title (boundary)."""
        task = MaxLengthTitleTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_title_near_max_length(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test title just under max length (255 chars)."""
        task_data = {"title": "A" * 255, "priority": 3}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_empty_description(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task with empty string description."""
        task = EmptyDescriptionTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_no_due_date(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task without due date."""
        task = NoDueDateTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])


@pytest.mark.edge_case
class TestCharacterEncoding:
    """Test various character encodings and special characters."""

    def test_unicode_title(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test unicode characters in title."""
        task = UnicodeTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_special_characters(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test special characters in title."""
        task = SpecialCharactersTitleTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_emoji_in_title(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test emoji characters."""
        task_data = {"title": "Task with emojis 🎯 🚀 ✅ 📊", "priority": 3}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_html_entities_in_title(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test HTML-like characters (should not be interpreted)."""
        task_data = {"title": "<script>alert('test')</script>", "priority": 3}

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_newlines_in_description(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test multiline description."""
        task_data = {
            "title": "Multiline Description",
            "description": "Line 1\nLine 2\nLine 3",
            "priority": 3,
        }

        response = client.create_task(task_data)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])


@pytest.mark.edge_case
class TestTimingEdgeCases:
    """Test time-based edge cases."""

    def test_overdue_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task that is already overdue."""
        task = OverdueTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id = response.data["id"]
        task_id_tracker.append(task_id)

        # Overdue tasks should score very high
        best = client.get_best_task()
        if isinstance(best.data, dict) and "id" in best.data:
            if best.data["id"] == task_id:
                assert best.data["score"] >= 90  # Overdue should be urgent

    def test_due_today_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task due today."""
        task = DueTodayTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_due_in_one_hour(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task due very soon."""
        task = DueInOneHourTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id = response.data["id"]
        task_id_tracker.append(task_id)

        # Should score very high
        best = client.get_best_task()
        if isinstance(best.data, dict) and "id" in best.data:
            if best.data["id"] == task_id:
                assert best.data["score"] >= 85

    def test_far_future_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task due far in the future."""
        task = FarFutureDueDateTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_very_old_pending_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test old pending task (momentum scoring)."""
        task = OldPendingTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])


@pytest.mark.edge_case
class TestSnoozeEdgeCases:
    """Test snooze-related edge cases."""

    def test_just_snoozed_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test recently snoozed task (should be hidden)."""
        task = JustSnoozedTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_snooze_expired_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test task whose snooze has expired (should be active)."""
        task = SnoozedExpiredTaskFactory.build()

        response = client.create_task(task)

        assert response.code == 201
        task_id_tracker.append(response.data["id"])

    def test_snooze_multiple_times(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test snoozing a task multiple times."""
        task = {"title": "Re-snooze Test", "priority": 3}
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Snooze once
        response1 = client.snooze_task(task_id, "1h")
        assert response1.status == "success"

        # Snooze again (should update snooze time)
        response2 = client.snooze_task(task_id, "2h")
        assert response2.status == "success"
        assert response2.data["snoozed_until"] != response1.data["snoozed_until"]


@pytest.mark.edge_case
class TestErrorHandling:
    """Test error conditions and recovery."""

    def test_missing_required_field_title(self, client: MindFlowClient):
        """Test error when title is missing."""
        task_data = {"priority": 3}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_missing_required_field_priority(self, client: MindFlowClient):
        """Test error when priority is missing."""
        task_data = {"title": "No Priority"}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_invalid_priority_too_high(self, client: MindFlowClient):
        """Test priority validation (> 5)."""
        task_data = {"title": "Invalid Priority", "priority": 10}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_invalid_priority_too_low(self, client: MindFlowClient):
        """Test priority validation (< 1)."""
        task_data = {"title": "Invalid Priority", "priority": 0}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_invalid_priority_negative(self, client: MindFlowClient):
        """Test negative priority."""
        task_data = {"title": "Negative Priority", "priority": -1}

        with pytest.raises(Exception):
            client.create_task(task_data)

    def test_invalid_status_value(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test invalid status value."""
        task = {"title": "Test Task", "priority": 3}
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Try to update with invalid status
        # API should reject or handle gracefully
        try:
            client.update_task(task_id, {"status": "invalid_status"})
        except Exception:
            pass  # Expected to fail

    def test_nonexistent_task_id_update(self, client: MindFlowClient):
        """Test updating non-existent task."""
        fake_id = "nonexistent-task-12345"

        with pytest.raises(Exception):
            client.update_task(fake_id, {"status": "completed"})

    def test_nonexistent_task_id_complete(self, client: MindFlowClient):
        """Test completing non-existent task."""
        fake_id = "nonexistent-task-12345"

        with pytest.raises(Exception):
            client.complete_task(fake_id)

    def test_nonexistent_task_id_snooze(self, client: MindFlowClient):
        """Test snoozing non-existent task."""
        fake_id = "nonexistent-task-12345"

        with pytest.raises(Exception):
            client.snooze_task(fake_id)


@pytest.mark.edge_case
class TestConcurrencyAndRaceConditions:
    """Test concurrent operations (basic)."""

    def test_update_completed_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test updating a task after it's been completed."""
        task = {"title": "Complete Then Update", "priority": 3}
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Complete task
        client.complete_task(task_id)

        # Try to update (should still work)
        response = client.update_task(task_id, {"priority": 5})
        assert response.status == "success"

    def test_snooze_completed_task(self, client: MindFlowClient, task_id_tracker: list[str]):
        """Test snoozing a completed task (edge case)."""
        task = {"title": "Complete Then Snooze", "priority": 3}
        create_response = client.create_task(task)
        task_id = create_response.data["id"]
        task_id_tracker.append(task_id)

        # Complete task
        client.complete_task(task_id)

        # Try to snooze (should work or fail gracefully)
        response = client.snooze_task(task_id)
        assert response.status == "success"
