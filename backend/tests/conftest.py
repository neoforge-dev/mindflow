"""Pytest fixtures for database testing."""

# Set testing environment BEFORE any app imports
import os

os.environ["ENVIRONMENT"] = "testing"

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


@pytest_asyncio.fixture(scope="session")
async def db_tables():
    """Create database tables once per test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables at end of session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_engine(db_tables):
    """Create test database engine with proper cleanup."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    yield engine

    # Dispose engine after each test
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Session with automatic cleanup after each test."""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

        # Clean up: Delete all data from tables (in correct order to respect foreign keys)
        await session.execute(Base.metadata.tables["tasks"].delete())
        await session.execute(Base.metadata.tables["user_preferences"].delete())
        await session.execute(Base.metadata.tables["audit_logs"].delete())
        await session.execute(Base.metadata.tables["password_reset_tokens"].delete())
        await session.execute(Base.metadata.tables["refresh_tokens"].delete())
        await session.execute(Base.metadata.tables["oauth_authorization_codes"].delete())
        await session.execute(Base.metadata.tables["oauth_clients"].delete())
        await session.execute(Base.metadata.tables["users"].delete())
        await session.commit()
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
    from app.main import create_app

    # Create fresh app instance for each test to avoid event loop issues
    app = create_app()

    # Override get_db dependency to use test database
    async def override_get_db():
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        # Clean up - ensure this always runs
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_with_password(db_session):
    """Create test user with known password for authentication."""
    from app.auth.security import hash_password

    user = User(
        id=uuid.uuid4(),
        email="testauth@example.com",
        password_hash=hash_password("testPassword123"),
        full_name="Test Auth User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    # Store plain password for testing
    user.plain_password = "testPassword123"
    return user


@pytest_asyncio.fixture
async def auth_headers(test_client, test_user_with_password):
    """Generate JWT auth headers for testing."""
    from app.auth.security import create_access_token

    # Create JWT token with user_id
    token = create_access_token(data={"sub": str(test_user_with_password.id)})

    # Return headers dict
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(test_client, test_user_with_password, auth_headers):
    """Client with JWT auth headers for convenience."""
    # Store auth headers and user for tests
    test_client.headers.update(auth_headers)
    test_client.user_id = test_user_with_password.id
    test_client.user = test_user_with_password
    return test_client
