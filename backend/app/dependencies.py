"""FastAPI dependency injection for database sessions and user context."""

from uuid import UUID

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.

    Yields database session for request scope, automatically commits
    if no exception and closes session after request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_id(
    user_id: UUID = Query(..., description="User ID (temporary - will use JWT in Phase 4)")
) -> UUID:
    """
    Temporary: Extract user_id from query param.

    Phase 4: This will be replaced with JWT token extraction.
    For now, require user_id as query parameter for all endpoints.
    """
    return user_id
