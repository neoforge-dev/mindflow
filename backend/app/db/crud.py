"""CRUD operations for tasks and users with transaction management."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.security import hash_password, verify_password

from .models import PasswordResetToken, RefreshToken, Task, User


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

    @staticmethod
    async def update(
        session: AsyncSession, user_id: uuid.UUID, data: dict[str, Any]
    ) -> User | None:
        """
        Update user fields.

        Args:
            session: Database session
            user_id: User ID to update
            data: Dictionary of fields to update

        Returns:
            Updated user or None if not found
        """
        try:
            user = await UserCRUD.get_by_id(session, user_id)

            if not user:
                return None

            for key, value in data.items():
                setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            return user
        except Exception:
            await session.rollback()
            raise


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


class PasswordResetTokenCRUD:
    """Password reset token database operations."""

    @staticmethod
    async def create(session: AsyncSession, user_id: uuid.UUID, token: str) -> PasswordResetToken:
        """
        Create a password reset token for user.

        Args:
            session: Database session
            user_id: User ID requesting password reset
            token: Plain text token (will be hashed)

        Returns:
            Created PasswordResetToken object
        """
        try:
            # Hash the token before storing
            token_hash = hash_password(token)

            reset_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                created_at=datetime.utcnow(),
            )

            session.add(reset_token)
            await session.commit()
            await session.refresh(reset_token)
            return reset_token
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def validate_and_use(session: AsyncSession, token: str) -> uuid.UUID | None:
        """
        Validate and mark password reset token as used.

        Args:
            session: Database session
            token: Plain text token to validate

        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            now = datetime.utcnow()

            # Get all unused, non-expired tokens
            result = await session.execute(
                select(PasswordResetToken).where(
                    and_(
                        PasswordResetToken.used_at.is_(None),
                        PasswordResetToken.expires_at > now,
                    )
                )
            )

            tokens = result.scalars().all()

            # Check each token hash (constant-time comparison via bcrypt)
            for reset_token in tokens:
                if verify_password(token, reset_token.token_hash):
                    # Mark token as used
                    reset_token.used_at = datetime.utcnow()
                    await session.commit()
                    return reset_token.user_id

            return None
        except Exception:
            await session.rollback()
            raise


class RefreshTokenCRUD:
    """Refresh token database operations."""

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: uuid.UUID,
        token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """
        Create a refresh token for user session.

        Args:
            session: Database session
            user_id: User ID
            token: Plain text token (will be hashed)
            user_agent: User agent string for security tracking
            ip_address: IP address for security tracking

        Returns:
            Created RefreshToken object
        """
        try:
            # Hash the token before storing
            token_hash = hash_password(token)

            refresh_token = RefreshToken(
                id=uuid.uuid4(),
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(days=30),
                created_at=datetime.utcnow(),
                last_used_at=datetime.utcnow(),
                user_agent=user_agent,
                ip_address=ip_address,
            )

            session.add(refresh_token)
            await session.commit()
            await session.refresh(refresh_token)
            return refresh_token
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def validate(session: AsyncSession, token: str) -> uuid.UUID | None:
        """
        Validate refresh token and update last_used_at.

        Args:
            session: Database session
            token: Plain text token to validate

        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            now = datetime.utcnow()

            # Get all active (non-revoked, non-expired) tokens
            result = await session.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.revoked_at.is_(None),
                        RefreshToken.expires_at > now,
                    )
                )
            )

            tokens = result.scalars().all()

            # Check each token hash (constant-time comparison via bcrypt)
            for refresh_token in tokens:
                if verify_password(token, refresh_token.token_hash):
                    # Update last used timestamp
                    refresh_token.last_used_at = datetime.utcnow()
                    await session.commit()
                    return refresh_token.user_id

            return None
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def revoke_all_for_user(session: AsyncSession, user_id: uuid.UUID) -> int:
        """
        Revoke all active refresh tokens for a user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        try:
            now = datetime.utcnow()

            # Get all active tokens for user
            result = await session.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.user_id == user_id,
                        RefreshToken.revoked_at.is_(None),
                    )
                )
            )

            tokens = result.scalars().all()

            # Mark all as revoked
            for token in tokens:
                token.revoked_at = now

            await session.commit()
            return len(tokens)
        except Exception:
            await session.rollback()
            raise
