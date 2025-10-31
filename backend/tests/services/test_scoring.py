"""Tests for task scoring service."""

from datetime import datetime, timedelta

import pytest

from app.services.scoring import (
    calculate_deadline_urgency,
    calculate_effort_bonus,
    calculate_task_score,
    calculate_time_of_day_multiplier,
)


class MockTask:
    """Mock task object for testing."""

    def __init__(
        self,
        due_date=None,
        priority=3,
        effort_estimate_minutes=None,
        preferred_time=None,
    ):
        self.due_date = due_date
        self.priority = priority
        self.effort_estimate_minutes = effort_estimate_minutes
        self.preferred_time = preferred_time


class TestDeadlineUrgency:
    """Test deadline urgency calculation."""

    def test_overdue_task_has_highest_urgency(self):
        """Overdue tasks should get 1.25 multiplier."""
        overdue = datetime.utcnow() - timedelta(days=1)
        urgency = calculate_deadline_urgency(overdue)
        assert urgency == 1.25

    def test_due_today_has_full_urgency(self):
        """Tasks due today should get 1.0 urgency."""
        today = datetime.utcnow() + timedelta(hours=12)  # Later today
        urgency = calculate_deadline_urgency(today)
        assert urgency == 1.0

    def test_due_tomorrow_reduced_urgency(self):
        """Tasks due tomorrow should get 0.75 urgency."""
        # Tomorrow means more than 24 hours but less than 48
        tomorrow = datetime.utcnow() + timedelta(hours=30)
        urgency = calculate_deadline_urgency(tomorrow)
        assert urgency == 0.75

    def test_due_this_week_moderate_urgency(self):
        """Tasks due within a week should get 0.5 urgency."""
        next_week = datetime.utcnow() + timedelta(days=5)
        urgency = calculate_deadline_urgency(next_week)
        assert urgency == 0.5

    def test_due_later_low_urgency(self):
        """Tasks due later should get 0.25 urgency."""
        later = datetime.utcnow() + timedelta(days=14)
        urgency = calculate_deadline_urgency(later)
        assert urgency == 0.25

    def test_no_deadline_zero_urgency(self):
        """Tasks without deadline should get 0.0 urgency."""
        urgency = calculate_deadline_urgency(None)
        assert urgency == 0.0


class TestEffortBonus:
    """Test effort bonus calculation."""

    def test_quick_tasks_get_effort_bonus(self):
        """Tasks ≤15 minutes should get full bonus."""
        bonus = calculate_effort_bonus(15)
        assert bonus == 1.0

        bonus = calculate_effort_bonus(10)
        assert bonus == 1.0

    def test_short_tasks_get_high_bonus(self):
        """Tasks ≤30 minutes should get 0.75 bonus."""
        bonus = calculate_effort_bonus(30)
        assert bonus == 0.75

    def test_medium_tasks_get_moderate_bonus(self):
        """Tasks ≤60 minutes should get 0.5 bonus."""
        bonus = calculate_effort_bonus(60)
        assert bonus == 0.5

    def test_long_tasks_get_low_bonus(self):
        """Tasks >60 minutes should get 0.25 bonus."""
        bonus = calculate_effort_bonus(120)
        assert bonus == 0.25

    def test_no_estimate_zero_bonus(self):
        """Tasks without effort estimate should get 0.0 bonus."""
        bonus = calculate_effort_bonus(None)
        assert bonus == 0.0


class TestTimeOfDayMultiplier:
    """Test time of day multiplier calculation."""

    def test_time_of_day_bonus_morning(self):
        """Morning tasks at 9am should get 1.1x multiplier."""
        multiplier = calculate_time_of_day_multiplier("morning", 9)
        assert multiplier == 1.1

        # Test early morning boundary
        multiplier = calculate_time_of_day_multiplier("morning", 6)
        assert multiplier == 1.1

        # Test late morning boundary
        multiplier = calculate_time_of_day_multiplier("morning", 11)
        assert multiplier == 1.1

    def test_time_of_day_bonus_afternoon(self):
        """Afternoon tasks at 3pm should get 1.1x multiplier."""
        multiplier = calculate_time_of_day_multiplier("afternoon", 15)
        assert multiplier == 1.1

        # Test boundaries
        multiplier = calculate_time_of_day_multiplier("afternoon", 12)
        assert multiplier == 1.1

        multiplier = calculate_time_of_day_multiplier("afternoon", 17)
        assert multiplier == 1.1

    def test_time_of_day_bonus_evening(self):
        """Evening tasks at 8pm should get 1.1x multiplier."""
        multiplier = calculate_time_of_day_multiplier("evening", 20)
        assert multiplier == 1.1

        # Test boundaries
        multiplier = calculate_time_of_day_multiplier("evening", 18)
        assert multiplier == 1.1

        multiplier = calculate_time_of_day_multiplier("evening", 21)
        assert multiplier == 1.1

    def test_time_of_day_penalty_wrong(self):
        """Morning task at 8pm should get 0.9x penalty."""
        multiplier = calculate_time_of_day_multiplier("morning", 20)
        assert multiplier == 0.9

        # Afternoon task in morning
        multiplier = calculate_time_of_day_multiplier("afternoon", 10)
        assert multiplier == 0.9

        # Evening task in morning
        multiplier = calculate_time_of_day_multiplier("evening", 9)
        assert multiplier == 0.9

    def test_no_time_preference_neutral(self):
        """Tasks without time preference should get 1.0x."""
        multiplier = calculate_time_of_day_multiplier(None, 15)
        assert multiplier == 1.0


class TestTaskScore:
    """Test complete task scoring."""

    def test_high_priority_increases_score(self):
        """Priority 5 task should score higher than priority 1."""
        high_priority = MockTask(priority=5)
        low_priority = MockTask(priority=1)

        high_score = calculate_task_score(high_priority)
        low_score = calculate_task_score(low_priority)

        assert high_score > low_score
        # Priority difference is 4 * 10 = 40 points
        assert high_score - low_score == 40.0

    def test_overdue_task_highest_score(self):
        """Overdue tasks should have highest urgency score."""
        overdue = datetime.utcnow() - timedelta(days=1)
        task = MockTask(due_date=overdue, priority=3)

        score = calculate_task_score(task)

        # Score = (1.25 * 40 + 3 * 10 + 0) * 1.0 = 50 + 30 = 80
        assert score == 80.0

    def test_quick_win_bonus(self):
        """Quick tasks should get effort bonus."""
        quick_task = MockTask(priority=3, effort_estimate_minutes=15)
        long_task = MockTask(priority=3, effort_estimate_minutes=120)

        quick_score = calculate_task_score(quick_task)
        long_score = calculate_task_score(long_task)

        # Quick: (0 * 40 + 3 * 10 + 1.0 * 10) * 1.0 = 40
        # Long: (0 * 40 + 3 * 10 + 0.25 * 10) * 1.0 = 32.5
        assert quick_score == 40.0
        assert long_score == 32.5
        assert quick_score > long_score

    def test_time_of_day_affects_score(self):
        """Time preference should affect final score."""
        task = MockTask(priority=3, preferred_time="morning")

        # Mock time injection
        morning_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
        evening_time = datetime.utcnow().replace(hour=20, minute=0, second=0, microsecond=0)

        morning_score = calculate_task_score(task, morning_time)
        evening_score = calculate_task_score(task, evening_time)

        # Base score: (0 * 40 + 3 * 10 + 0) = 30
        # Morning: 30 * 1.1 = 33.0
        # Evening: 30 * 0.9 = 27.0
        assert morning_score == 33.0
        assert evening_score == 27.0
        assert morning_score > evening_score

    def test_comprehensive_scoring(self):
        """Test task with all factors."""
        due_today = datetime.utcnow() + timedelta(hours=6)
        task = MockTask(
            due_date=due_today,
            priority=5,
            effort_estimate_minutes=15,
            preferred_time="morning",
        )

        morning_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
        score = calculate_task_score(task, morning_time)

        # Score = (1.0 * 40 + 5 * 10 + 1.0 * 10) * 1.1
        # = (40 + 50 + 10) * 1.1 = 100 * 1.1 = 110.0
        assert pytest.approx(score, rel=1e-9) == 110.0
