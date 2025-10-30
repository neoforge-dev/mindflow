"""CRUD operations for tasks and users with transaction management."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import Task, User


class UserCRUD:
    """User database operations for authentication."""

    @staticmethod
    async def create(session: AsyncSession, data: dict[str, Any]) -> User:
        """Create new user with transaction handling."""
        try:
            user = User(**data)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        """Find user by email address (case-sensitive)."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Find user by UUID primary key."""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()


class TaskCRUD:
    """Task database operations with proper error handling."""

    @staticmethod
    async def create(session: AsyncSession, data: dict[str, Any]) -> Task:
        """Create new task with transaction handling."""
        try:
            task = Task(**data)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def get_by_id(
        session: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task | None:
        """Get task by ID with user validation (returns None if not found or wrong user)."""
        result = await session.execute(
            select(Task).where(and_(Task.id == task_id, Task.user_id == user_id))
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_user(
        session: AsyncSession, user_id: uuid.UUID, status: str | None = None
    ) -> list[Task]:
        """List user's tasks with optional status filter."""
        query = select(Task).where(Task.user_id == user_id)

        if status:
            query = query.where(Task.status == status)

        query = query.order_by(Task.created_at.desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID, data: dict[str, Any]
    ) -> Task:
        """Update task with error handling."""
        try:
            task = await TaskCRUD.get_by_id(session, task_id, user_id)

            if not task:
                raise ValueError(f"Task {task_id} not found or access denied")

            for key, value in data.items():
                setattr(task, key, value)

            task.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(task)
            return task
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def delete(session: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete task with ownership validation."""
        try:
            task = await TaskCRUD.get_by_id(session, task_id, user_id)

            if task:
                await session.delete(task)
                await session.commit()
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def get_pending_tasks(session: AsyncSession, user_id: uuid.UUID) -> list[Task]:
        """Get all pending/in-progress tasks for user (excludes completed and snoozed)."""
        now = datetime.utcnow()
        result = await session.execute(
            select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.status.in_(["pending", "in_progress"]),
                    # Exclude snoozed tasks that are still sleeping
                    or_(Task.snoozed_until.is_(None), Task.snoozed_until <= now),
                )
            )
        )
        return list(result.scalars().all())
