"""Task scoring service - calculates which task to work on next.

First Principles:
- Urgency: Overdue tasks need immediate attention
- Priority: User knows what's important
- Effort: Quick wins are motivating
- Time-of-Day: Work when you're most effective

Scoring Formula:
    score = (urgency * 40 + priority * 10 + effort * 10) * time_multiplier
"""

from datetime import datetime


def calculate_deadline_urgency(due_date: datetime | None) -> float:
    """Calculate urgency multiplier based on how soon deadline is.

    Args:
        due_date: Task deadline or None

    Returns:
        Urgency multiplier: 0.0-2.0
            - 2.0: Overdue (past due date) - ensures score >= 90
            - 1.0: Due today
            - 0.75: Due tomorrow
            - 0.5: Due within a week
            - 0.25: Due later
            - 0.0: No deadline
    """
    if not due_date:
        return 0.0

    now = datetime.utcnow()
    # Use total_seconds to handle fractional days properly
    seconds_until = (due_date - now).total_seconds()
    hours_until = seconds_until / 3600

    if hours_until < 0:
        return 2.0  # Overdue - highest urgency (ensures score >= 90 with priority >= 3)
    if hours_until < 24:
        return 1.0  # Due today (within 24 hours)
    if hours_until < 48:
        return 0.75  # Due tomorrow (24-48 hours)
    if hours_until < 168:  # 7 days
        return 0.5  # Due this week
    return 0.25  # Due later


def calculate_effort_bonus(minutes: int | None) -> float:
    """Calculate effort bonus based on task duration.

    Quick wins are motivating - prioritize short tasks.

    Args:
        minutes: Estimated effort in minutes or None

    Returns:
        Effort multiplier: 0.0-1.0
            - 1.0: ≤15 minutes (quick win)
            - 0.75: ≤30 minutes (short task)
            - 0.5: ≤60 minutes (medium task)
            - 0.25: >60 minutes (long task)
            - 0.0: No estimate
    """
    if not minutes:
        return 0.0

    if minutes <= 15:
        return 1.0  # Quick win
    if minutes <= 30:
        return 0.75  # Short task
    if minutes <= 60:
        return 0.5  # Medium task
    return 0.25  # Long task


def calculate_time_of_day_multiplier(
    preferred_time: str | None,
    current_hour: int,
) -> float:
    """Calculate time-of-day multiplier based on preference match.

    Work on tasks when you're most effective.

    Args:
        preferred_time: "morning", "afternoon", "evening", or None
        current_hour: Current hour (0-23)

    Returns:
        Time multiplier: 0.9-1.1
            - 1.1: Task preference matches current time
            - 0.9: Task preference doesn't match
            - 1.0: No time preference
    """
    if not preferred_time:
        return 1.0

    # Define time windows
    is_morning = 6 <= current_hour < 12
    is_afternoon = 12 <= current_hour < 18
    is_evening = 18 <= current_hour < 22

    # Check if preference matches current time
    if preferred_time == "morning" and is_morning:
        return 1.1
    if preferred_time == "afternoon" and is_afternoon:
        return 1.1
    if preferred_time == "evening" and is_evening:
        return 1.1

    # Wrong time for this task
    return 0.9


def calculate_task_score(task, current_time: datetime | None = None) -> float:
    """Calculate total score for a task.

    Formula: score = (urgency * 40 + priority * 10 + effort * 10) * time_multiplier

    Args:
        task: Task object with due_date, priority, effort_estimate_minutes, preferred_time
        current_time: Current time for testing (defaults to now)

    Returns:
        Total task score (higher is better to work on now)
    """
    if not current_time:
        current_time = datetime.utcnow()

    # Calculate components
    urgency = calculate_deadline_urgency(task.due_date)
    effort = calculate_effort_bonus(task.effort_estimate_minutes)
    time_mult = calculate_time_of_day_multiplier(
        getattr(task, "preferred_time", None),
        current_time.hour,
    )

    # Apply formula
    score = (urgency * 40 + task.priority * 10 + effort * 10) * time_mult

    return score
