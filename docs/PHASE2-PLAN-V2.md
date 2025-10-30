# Phase 2: Database Layer Implementation Plan (v2.0)

**Status**: Ready to Execute
**Approach**: Test-Driven Development (Outside-In)
**Duration**: 4 hours
**Coverage Target**: >90%
**Updated**: 2025-10-30

---

## Overview

We are building the **PostgreSQL database layer** for MindFlow's FastAPI backend from scratch. This replaces the Google Apps Script/Sheets backend.

**What We're Building**:
- SQLAlchemy async models (User, Task, UserPreferences, AuditLog)
- Database connection management with async sessions and pooling
- CRUD operations for tasks (Create, Read, Update, Delete)
- Complete test suite with PostgreSQL fixtures and error handling
- Production-ready transaction management and indexing

**What We're NOT Building** (yet):
- API endpoints (Phase 3)
- Authentication middleware (Phase 4)
- Task scoring logic (Phase 1 - can do in parallel)
- Frontend (separate)
- Data migration from Sheets (not needed)
- Performance benchmarks (add later when needed)

**Success Criteria**:
- All tests pass
- >90% code coverage for database layer
- Can create, read, update, delete tasks in PostgreSQL
- Proper async/await patterns throughout
- Multi-user isolation verified
- Audit logging functional

---

## Deployment Architecture

**Backend**: DigitalOcean Droplet (Ubuntu 22.04 LTS)
- FastAPI application (uvicorn)
- PostgreSQL 15 (same droplet or managed database)
- Nginx reverse proxy
- SSL via Let's Encrypt

**Frontend**: Cloudflare Pages
- Static hosting for LIT dashboard (optional)
- CDN and DDoS protection
- Cloudflare Workers for edge functions (if needed)

**Primary UI**: ChatGPT Custom GPT (no hosting needed)

---

## Files to Create/Modify

### New Files (12 files)

```
backend/                          # CREATE: New directory
├── app/
│   ├── __init__.py              # CREATE: Empty
│   ├── config.py                # CREATE: Environment configuration
│   ├── db/
│   │   ├── __init__.py          # CREATE: Empty
│   │   ├── database.py          # CREATE: Async SQLAlchemy engine + pooling
│   │   ├── models.py            # CREATE: User, Task, UserPreferences, AuditLog
│   │   └── crud.py              # CREATE: Database operations with transactions
│   └── schemas/
│       ├── __init__.py          # CREATE: Empty
│       └── task.py              # CREATE: Pydantic models
├── tests/
│   ├── __init__.py              # CREATE: Empty
│   ├── conftest.py              # CREATE: Pytest fixtures (PostgreSQL-based)
│   └── integration/
│       ├── __init__.py          # CREATE: Empty
│       └── test_database.py    # CREATE: CRUD + error handling tests
├── requirements.txt             # CREATE: Python dependencies
├── requirements-dev.txt         # CREATE: Test dependencies
├── pytest.ini                   # CREATE: Pytest configuration
├── .env.example                 # CREATE: Environment template
└── alembic.ini                  # CREATE: (Phase 3 - migrations)
```

### Files to NOT Touch

```
src/gas/                         # IGNORE: Keep GAS code for reference
tests/ (root)                    # IGNORE: Old GAS tests
pyproject.toml                   # KEEP: Already configured
docs/DEPLOYMENT.md               # UPDATE: Later (DigitalOcean instructions)
```

---

## Enhanced Data Model

### Core Tables

#### `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',  -- free, pro, enterprise
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

#### `tasks`

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Core fields
    title VARCHAR(256) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, snoozed
    priority INTEGER DEFAULT 3,            -- 1-5 scale

    -- Temporal
    due_date TIMESTAMP,
    snoozed_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Scoring fields (NEW - from GAS logic)
    effort_estimate_minutes INTEGER,       -- For impact/effort scoring
    tags VARCHAR(500),                     -- Comma-separated: "morning,urgent,deep-work"

    -- Indexes for common queries
    CONSTRAINT tasks_priority_check CHECK (priority BETWEEN 1 AND 5)
);

CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_date);
CREATE INDEX idx_tasks_snoozed_until ON tasks(snoozed_until);
```

#### `user_preferences`

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Scoring weights (stored as integers 0-100, sum to 100)
    weight_urgency INTEGER DEFAULT 40,
    weight_priority INTEGER DEFAULT 35,
    weight_impact INTEGER DEFAULT 15,
    weight_effort INTEGER DEFAULT 10,

    -- Time preferences
    timezone VARCHAR(50) DEFAULT 'UTC',
    work_start_time TIME DEFAULT '09:00',
    work_end_time TIME DEFAULT '17:00',

    -- AI configuration
    enable_habit_learning BOOLEAN DEFAULT true
);
```

#### `audit_logs` (NEW - from GAS logs sheet)

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Action tracking
    action VARCHAR(100) NOT NULL,          -- "CREATE_TASK", "GET_BEST_TASK", etc.
    resource_id UUID,                      -- Task ID if applicable
    result VARCHAR(20) NOT NULL,           -- "success" or "error"
    error_message TEXT,
    request_duration_ms INTEGER,

    -- Indexes for debugging
    CONSTRAINT audit_result_check CHECK (result IN ('success', 'error'))
);

CREATE INDEX idx_audit_user_timestamp ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_errors ON audit_logs(result) WHERE result = 'error';
```

**Why audit_logs table?**
- Port existing GAS logging functionality
- Debug production issues (who did what when)
- Track API usage patterns
- Identify error trends

---

## Detailed Function & Test Specifications

### Part 1: Configuration (`app/config.py`)

#### Functions

**`class Settings(BaseSettings)`**
Load environment variables using Pydantic. Validates DATABASE_URL, SECRET_KEY, and environment mode.

```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://localhost/mindflow"
    )

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

#### Tests

No tests needed for simple configuration class.

---

### Part 2: Database Connection (`app/db/database.py`)

#### Functions

**`create_async_engine() -> AsyncEngine`**
Create SQLAlchemy async engine for PostgreSQL with production-ready connection pooling.

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,

    # Production pooling configuration
    pool_size=10,          # 10 persistent connections
    max_overflow=5,        # +5 during traffic spikes
    pool_timeout=30,       # Wait 30s for connection
    pool_pre_ping=True,    # Verify connection before use
    pool_recycle=3600,     # Recycle connections every hour (prevents stale connections)
)
```

**`async_session_maker() -> AsyncSession`**
Session factory for database operations. Set expire_on_commit=False for async compatibility.

```python
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

**`async def get_db() -> AsyncSession`**
FastAPI dependency injection for database sessions. Yields session, ensures proper cleanup with async context manager.

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**`Base = declarative_base()`**
SQLAlchemy declarative base for all models.

```python
Base = declarative_base()
```

#### Tests

**`test_database_connection_succeeds`**
Database engine connects successfully to PostgreSQL instance.

**`test_async_session_created`**
Session factory creates valid AsyncSession with correct configuration.

**`test_get_db_yields_session_and_closes`**
Dependency injection yields session then closes on exit.

---

### Part 3: Database Models (`app/db/models.py`)

#### Classes/Functions

**`class User(Base)`**
User model with id, email, password_hash, full_name, plan, timestamps. Has relationship to tasks with cascade delete.

```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
```

**`class Task(Base)`**
Task model with id, user_id, title, description, status, priority, due_date, timestamps, tags, effort_estimate. Foreign key to User with CASCADE.

```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(256), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=3)  # 1-5

    due_date = Column(DateTime)
    snoozed_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Scoring fields (from GAS logic)
    effort_estimate_minutes = Column(Integer)  # For impact/effort calculations
    tags = Column(String(500))  # "morning,urgent,deep-work"

    user = relationship("User", back_populates="tasks")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_tasks_user_status", "user_id", "status"),
        Index("idx_tasks_user_due", "user_id", "due_date"),
        Index("idx_tasks_snoozed_until", "snoozed_until"),
    )
```

**`class UserPreferences(Base)`**
Preferences model with id, user_id, scoring weights, timezone, work hours. One-to-one relationship with User.

```python
class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    weight_urgency = Column(Integer, default=40)  # 0-100
    weight_priority = Column(Integer, default=35)
    weight_impact = Column(Integer, default=15)
    weight_effort = Column(Integer, default=10)

    timezone = Column(String(50), default="UTC")
```

**`class AuditLog(Base)` (NEW)**
Audit log model for tracking all API operations (from GAS logs sheet).

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    action = Column(String(100), nullable=False)  # "CREATE_TASK", "GET_BEST_TASK"
    resource_id = Column(UUID(as_uuid=True))  # Task ID if applicable
    result = Column(String(20), nullable=False)  # "success" or "error"
    error_message = Column(Text)
    request_duration_ms = Column(Integer)

    __table_args__ = (
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_action", "action"),
    )
```

#### Tests

**`test_user_model_creates_with_required_fields`**
User created with email and password_hash has valid UUID.

**`test_user_model_has_default_plan_free`**
User without plan specified defaults to 'free' tier.

**`test_task_model_creates_with_user_relationship`**
Task with user_id foreign key links to User correctly.

**`test_task_model_has_default_status_pending`**
Task without status specified defaults to 'pending' status.

**`test_task_cascade_deletes_when_user_deleted`**
When User deleted, all associated Tasks also deleted automatically.

**`test_user_preferences_one_to_one_with_user`**
UserPreferences has unique user_id constraint enforcing one-to-one relationship.

**`test_audit_log_creates_with_timestamp`**
AuditLog entry created with automatic timestamp.

---

### Part 4: Pydantic Schemas (`app/schemas/task.py`)

#### Classes/Functions

**`class TaskBase(BaseModel)`**
Base task schema with title, description, priority, due_date, tags, effort_estimate. Validates title length and priority range.

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[datetime] = None
    tags: Optional[str] = None
    effort_estimate_minutes: Optional[int] = Field(None, ge=1, le=480)  # Max 8 hours
```

**`class TaskCreate(TaskBase)`**
Schema for creating tasks. Validates title not empty, priority 1-5.

```python
class TaskCreate(TaskBase):
    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

**`class TaskUpdate(BaseModel)`**
Schema for updating tasks. All fields optional: status, priority, due_date, snoozed_until.

```python
class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    effort_estimate_minutes: Optional[int] = Field(None, ge=1, le=480)
```

**`class TaskResponse(TaskBase)`**
Response schema adds id, user_id, status, timestamps. Config from_attributes=True.

```python
class TaskResponse(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None

    class Config:
        from_attributes = True
```

#### Tests

**`test_task_create_validates_title_required`**
TaskCreate raises ValidationError when title missing or empty.

**`test_task_create_validates_priority_range`**
TaskCreate raises ValidationError when priority outside 1-5 range.

**`test_task_update_allows_partial_updates`**
TaskUpdate accepts only status field, ignores others correctly.

**`test_task_response_serializes_from_orm_model`**
TaskResponse converts SQLAlchemy Task model to JSON successfully.

**`test_effort_estimate_validates_range`**
TaskCreate raises ValidationError when effort_estimate > 480 minutes.

---

### Part 5: CRUD Operations (`app/db/crud.py`)

#### Functions

**`async def create_task(session, data) -> Task`**
Create new task in database with transaction management. Accepts dict, returns Task model with generated ID.

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from .models import Task

class TaskCRUD:
    """Task database operations with transaction management."""

    @staticmethod
    async def create(session: AsyncSession, data: Dict[str, Any]) -> Task:
        """Create new task with transaction handling."""
        try:
            task = Task(**data)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task
        except Exception as e:
            await session.rollback()
            raise
```

**`async def get_task_by_id(session, task_id, user_id) -> Task | None`**
Retrieve task by ID with user validation. Returns None if not found or wrong user.

```python
    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Task]:
        """Get task by ID (with user validation)."""
        result = await session.execute(
            select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.user_id == user_id
                )
            )
        )
        return result.scalars().first()
```

**`async def list_tasks_by_user(session, user_id, status=None) -> list[Task]`**
List all user's tasks with optional status filter. Orders by created_at DESC.

```python
    @staticmethod
    async def list_by_user(
        session: AsyncSession,
        user_id: uuid.UUID,
        status: Optional[str] = None
    ) -> List[Task]:
        """List user's tasks with optional status filter."""
        query = select(Task).where(Task.user_id == user_id)

        if status:
            query = query.where(Task.status == status)

        query = query.order_by(Task.created_at.desc())

        result = await session.execute(query)
        return list(result.scalars().all())
```

**`async def update_task(session, task_id, user_id, data) -> Task`**
Update task fields for given user with transaction handling. Raises ValueError if task not found.

```python
    @staticmethod
    async def update(
        session: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        data: Dict[str, Any]
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
        except Exception as e:
            await session.rollback()
            raise
```

**`async def delete_task(session, task_id, user_id) -> None`**
Delete task with user validation. Validates ownership before deletion.

```python
    @staticmethod
    async def delete(
        session: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """Delete task with ownership validation."""
        try:
            task = await TaskCRUD.get_by_id(session, task_id, user_id)

            if task:
                await session.delete(task)
                await session.commit()
        except Exception as e:
            await session.rollback()
            raise
```

**`async def get_pending_tasks(session, user_id) -> list[Task]`**
Get all non-completed tasks for user. Excludes completed and snoozed (if snoozed_until > now).

```python
    @staticmethod
    async def get_pending_tasks(
        session: AsyncSession,
        user_id: uuid.UUID
    ) -> List[Task]:
        """Get all pending/in-progress tasks for user."""
        now = datetime.utcnow()
        result = await session.execute(
            select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.status.in_(["pending", "in_progress"]),
                    # Exclude snoozed tasks that are still sleeping
                    or_(
                        Task.snoozed_until == None,
                        Task.snoozed_until <= now
                    )
                )
            )
        )
        return list(result.scalars().all())
```

#### Tests

**`test_create_task_returns_task_with_id`**
Created task has valid UUID and matches input data.

**`test_create_task_sets_default_status_pending`**
Task created without status defaults to pending automatically.

**`test_get_task_by_id_returns_correct_task`**
Retrieved task matches ID and belongs to requesting user.

**`test_get_task_by_id_returns_none_for_wrong_user`**
Cannot retrieve another user's task, returns None correctly.

**`test_list_tasks_by_user_returns_only_user_tasks`**
List contains only requesting user's tasks, not others.

**`test_list_tasks_by_user_filters_by_status`**
List with status filter returns only tasks matching status.

**`test_update_task_modifies_specified_fields_only`**
Update changes only provided fields, leaves others unchanged.

**`test_update_task_updates_updated_at_timestamp`**
Update automatically updates the updated_at timestamp.

**`test_update_task_raises_for_nonexistent_task`**
Update raises ValueError when task doesn't exist or wrong user.

**`test_delete_task_removes_from_database`**
After deletion, task no longer retrievable by ID query.

**`test_delete_task_validates_ownership`**
Cannot delete another user's task, operation fails silently.

**`test_get_pending_tasks_excludes_completed`**
Returns pending and in_progress, excludes completed and snoozed.

**`test_get_pending_tasks_excludes_snoozed`**
Tasks with snoozed_until in future are excluded from pending list.

**Error Handling Tests** (NEW):

**`test_get_nonexistent_task_returns_none`**
Getting task with invalid UUID returns None, not exception.

**`test_update_nonexistent_task_raises_value_error`**
Updating nonexistent task raises ValueError with clear message.

**`test_cannot_access_other_users_task`**
User cannot retrieve another user's task (multi-tenancy isolation).

**`test_transaction_rollback_on_error`**
Database error during create/update triggers rollback, no partial writes.

---

### Part 6: Test Fixtures (`tests/conftest.py`)

#### Functions

**`@pytest_asyncio.fixture async def db_engine()`**
Create test PostgreSQL database engine. Creates tables, yields, drops tables.

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import User, Task
import uuid
import os

# Use PostgreSQL for tests (not SQLite - matches production)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/mindflow_test"
)

@pytest_asyncio.fixture(scope="session")
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
```

**`@pytest_asyncio.fixture async def db_session(db_engine)`**
Create async session for tests with automatic rollback. Yields session, rolls back after test.

```python
@pytest_asyncio.fixture
async def db_session(db_engine):
    """Session with automatic rollback after each test."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()  # Rollback after test (isolation)
```

**`@pytest_asyncio.fixture async def test_user(db_session)`**
Create and return test user with known credentials. Commits to database.

```python
@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

**`@pytest_asyncio.fixture async def test_user_2(db_session)`** (NEW)
Create second test user for multi-user test scenarios.

```python
@pytest_asyncio.fixture
async def test_user_2(db_session):
    """Create second test user for multi-tenancy tests."""
    user = User(
        id=uuid.uuid4(),
        email="test2@example.com",
        password_hash="hashed_password_2",
        full_name="Test User 2"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

**`@pytest_asyncio.fixture async def test_task(db_session, test_user)`**
Create sample task for test user. Returns committed task.

```python
@pytest_asyncio.fixture
async def test_task(db_session, test_user):
    """Create test task."""
    from app.db.crud import TaskCRUD
    from datetime import datetime, timedelta

    task = await TaskCRUD.create(db_session, {
        "title": "Test task",
        "description": "Test description",
        "priority": 3,
        "due_date": datetime.utcnow() + timedelta(days=1),
        "user_id": test_user.id
    })
    return task
```

---

## Implementation Order (TDD Red-Green-Refactor)

### Step 1: Setup Project Structure (15 min)

```bash
# Create backend directory
mkdir -p backend/app/db
mkdir -p backend/app/schemas
mkdir -p backend/tests/integration

# Create __init__.py files
touch backend/app/__init__.py
touch backend/app/db/__init__.py
touch backend/app/schemas/__init__.py
touch backend/tests/__init__.py
touch backend/tests/integration/__init__.py

# Create main files
touch backend/app/config.py
touch backend/app/db/database.py
touch backend/app/db/models.py
touch backend/app/db/crud.py
touch backend/app/schemas/task.py
touch backend/tests/conftest.py
touch backend/tests/integration/test_database.py
touch backend/pytest.ini
touch backend/requirements.txt
touch backend/requirements-dev.txt
touch backend/.env.example
```

### Step 2: Create Dependencies Files (10 min)

**backend/requirements.txt**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

**backend/requirements-dev.txt**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
aiosqlite==0.19.0
httpx==0.25.1
```

**backend/pytest.ini**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts =
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90
    -v
markers =
    integration: Integration tests (require database)
```

**backend/.env.example**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mindflow
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mindflow_test

# Security
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Step 3: Write Config (15 min)

**RED**: No test needed for simple config
**GREEN**: Implement `app/config.py` (see Part 1)
**REFACTOR**: Add type hints, docstrings

### Step 4: Write Database Connection (20 min)

**RED**: Write connection tests in `tests/integration/test_database.py`

```python
import pytest
from app.db.database import engine, AsyncSessionLocal, get_db

@pytest.mark.integration
class TestDatabaseConnection:
    """Test database connectivity."""

    @pytest.mark.asyncio
    async def test_engine_connects_to_postgres(self):
        """GIVEN PostgreSQL database
           WHEN engine created
           THEN connection succeeds
        """
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_session_factory_creates_session(self):
        """GIVEN session factory
           WHEN session created
           THEN returns AsyncSession
        """
        async with AsyncSessionLocal() as session:
            assert isinstance(session, AsyncSession)
```

**GREEN**: Implement `app/db/database.py` (see Part 2)
**REFACTOR**: Add connection pooling config, improve error handling

### Step 5: Write Model Tests (30 min)

**RED**: Write all model tests in `tests/integration/test_database.py`

```python
@pytest.mark.integration
class TestModels:
    """Test database models."""

    @pytest.mark.asyncio
    async def test_user_model_creates_with_required_fields(self, db_session):
        """GIVEN email and password_hash
           WHEN user created
           THEN has valid UUID
        """
        user = User(
            email="user@example.com",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.plan == "free"  # Default

    @pytest.mark.asyncio
    async def test_task_cascade_deletes_when_user_deleted(
        self, db_session, test_user, test_task
    ):
        """GIVEN user with tasks
           WHEN user deleted
           THEN tasks also deleted
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

    # Add remaining model tests...
```

**GREEN**: Implement `app/db/models.py` (see Part 3)
**REFACTOR**: Add indexes, improve relationships

### Step 6: Write Pydantic Schema Tests (20 min)

**RED**: Write schema validation tests

```python
import pytest
from pydantic import ValidationError
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

class TestTaskSchemas:
    """Test Pydantic validation."""

    def test_task_create_validates_title_required(self):
        """GIVEN missing title
           WHEN task created
           THEN raises ValidationError
        """
        with pytest.raises(ValidationError, match="title"):
            TaskCreate(priority=3)

    def test_task_create_validates_priority_range(self):
        """GIVEN priority out of range
           WHEN task created
           THEN raises ValidationError
        """
        with pytest.raises(ValidationError, match="priority"):
            TaskCreate(title="Task", priority=10)

    # Add remaining schema tests...
```

**GREEN**: Implement `app/schemas/task.py` (see Part 4)
**REFACTOR**: Add custom validators, better error messages

### Step 7: Write CRUD Tests (45 min)

**RED**: Write all CRUD tests

```python
@pytest.mark.integration
class TestTaskCRUD:
    """Test task database operations."""

    @pytest.mark.asyncio
    async def test_create_task_returns_task_with_id(
        self, db_session, test_user
    ):
        """GIVEN user and task data
           WHEN task created
           THEN has valid ID
        """
        from app.db.crud import TaskCRUD

        task = await TaskCRUD.create(db_session, {
            "title": "New task",
            "priority": 4,
            "user_id": test_user.id
        })

        assert task.id is not None
        assert task.title == "New task"
        assert task.status == "pending"

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_task(
        self, db_session, test_user, test_user_2
    ):
        """GIVEN task belongs to user1
           WHEN user2 tries to access
           THEN returns None
        """
        from app.db.crud import TaskCRUD

        # User 1 creates task
        task = await TaskCRUD.create(db_session, {
            "title": "User 1 task",
            "user_id": test_user.id
        })

        # User 2 tries to access
        result = await TaskCRUD.get_by_id(
            db_session, task.id, test_user_2.id
        )
        assert result is None

    # Add all remaining CRUD tests...
```

**GREEN**: Implement `app/db/crud.py` one function at a time (see Part 5)
**REFACTOR**: Extract common patterns, add error handling

### Step 8: Write Error Handling Tests (20 min)

**RED**: Write error condition tests

```python
@pytest.mark.integration
class TestTaskCRUDErrors:
    """Test error conditions."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_returns_none(
        self, db_session, test_user
    ):
        """GIVEN invalid task ID
           WHEN retrieved
           THEN returns None
        """
        from app.db.crud import TaskCRUD
        import uuid

        fake_id = uuid.uuid4()
        result = await TaskCRUD.get_by_id(db_session, fake_id, test_user.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_nonexistent_task_raises(
        self, db_session, test_user
    ):
        """GIVEN invalid task ID
           WHEN updated
           THEN raises ValueError
        """
        from app.db.crud import TaskCRUD
        import uuid

        fake_id = uuid.uuid4()
        with pytest.raises(ValueError, match="not found"):
            await TaskCRUD.update(
                db_session, fake_id, test_user.id, {"status": "completed"}
            )

    # Add remaining error tests...
```

**GREEN**: Add error handling to CRUD operations
**REFACTOR**: Consistent error messages, proper rollback

### Step 9: Write Test Fixtures (20 min)

**GREEN**: Implement all fixtures in `tests/conftest.py` (see Part 6)
**REFACTOR**: Make fixtures reusable, add more test users

### Step 10: Run Full Test Suite (10 min)

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start test database (if using Docker)
docker run -d \
  --name mindflow-test-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mindflow_test \
  -p 5432:5432 \
  postgres:15-alpine

# Wait for database to be ready
sleep 3

# Run tests
pytest -v --cov=app

# Expected output:
# tests/integration/test_database.py::TestDatabaseConnection::test_engine_connects_to_postgres PASSED
# tests/integration/test_database.py::TestModels::test_user_model_creates_with_required_fields PASSED
# tests/integration/test_database.py::TestTaskCRUD::test_create_task_returns_task_with_id PASSED
# ... (all tests passing)
#
# ----------- coverage: 92% -----------
```

### Step 11: Verify Coverage (10 min)

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

Check coverage for:
- app/db/database.py: >95%
- app/db/models.py: >85%
- app/db/crud.py: >95%
- app/schemas/task.py: >90%

---

## Verification Checklist

Before considering Phase 2 complete:

### Functionality
- [ ] All 28+ tests pass
- [ ] Coverage >90% for database layer
- [ ] Can create user and task in database
- [ ] Can retrieve tasks by user
- [ ] Can update task status and fields
- [ ] Can delete task
- [ ] Cascade delete works (user deletion removes tasks)

### Data Integrity
- [ ] Multi-user isolation verified (users can't access each other's tasks)
- [ ] Foreign key constraints enforced
- [ ] Transaction rollback on errors
- [ ] Timestamps auto-update on modifications

### Performance
- [ ] Indexes created on common query columns
- [ ] Connection pooling configured
- [ ] No N+1 query problems in CRUD operations

### Code Quality
- [ ] Async/await used correctly throughout
- [ ] Proper error handling with rollback
- [ ] Test fixtures are reusable
- [ ] Type hints on all functions

---

## Common Commands

```bash
# Setup test database (Docker)
docker run -d --name mindflow-test-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mindflow_test \
  -p 5432:5432 postgres:15-alpine

# Install dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/integration/test_database.py -v

# Run specific test
pytest tests/integration/test_database.py::TestTaskCRUD::test_create_task_returns_task_with_id -v

# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Stop test database
docker stop mindflow-test-db
docker rm mindflow-test-db
```

---

## Next Phase Preview

**Phase 3: API Endpoints** (4-5 hours)
- FastAPI app with routes
- `/api/tasks` CRUD endpoints
- `/api/tasks/best` for scoring
- Request/response validation
- Error handling middleware
- 15-20 API endpoint tests
- Deployment to DigitalOcean droplet

---

## Time Budget

| Step | Duration | Cumulative |
|------|----------|------------|
| 1. Setup project structure | 15 min | 15 min |
| 2. Create dependencies files | 10 min | 25 min |
| 3. Write config | 15 min | 40 min |
| 4. Database connection tests + impl | 20 min | 60 min |
| 5. Model tests + impl | 30 min | 90 min |
| 6. Schema tests + impl | 20 min | 110 min |
| 7. CRUD tests + impl | 45 min | 155 min |
| 8. Error handling tests + impl | 20 min | 175 min |
| 9. Test fixtures | 20 min | 195 min |
| 10. Run full test suite | 10 min | 205 min |
| 11. Verify coverage | 10 min | 215 min |
| **Total** | **3h 35min** | |

**Buffer**: 25 minutes for debugging/refactoring

**Final**: 4 hours total

---

## Production Deployment Notes

### DigitalOcean Setup

**Droplet Specs** (recommended):
- Ubuntu 22.04 LTS
- 2 GB RAM / 1 vCPU (Basic - $12/month)
- Or 4 GB RAM / 2 vCPU (for higher traffic - $24/month)

**Database Options**:
1. **Same Droplet**: PostgreSQL installed on app server (cheaper, simpler)
2. **Managed Database**: DigitalOcean Managed PostgreSQL ($15/month, auto-backups)

**Initial Setup**:
```bash
# On droplet:
sudo apt update
sudo apt install -y python3.11 python3-pip postgresql nginx

# Setup PostgreSQL
sudo -u postgres createdb mindflow
sudo -u postgres createuser mindflow_user -P

# Clone repo and install
git clone https://github.com/yourusername/mindflow.git
cd mindflow/backend
pip install -r requirements.txt

# Run migrations (Phase 3)
alembic upgrade head

# Start with systemd service
sudo systemctl enable mindflow
sudo systemctl start mindflow
```

### Cloudflare Frontend

**For LIT Dashboard** (optional):
1. Build static assets: `npm run build`
2. Deploy to Cloudflare Pages
3. Connect custom domain
4. Free SSL and CDN included

**For ChatGPT Custom GPT**:
- Update Actions schema with DigitalOcean droplet IP/domain
- Configure CORS in FastAPI to allow OpenAI requests
- No separate hosting needed

---

## Key Changes from Original Plan

### ✅ Additions (Production-Ready)

1. **AuditLog table** - Port existing GAS logging functionality
2. **Task.effort_estimate_minutes** - Enable impact/effort scoring
3. **Task.tags** - Enable context-based scoring
4. **PostgreSQL for tests** - Match production database
5. **Connection pooling** - Handle concurrent requests
6. **Indexes** - Optimize common queries
7. **Transaction management** - Explicit commit/rollback
8. **Error handling tests** - Multi-tenancy, nonexistent resources
9. **test_user_2 fixture** - Test user isolation

### ❌ Removals (Pragmatic)

1. ~~Data migration from Sheets~~ - Not needed
2. ~~Performance benchmarks~~ - Add later when needed
3. ~~Repository pattern~~ - SQLAlchemy is sufficient for MVP
4. ~~Service layer~~ - Build in Phase 3 with API
5. ~~Fly.io references~~ - Using DigitalOcean + Cloudflare

---

**Status**: Ready to execute
**Next Action**: Create project structure (Step 1)

**Document Version**: 2.0
**Last Updated**: 2025-10-30
**Deployment**: DigitalOcean (backend) + Cloudflare (frontend)
