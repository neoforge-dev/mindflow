"""Tests for task scoring endpoint - /api/tasks/best."""

from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_best_task_returns_highest_score(authenticated_client, db_session):
    """GET /api/tasks/best returns task with highest score."""
    from app.db.crud import TaskCRUD

    # Create low priority task (score: 0 * 40 + 2 * 10 + 0 = 20)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Low priority task",
            "priority": 2,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    # Create high priority task (score: 0 * 40 + 5 * 10 + 0 = 50)
    high_priority = await TaskCRUD.create(
        db_session,
        {
            "title": "High priority task",
            "priority": 5,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    # Create overdue task (score: 1.25 * 40 + 3 * 10 + 0 = 80)
    overdue_date = datetime.utcnow() - timedelta(days=1)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Overdue task",
            "priority": 3,
            "due_date": overdue_date,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 200
    data = response.json()
    assert "task" in data
    assert "score" in data
    assert "reasoning" in data

    # The overdue task should be selected (highest score)
    assert data["task"]["title"] == "Overdue task"
    assert data["score"] == 80.0


@pytest.mark.asyncio
async def test_best_task_excludes_completed(authenticated_client, db_session):
    """GET /api/tasks/best excludes completed tasks."""
    from app.db.crud import TaskCRUD

    # Create completed high-priority task (should be ignored)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Completed high priority",
            "priority": 5,
            "status": "completed",
            "user_id": authenticated_client.user_id,
        },
    )

    # Create pending low-priority task (should be selected)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Pending low priority",
            "priority": 2,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 200
    data = response.json()
    assert data["task"]["title"] == "Pending low priority"
    assert data["task"]["status"] == "pending"


@pytest.mark.asyncio
async def test_best_task_excludes_snoozed(authenticated_client, db_session):
    """GET /api/tasks/best excludes snoozed tasks."""
    from app.db.crud import TaskCRUD

    # Create snoozed high-priority task (should be ignored)
    future_time = datetime.utcnow() + timedelta(hours=2)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Snoozed high priority",
            "priority": 5,
            "status": "snoozed",
            "snoozed_until": future_time,
            "user_id": authenticated_client.user_id,
        },
    )

    # Create pending low-priority task (should be selected)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Pending task",
            "priority": 2,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 200
    data = response.json()
    assert data["task"]["title"] == "Pending task"


@pytest.mark.asyncio
async def test_best_task_returns_404_when_no_tasks(authenticated_client, db_session):
    """GET /api/tasks/best returns 404 when no pending tasks."""
    # No tasks created
    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 404
    assert "No pending tasks" in response.json()["detail"]


@pytest.mark.asyncio
async def test_best_task_includes_reasoning(authenticated_client, db_session):
    """GET /api/tasks/best includes transparent reasoning."""
    from app.db.crud import TaskCRUD

    # Create quick win task
    await TaskCRUD.create(
        db_session,
        {
            "title": "Quick task",
            "priority": 3,
            "effort_estimate_minutes": 10,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 200
    data = response.json()

    # Verify reasoning structure
    reasoning = data["reasoning"]
    assert "deadline_urgency" in reasoning
    assert "priority_score" in reasoning
    assert "effort_bonus" in reasoning
    assert "total_score" in reasoning
    assert "recommendation" in reasoning

    # Verify values
    assert reasoning["deadline_urgency"] == 0.0  # No deadline
    assert reasoning["priority_score"] == 30  # 3 * 10
    assert reasoning["effort_bonus"] == 10  # 1.0 * 10 for quick task
    assert reasoning["total_score"] == 40.0  # (0 + 30 + 10) * 1.0
    assert isinstance(reasoning["recommendation"], str)
    assert len(reasoning["recommendation"]) > 0


@pytest.mark.asyncio
async def test_best_task_considers_effort_estimate(authenticated_client, db_session):
    """GET /api/tasks/best favors quick wins."""
    from app.db.crud import TaskCRUD

    # Create long task (score: 0 * 40 + 3 * 10 + 0.25 * 10 = 32.5)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Long task",
            "priority": 3,
            "effort_estimate_minutes": 120,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    # Create quick task (score: 0 * 40 + 3 * 10 + 1.0 * 10 = 40)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Quick task",
            "priority": 3,
            "effort_estimate_minutes": 10,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 200
    data = response.json()
    # Quick task should win despite same priority
    assert data["task"]["title"] == "Quick task"
    assert data["score"] == 40.0
