"""Pytest fixtures for database testing."""

import os
import uuid

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import User

# Use PostgreSQL for tests (matches production)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:54320/mindflow_test"
)


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine with proper cleanup."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables (clean slate for next test run)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Session with automatic rollback after each test."""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any uncommitted changes
        await session.close()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_2(db_session):
    """Create second test user for multi-tenancy tests."""
    user = User(
        id=uuid.uuid4(),
        email="test2@example.com",
        password_hash="hashed_password_2",
        full_name="Test User 2",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_task(db_engine, test_user):
    """Create test task."""
    from datetime import datetime, timedelta

    from app.db.crud import TaskCRUD

    # Create task in its own session that commits independently
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        task = await TaskCRUD.create(
            session,
            {
                "title": "Test task",
                "description": "Test description",
                "priority": 3,
                "due_date": datetime.utcnow() + timedelta(days=1),
                "user_id": test_user.id,
            },
        )
        await session.commit()
        await session.refresh(task)
        return task


# API Testing Fixtures


@pytest_asyncio.fixture
async def test_client(db_engine):
    """Async HTTP client for API testing with database override."""
    from httpx import ASGITransport, AsyncClient

    from app.dependencies import get_db
    from app.main import app

    # Override get_db dependency to use test database
    async def override_get_db():
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(test_client, test_user):
    """Client with user_id stored for convenience."""
    # Store user_id - tests must include ?user_id={client.user_id} in URLs
    test_client.user_id = test_user.id
    return test_client
