"""
Factory Boy factories for generating realistic test data.

Uses factory_boy with Faker to create diverse, realistic task data
for testing edge cases and various scenarios.
"""

from datetime import datetime, timedelta
from typing import Any

import factory
from factory import Faker, LazyAttribute, Sequence, fuzzy


class TaskFactory(factory.Factory):
    """Factory for creating realistic task data."""

    class Meta:
        model = dict

    id = Sequence(lambda n: f"task-{n:04d}")
    title = Faker("sentence", nb_words=6)
    description = Faker("paragraph", nb_sentences=3)
    status = fuzzy.FuzzyChoice(["pending", "in_progress", "completed", "snoozed"])
    priority = fuzzy.FuzzyInteger(1, 5)
    due_date = Faker("future_datetime", end_date="+30d", tzinfo=None)
    snoozed_until = None
    created_at = Faker("past_datetime", start_date="-30d", tzinfo=None)
    updated_at = LazyAttribute(lambda obj: obj.created_at)

    @classmethod
    def _adjust_kwargs(cls, **kwargs: Any) -> dict[str, Any]:
        """Convert datetime objects to ISO8601 strings."""
        for key in ["due_date", "created_at", "updated_at", "snoozed_until"]:
            if key in kwargs and kwargs[key] is not None:
                if isinstance(kwargs[key], datetime):
                    kwargs[key] = kwargs[key].strftime("%Y-%m-%dT%H:%M:%SZ")
        return kwargs


class UrgentTaskFactory(TaskFactory):
    """Factory for urgent, high-priority tasks."""

    title = Faker("sentence", nb_words=4)
    status = "pending"
    priority = 5
    due_date = Faker("future_datetime", end_date="+2d", tzinfo=None)


class OverdueTaskFactory(TaskFactory):
    """Factory for overdue tasks."""

    title = Faker("sentence", nb_words=5)
    status = "pending"
    priority = fuzzy.FuzzyInteger(3, 5)
    due_date = Faker("past_datetime", start_date="-7d", tzinfo=None)


class InProgressTaskFactory(TaskFactory):
    """Factory for tasks currently being worked on."""

    status = "in_progress"
    priority = fuzzy.FuzzyInteger(3, 5)
    due_date = Faker("future_datetime", end_date="+7d", tzinfo=None)


class SnoozedTaskFactory(TaskFactory):
    """Factory for snoozed tasks."""

    status = "snoozed"
    priority = fuzzy.FuzzyInteger(2, 4)
    due_date = Faker("future_datetime", end_date="+14d", tzinfo=None)
    snoozed_until = Faker("future_datetime", end_date="+3d", tzinfo=None)


class CompletedTaskFactory(TaskFactory):
    """Factory for completed tasks."""

    status = "completed"
    priority = fuzzy.FuzzyInteger(1, 5)
    due_date = Faker("past_datetime", start_date="-14d", tzinfo=None)
    created_at = Faker("past_datetime", start_date="-30d", tzinfo=None)
    updated_at = Faker("past_datetime", start_date="-7d", tzinfo=None)


class LowPriorityTaskFactory(TaskFactory):
    """Factory for low-priority, nice-to-have tasks."""

    title = Faker("sentence", nb_words=8)
    status = "pending"
    priority = fuzzy.FuzzyInteger(1, 2)
    due_date = Faker("future_datetime", end_date="+60d", tzinfo=None)


class EdgeCaseTaskFactory(TaskFactory):
    """Factory for edge case scenarios."""

    pass


# Edge Case Factories


class EmptyDescriptionTaskFactory(TaskFactory):
    """Task with no description."""

    description = ""


class VeryLongTitleTaskFactory(TaskFactory):
    """Task with extremely long title (boundary test)."""

    title = Faker("text", max_nb_chars=250)


class MaxLengthTitleTaskFactory(TaskFactory):
    """Task with exactly 256 character title."""

    title = LazyAttribute(lambda _: "A" * 256)


class NoDueDateTaskFactory(TaskFactory):
    """Task with no due date."""

    due_date = None


class FarFutureDueDateTaskFactory(TaskFactory):
    """Task due far in the future."""

    due_date = Faker("future_datetime", end_date="+365d", tzinfo=None)


class DueTodayTaskFactory(TaskFactory):
    """Task due today (urgent)."""

    status = "pending"
    priority = fuzzy.FuzzyInteger(4, 5)
    due_date = LazyAttribute(
        lambda _: (datetime.utcnow() + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class DueInOneHourTaskFactory(TaskFactory):
    """Task due in one hour (critical)."""

    status = "pending"
    priority = 5
    due_date = LazyAttribute(
        lambda _: (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class JustSnoozedTaskFactory(TaskFactory):
    """Task that was just snoozed (edge case for filtering)."""

    status = "snoozed"
    snoozed_until = LazyAttribute(
        lambda _: (datetime.utcnow() + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class SnoozedExpiredTaskFactory(TaskFactory):
    """Task whose snooze period has expired (should appear active)."""

    status = "snoozed"
    snoozed_until = Faker("past_datetime", start_date="-2d", tzinfo=None)


class OldPendingTaskFactory(TaskFactory):
    """Very old pending task (momentum test)."""

    status = "pending"
    priority = fuzzy.FuzzyInteger(2, 4)
    created_at = Faker("past_datetime", start_date="-90d", tzinfo=None)
    due_date = Faker("future_datetime", end_date="+7d", tzinfo=None)


class SpecialCharactersTitleTaskFactory(TaskFactory):
    """Task with special characters in title."""

    title = "Task with émojis 🎯 and spëcial çhars: <>&\"'"


class UnicodeTaskFactory(TaskFactory):
    """Task with unicode characters."""

    title = "任务 with 中文字符 and العربية and עִבְרִית"
    description = "Тестовое задание с unicode символами 🌍🚀"


# Test Data Sets


class TestDataSets:
    """Pre-configured sets of test data for different scenarios."""

    @staticmethod
    def realistic_mixed_tasks(count: int = 20) -> list[dict[str, Any]]:
        """Generate a realistic mix of tasks."""
        return [
            UrgentTaskFactory(),
            UrgentTaskFactory(),
            InProgressTaskFactory(),
            InProgressTaskFactory(),
            InProgressTaskFactory(),
            OverdueTaskFactory(),
            SnoozedTaskFactory(),
            SnoozedTaskFactory(),
            CompletedTaskFactory(),
            CompletedTaskFactory(),
            CompletedTaskFactory(),
            CompletedTaskFactory(),
            LowPriorityTaskFactory(),
            LowPriorityTaskFactory(),
            LowPriorityTaskFactory(),
            *[TaskFactory() for _ in range(count - 15)],
        ]

    @staticmethod
    def edge_cases() -> list[dict[str, Any]]:
        """Generate edge case tasks."""
        return [
            # Boundary tests
            MaxLengthTitleTaskFactory(),
            VeryLongTitleTaskFactory(),
            EmptyDescriptionTaskFactory(),
            NoDueDateTaskFactory(),
            # Timing edge cases
            DueTodayTaskFactory(),
            DueInOneHourTaskFactory(),
            OverdueTaskFactory(),
            FarFutureDueDateTaskFactory(),
            # Status edge cases
            JustSnoozedTaskFactory(),
            SnoozedExpiredTaskFactory(),
            OldPendingTaskFactory(),
            # Character encoding
            SpecialCharactersTitleTaskFactory(),
            UnicodeTaskFactory(),
            # Priority boundaries
            TaskFactory(priority=1),  # Minimum
            TaskFactory(priority=5),  # Maximum
        ]

    @staticmethod
    def scoring_test_set() -> list[dict[str, Any]]:
        """Generate tasks specifically for testing scoring algorithm."""
        now = datetime.utcnow()

        return [
            # Priority variations (same due date)
            TaskFactory(
                title="Priority 5 - Same Due",
                priority=5,
                status="pending",
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Priority 4 - Same Due",
                priority=4,
                status="pending",
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Priority 3 - Same Due",
                priority=3,
                status="pending",
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Priority 2 - Same Due",
                priority=2,
                status="pending",
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Priority 1 - Same Due",
                priority=1,
                status="pending",
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            # Urgency variations (same priority)
            TaskFactory(
                title="Overdue",
                priority=3,
                status="pending",
                due_date=(now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Due in 2 hours",
                priority=3,
                status="pending",
                due_date=(now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Due in 12 hours",
                priority=3,
                status="pending",
                due_date=(now + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Due in 2 days",
                priority=3,
                status="pending",
                due_date=(now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Due in 30 days",
                priority=3,
                status="pending",
                due_date=(now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            # Momentum variations
            TaskFactory(
                title="In Progress",
                priority=3,
                status="in_progress",
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            TaskFactory(
                title="Created 30 days ago",
                priority=3,
                status="pending",
                created_at=(now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                due_date=(now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        ]

    @staticmethod
    def empty_state() -> list[dict[str, Any]]:
        """No tasks (empty state test)."""
        return []

    @staticmethod
    def only_completed() -> list[dict[str, Any]]:
        """Only completed tasks (no active tasks)."""
        return [CompletedTaskFactory() for _ in range(10)]

    @staticmethod
    def only_snoozed() -> list[dict[str, Any]]:
        """Only snoozed tasks (no active tasks)."""
        return [SnoozedTaskFactory() for _ in range(5)]

    @staticmethod
    def high_volume() -> list[dict[str, Any]]:
        """Large number of tasks (performance test)."""
        return [TaskFactory() for _ in range(100)]
