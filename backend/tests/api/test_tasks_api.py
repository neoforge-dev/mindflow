"""Task API endpoint tests - defines route order."""

from datetime import datetime, timedelta

import pytest

# ==============================================================================
# CREATE TASK TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_create_task_returns_201_with_task(authenticated_client):
    """POST /api/tasks returns 201 with created task."""
    response = await authenticated_client.post(
        "/api/tasks",
        json={"title": "New task", "priority": 3},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New task"
    assert data["priority"] == 3
    assert data["status"] == "pending"
    assert "id" in data
    assert data["user_id"] == str(authenticated_client.user_id)


@pytest.mark.asyncio
async def test_create_task_validates_required_fields(authenticated_client):
    """POST /api/tasks returns 422 if title missing."""
    response = await authenticated_client.post(
        "/api/tasks",
        json={"priority": 3},  # Missing title
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_validates_priority_range(authenticated_client):
    """POST /api/tasks returns 422 if priority outside 1-5."""
    response = await authenticated_client.post(
        "/api/tasks",
        json={"title": "Task", "priority": 10},  # Invalid priority
    )

    assert response.status_code == 422


# ==============================================================================
# GET PENDING TASKS TESTS (MUST BE BEFORE GET SINGLE TASK!)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_pending_tasks_returns_actionable_tasks(authenticated_client, db_session):
    """GET /api/tasks/pending returns pending and in_progress tasks."""
    from app.db.crud import TaskCRUD

    # Create pending task
    pending_task = await TaskCRUD.create(
        db_session,
        {
            "title": "Pending task",
            "status": "pending",
            "priority": 3,
            "user_id": authenticated_client.user_id,
        },
    )

    # Create in-progress task
    in_progress_task = await TaskCRUD.create(
        db_session,
        {
            "title": "In progress task",
            "status": "in_progress",
            "priority": 4,
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    task_ids = [t["id"] for t in data]
    assert str(pending_task.id) in task_ids
    assert str(in_progress_task.id) in task_ids


@pytest.mark.asyncio
async def test_get_pending_tasks_excludes_completed(authenticated_client, db_session):
    """GET /api/tasks/pending excludes completed tasks."""
    from app.db.crud import TaskCRUD

    # Create completed task
    await TaskCRUD.create(
        db_session,
        {
            "title": "Completed task",
            "status": "completed",
            "priority": 3,
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should not include completed task


@pytest.mark.asyncio
async def test_get_pending_tasks_excludes_snoozed(authenticated_client, db_session):
    """GET /api/tasks/pending excludes tasks with future snoozed_until."""
    from app.db.crud import TaskCRUD

    # Create snoozed task (future date)
    future = datetime.utcnow() + timedelta(hours=2)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Snoozed task",
            "status": "pending",
            "priority": 3,
            "snoozed_until": future,
            "user_id": authenticated_client.user_id,
        },
    )

    response = await authenticated_client.get("/api/tasks/pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should not include snoozed task


# ==============================================================================
# LIST TASKS TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_list_tasks_returns_200_with_tasks(authenticated_client, db_session):
    """GET /api/tasks returns 200 with user's tasks."""
    from app.db.crud import TaskCRUD

    # Create test task
    task = await TaskCRUD.create(
        db_session,
        {"title": "Test task", "priority": 3, "user_id": authenticated_client.user_id},
    )

    response = await authenticated_client.get("/api/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(t["id"] == str(task.id) for t in data)


@pytest.mark.asyncio
async def test_list_tasks_filters_by_status(authenticated_client, db_session):
    """GET /api/tasks?status=pending returns only pending tasks."""
    from app.db.crud import TaskCRUD

    # Create pending task
    pending = await TaskCRUD.create(
        db_session,
        {"title": "Pending", "status": "pending", "priority": 3, "user_id": authenticated_client.user_id},
    )

    # Create completed task
    await TaskCRUD.create(
        db_session,
        {"title": "Done", "status": "completed", "priority": 3, "user_id": authenticated_client.user_id},
    )

    response = await authenticated_client.get("/api/tasks?status=pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(pending.id)
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks_empty_for_new_user(test_client):
    """GET /api/tasks returns empty list for user with no tasks (using test registration)."""
    # Register and login new user
    await test_client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "testPassword123"},
    )
    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": "newuser@example.com", "password": "testPassword123"},
    )
    token = login_response.json()["access_token"]

    response = await test_client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data == []


# ==============================================================================
# GET SINGLE TASK TESTS (AFTER /pending ROUTE!)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_task_returns_200_with_task(authenticated_client, db_session):
    """GET /api/tasks/{id} returns 200 with task details."""
    from app.db.crud import TaskCRUD

    # Create task
    task = await TaskCRUD.create(
        db_session,
        {"title": "Get task test", "priority": 3, "user_id": authenticated_client.user_id},
    )

    response = await authenticated_client.get(f"/api/tasks/{task.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(task.id)
    assert data["title"] == task.title
    assert data["priority"] == task.priority


@pytest.mark.asyncio
async def test_get_task_returns_404_for_nonexistent(authenticated_client):
    """GET /api/tasks/{fake-id} returns 404 not found."""
    import uuid

    fake_id = uuid.uuid4()
    response = await authenticated_client.get(f"/api/tasks/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task_returns_404_for_other_user(test_client, db_session):
    """GET /api/tasks/{id} returns 404 if task belongs to different user."""
    from app.auth.security import create_access_token
    from app.db.crud import TaskCRUD, UserCRUD

    # Create user 1 and their task
    user1 = await UserCRUD.create(
        db_session,
        {
            "email": "user1@example.com",
            "password_hash": "hashed_password",
            "full_name": "User 1",
        },
    )
    task = await TaskCRUD.create(
        db_session, {"title": "User 1 task", "priority": 3, "user_id": user1.id}
    )

    # Create user 2 with JWT token
    user2 = await UserCRUD.create(
        db_session,
        {
            "email": "user2@example.com",
            "password_hash": "hashed_password",
            "full_name": "User 2",
        },
    )
    user2_token = create_access_token(data={"sub": str(user2.id)})

    # User 2 tries to access User 1's task
    response = await test_client.get(
        f"/api/tasks/{task.id}", headers={"Authorization": f"Bearer {user2_token}"}
    )

    assert response.status_code == 404


# ==============================================================================
# UPDATE TASK TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_update_task_returns_200_with_updated_task(authenticated_client, db_session):
    """PUT /api/tasks/{id} returns 200 with updated fields."""
    from app.db.crud import TaskCRUD

    # Create task
    task = await TaskCRUD.create(
        db_session,
        {"title": "Original", "priority": 3, "user_id": authenticated_client.user_id},
    )

    response = await authenticated_client.put(
        f"/api/tasks/{task.id}",
        json={"priority": 5, "status": "in_progress"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(task.id)
    assert data["priority"] == 5
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_task_validates_partial_update(authenticated_client, db_session):
    """PUT /api/tasks/{id} updates only provided fields, leaves others unchanged."""
    from app.db.crud import TaskCRUD

    # Create task
    task = await TaskCRUD.create(
        db_session,
        {"title": "Original", "priority": 3, "user_id": authenticated_client.user_id},
    )
    original_title = task.title

    response = await authenticated_client.put(
        f"/api/tasks/{task.id}",
        json={"priority": 4},  # Only update priority
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == original_title  # Title unchanged
    assert data["priority"] == 4  # Priority updated


@pytest.mark.asyncio
async def test_update_task_returns_404_for_nonexistent(authenticated_client):
    """PUT /api/tasks/{fake-id} returns 404 not found."""
    import uuid

    fake_id = uuid.uuid4()
    response = await authenticated_client.put(
        f"/api/tasks/{fake_id}",
        json={"title": "Updated"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_validates_priority_range(authenticated_client, db_session):
    """PUT /api/tasks/{id} returns 422 if priority invalid."""
    from app.db.crud import TaskCRUD

    # Create task
    task = await TaskCRUD.create(
        db_session,
        {"title": "Test", "priority": 3, "user_id": authenticated_client.user_id},
    )

    response = await authenticated_client.put(
        f"/api/tasks/{task.id}",
        json={"priority": 10},  # Invalid priority
    )

    assert response.status_code == 422


# ==============================================================================
# DELETE TASK TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_task_returns_204(authenticated_client, db_session):
    """DELETE /api/tasks/{id} returns 204 with no content."""
    from app.db.crud import TaskCRUD

    # Create task
    task = await TaskCRUD.create(
        db_session,
        {"title": "To delete", "priority": 3, "user_id": authenticated_client.user_id},
    )

    response = await authenticated_client.delete(f"/api/tasks/{task.id}")

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_delete_task_returns_404_for_nonexistent(authenticated_client):
    """DELETE /api/tasks/{fake-id} returns 404 not found."""
    import uuid

    fake_id = uuid.uuid4()
    response = await authenticated_client.delete(f"/api/tasks/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_removes_from_database(authenticated_client, db_session):
    """After DELETE /api/tasks/{id}, GET returns 404."""
    from app.db.crud import TaskCRUD

    # Create task
    task = await TaskCRUD.create(
        db_session,
        {"title": "To delete", "priority": 3, "user_id": authenticated_client.user_id},
    )

    # Delete task
    delete_response = await authenticated_client.delete(f"/api/tasks/{task.id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = await authenticated_client.get(f"/api/tasks/{task.id}")
    assert get_response.status_code == 404
