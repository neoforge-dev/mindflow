"""Integration tests for database layer."""
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, Task, AuditLog
from app.db.crud import TaskCRUD
from datetime import datetime, timedelta
import uuid


@pytest.mark.integration
class TestDatabaseConnection:
    """Test database connectivity."""

    @pytest.mark.asyncio
    async def test_engine_connects_to_postgres(self, db_engine):
        """GIVEN PostgreSQL database
           WHEN engine created
           THEN connection succeeds
        """
        async with db_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_session_factory_creates_session(self, db_session):
        """GIVEN session factory
           WHEN session created
           THEN returns AsyncSession
        """
        assert isinstance(db_session, AsyncSession)


@pytest.mark.integration
class TestModels:
    """Test database models."""

    @pytest.mark.asyncio
    async def test_user_model_creates_with_required_fields(self, db_session):
        """GIVEN email and password_hash
           WHEN user created
           THEN has valid UUID and defaults
        """
        user = User(
            email="newuser@example.com",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.plan == "free"  # Default
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_task_model_creates_with_user_relationship(self, db_session, test_user):
        """GIVEN user exists
           WHEN task created with user_id
           THEN task links to user
        """
        task = Task(
            title="Test task",
            user_id=test_user.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.user_id == test_user.id
        assert task.status == "pending"  # Default

    @pytest.mark.asyncio
    async def test_task_cascade_deletes_when_user_deleted(
        self, db_session, test_user, test_task
    ):
        """GIVEN user with tasks
           WHEN user deleted
           THEN tasks also deleted (cascade)
        """
        task_id = test_task.id

        # Delete user
        await db_session.delete(test_user)
        await db_session.commit()

        # Verify task deleted
        result = await db_session.execute(
            select(Task).where(Task.id == task_id)
        )
        assert result.scalars().first() is None

    @pytest.mark.asyncio
    async def test_audit_log_creates_with_timestamp(self, db_session, test_user):
        """GIVEN user and action
           WHEN audit log created
           THEN has automatic timestamp
        """
        log = AuditLog(
            user_id=test_user.id,
            action="CREATE_TASK",
            result="success"
        )
        db_session.add(log)
        await db_session.commit()
        await db_session.refresh(log)

        assert log.id is not None
        assert log.timestamp is not None
        assert (datetime.utcnow() - log.timestamp).seconds < 5


@pytest.mark.integration
class TestTaskCRUD:
    """Test task database operations."""

    @pytest.mark.asyncio
    async def test_create_task_returns_task_with_id(self, db_session, test_user):
        """GIVEN user and task data
           WHEN task created
           THEN has valid ID and defaults
        """
        task = await TaskCRUD.create(db_session, {
            "title": "New task",
            "priority": 4,
            "user_id": test_user.id
        })

        assert task.id is not None
        assert task.title == "New task"
        assert task.status == "pending"
        assert task.priority == 4

    @pytest.mark.asyncio
    async def test_get_task_by_id_returns_correct_task(
        self, db_session, test_user, test_task
    ):
        """GIVEN task exists
           WHEN retrieved by ID
           THEN returns correct task
        """
        retrieved = await TaskCRUD.get_by_id(
            db_session, test_task.id, test_user.id
        )

        assert retrieved is not None
        assert retrieved.id == test_task.id
        assert retrieved.title == test_task.title

    @pytest.mark.asyncio
    async def test_get_task_by_id_returns_none_for_wrong_user(
        self, db_session, test_user_2, test_task
    ):
        """GIVEN task belongs to user1
           WHEN user2 tries to access
           THEN returns None (multi-tenancy)
        """
        retrieved = await TaskCRUD.get_by_id(
            db_session, test_task.id, test_user_2.id
        )

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_list_tasks_by_user_returns_only_user_tasks(
        self, db_session, test_user, test_user_2
    ):
        """GIVEN multiple users with tasks
           WHEN list tasks by user
           THEN returns only that user's tasks
        """
        # Create tasks for user 1
        await TaskCRUD.create(db_session, {
            "title": "User 1 task 1",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "User 1 task 2",
            "user_id": test_user.id
        })

        # Create task for user 2
        await TaskCRUD.create(db_session, {
            "title": "User 2 task",
            "user_id": test_user_2.id
        })

        # List user 1's tasks
        tasks = await TaskCRUD.list_by_user(db_session, test_user.id)

        assert len(tasks) == 2
        assert all(t.user_id == test_user.id for t in tasks)

    @pytest.mark.asyncio
    async def test_list_tasks_filters_by_status(self, db_session, test_user):
        """GIVEN tasks with different statuses
           WHEN list with status filter
           THEN returns only matching tasks
        """
        await TaskCRUD.create(db_session, {
            "title": "Pending task",
            "status": "pending",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "Completed task",
            "status": "completed",
            "user_id": test_user.id
        })

        pending = await TaskCRUD.list_by_user(
            db_session, test_user.id, status="pending"
        )

        assert len(pending) == 1
        assert pending[0].title == "Pending task"

    @pytest.mark.asyncio
    async def test_update_task_modifies_specified_fields(
        self, db_session, test_user, test_task
    ):
        """GIVEN task exists
           WHEN updated with new data
           THEN only specified fields changed
        """
        original_title = test_task.title

        updated = await TaskCRUD.update(
            db_session,
            test_task.id,
            test_user.id,
            {"status": "completed", "priority": 5}
        )

        assert updated.status == "completed"
        assert updated.priority == 5
        assert updated.title == original_title  # Unchanged

    @pytest.mark.asyncio
    async def test_update_task_updates_timestamp(
        self, db_session, test_user, test_task
    ):
        """GIVEN task exists
           WHEN updated
           THEN updated_at timestamp changes
        """
        original_updated = test_task.updated_at

        # Wait a moment to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)

        updated = await TaskCRUD.update(
            db_session,
            test_task.id,
            test_user.id,
            {"status": "in_progress"}
        )

        assert updated.updated_at > original_updated

    @pytest.mark.asyncio
    async def test_delete_task_removes_from_database(
        self, db_session, test_user, test_task
    ):
        """GIVEN task exists
           WHEN deleted
           THEN no longer retrievable
        """
        task_id = test_task.id

        await TaskCRUD.delete(db_session, task_id, test_user.id)

        retrieved = await TaskCRUD.get_by_id(db_session, task_id, test_user.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_pending_tasks_excludes_completed(self, db_session, test_user):
        """GIVEN tasks with various statuses
           WHEN get pending tasks
           THEN excludes completed and snoozed
        """
        await TaskCRUD.create(db_session, {
            "title": "Pending",
            "status": "pending",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "In progress",
            "status": "in_progress",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "Completed",
            "status": "completed",
            "user_id": test_user.id
        })

        pending = await TaskCRUD.get_pending_tasks(db_session, test_user.id)

        assert len(pending) == 2
        assert all(t.status in ["pending", "in_progress"] for t in pending)

    @pytest.mark.asyncio
    async def test_get_pending_tasks_excludes_snoozed(self, db_session, test_user):
        """GIVEN task snoozed until future
           WHEN get pending tasks
           THEN snoozed task excluded
        """
        await TaskCRUD.create(db_session, {
            "title": "Active task",
            "status": "pending",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "Snoozed task",
            "status": "pending",
            "snoozed_until": datetime.utcnow() + timedelta(hours=2),
            "user_id": test_user.id
        })

        pending = await TaskCRUD.get_pending_tasks(db_session, test_user.id)

        assert len(pending) == 1
        assert pending[0].title == "Active task"


@pytest.mark.integration
class TestTaskCRUDErrors:
    """Test error conditions."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_returns_none(self, db_session, test_user):
        """GIVEN invalid task ID
           WHEN retrieved
           THEN returns None (not exception)
        """
        fake_id = uuid.uuid4()
        task = await TaskCRUD.get_by_id(db_session, fake_id, test_user.id)
        assert task is None

    @pytest.mark.asyncio
    async def test_update_nonexistent_task_raises(self, db_session, test_user):
        """GIVEN invalid task ID
           WHEN updated
           THEN raises ValueError
        """
        fake_id = uuid.uuid4()
        with pytest.raises(ValueError, match="not found"):
            await TaskCRUD.update(
                db_session, fake_id, test_user.id, {"status": "completed"}
            )

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_task(
        self, db_session, test_user, test_user_2
    ):
        """GIVEN task belongs to user1
           WHEN user2 tries to access
           THEN returns None (multi-tenancy isolation)
        """
        # User 1 creates task
        task = await TaskCRUD.create(db_session, {
            "title": "User 1 task",
            "user_id": test_user.id
        })

        # User 2 tries to access
        result = await TaskCRUD.get_by_id(db_session, task.id, test_user_2.id)
        assert result is None
