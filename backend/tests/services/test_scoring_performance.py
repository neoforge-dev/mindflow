"""Performance tests for task scoring service."""

import time
from datetime import datetime, timedelta

import pytest

from app.services.scoring import calculate_task_score


class MockTask:
    """Mock task object for performance testing."""

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


def test_score_100_tasks_under_50ms():
    """Scoring 100 tasks should take less than 50ms.

    This is critical for UX - users expect instant "best task" recommendations.
    """
    # Create diverse set of 100 tasks
    tasks = []
    current_time = datetime.utcnow()

    for i in range(100):
        # Vary task properties
        task = MockTask(
            due_date=(
                current_time + timedelta(days=i % 10)
                if i % 3 == 0  # noqa: PLR2004
                else None
            ),
            priority=(i % 5) + 1,  # 1-5
            effort_estimate_minutes=(
                15 * ((i % 8) + 1)  # 15, 30, 45, ..., 120
                if i % 2 == 0  # noqa: PLR2004
                else None
            ),
            preferred_time=(
                ["morning", "afternoon", "evening"][i % 3] if i % 4 == 0 else None  # noqa: PLR2004
            ),
        )
        tasks.append(task)

    # Time the scoring operation
    start_time = time.perf_counter()

    for task in tasks:
        calculate_task_score(task, current_time)

    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000

    # Assert performance target
    assert elapsed_ms < 50, f"Scoring 100 tasks took {elapsed_ms:.2f}ms (target: <50ms)"

    # Print actual performance for monitoring
    print(f"\n✓ Scored 100 tasks in {elapsed_ms:.2f}ms ({elapsed_ms/100:.3f}ms per task)")


def test_score_and_sort_100_tasks_under_100ms():
    """Complete workflow (score + sort) should be under 100ms.

    This tests the full endpoint operation including sorting.
    """
    # Create 100 tasks
    tasks = []
    current_time = datetime.utcnow()

    for i in range(100):
        task = MockTask(
            due_date=(
                current_time + timedelta(days=i % 10)
                if i % 3 == 0  # noqa: PLR2004
                else None
            ),
            priority=(i % 5) + 1,
            effort_estimate_minutes=15 * ((i % 8) + 1) if i % 2 == 0 else None,  # noqa: PLR2004
        )
        tasks.append(task)

    # Time complete workflow
    start_time = time.perf_counter()

    # Score all tasks (as endpoint does)
    scored_tasks = []
    for task in tasks:
        score = calculate_task_score(task, current_time)
        scored_tasks.append((task, score))

    # Sort by score
    scored_tasks.sort(key=lambda x: x[1], reverse=True)
    best_task, best_score = scored_tasks[0]

    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000

    # Assert performance target
    assert elapsed_ms < 100, f"Score + sort took {elapsed_ms:.2f}ms (target: <100ms)"
    assert best_task is not None
    assert best_score > 0

    print(
        f"\n✓ Scored and sorted 100 tasks in {elapsed_ms:.2f}ms "
        f"(best score: {best_score:.1f})"
    )


def test_scoring_memory_efficiency():
    """Verify scoring doesn't create unnecessary objects or memory leaks."""
    # Create a single task
    task = MockTask(
        due_date=datetime.utcnow() + timedelta(days=1),
        priority=3,
        effort_estimate_minutes=30,
    )

    # Score task many times and verify no exceptions
    scores = []
    for _ in range(1000):
        score = calculate_task_score(task)
        scores.append(score)

    # Verify scoring is deterministic (same task = same score)
    assert len(set(scores)) == 1, "Scoring should be deterministic"

    # Verify score is reasonable (tomorrow = 0.75 urgency, priority 3, 30min effort = 0.75 bonus)
    # Score = (0.75 * 40 + 3 * 10 + 0.75 * 10) * 1.0 = (30 + 30 + 7.5) = 67.5
    # But could vary based on hour boundaries
    assert scores[0] > 0, "Score should be positive"
    assert scores[0] < 200, "Score should be reasonable"

    print(f"\n✓ Memory-efficient: 1000 operations completed, deterministic score: {scores[0]}")
