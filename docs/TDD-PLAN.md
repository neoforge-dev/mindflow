# MindFlow: Test-Driven Development Implementation Plan

**Last Updated**: 2025-10-30
**Approach**: Outside-In TDD with pytest
**Coverage Target**: >85%

---

## Table of Contents

1. [TDD Philosophy](#tdd-philosophy)
2. [Testing Stack](#testing-stack)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Phase 1: Core Domain](#phase-1-core-domain)
6. [Phase 2: Database Layer](#phase-2-database-layer)
7. [Phase 3: API Endpoints](#phase-3-api-endpoints)
8. [Phase 4: Authentication](#phase-4-authentication)
9. [Phase 5: Integration Tests](#phase-5-integration-tests)
10. [CI/CD Integration](#cicd-integration)

---

## TDD Philosophy

### The Red-Green-Refactor Cycle

```
┌─────────────────────────────────────────┐
│  1. RED: Write failing test             │
│     • Define expected behavior           │
│     • Test should fail (no code yet)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. GREEN: Write minimal code to pass   │
│     • Implement simplest solution       │
│     • Test should pass                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  3. REFACTOR: Improve code quality      │
│     • Remove duplication                │
│     • Improve names, structure          │
│     • Tests still pass                  │
└──────────────┬──────────────────────────┘
               │
               └──────────> Repeat
```

### Outside-In TDD Strategy

1. **Start with API tests** (acceptance tests)
2. **Work inward** to services, models
3. **Mock external dependencies** initially
4. **Replace mocks** with real implementations
5. **Integration tests** verify end-to-end

**Benefits**:
- Design API first (API-driven design)
- Tests document expected behavior
- Refactoring confidence
- Less debugging

---

## Testing Stack

### Core Dependencies

```python
# backend/requirements-dev.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.1                # Async HTTP client for API tests
faker==20.1.0                 # Generate test data
freezegun==1.4.0              # Time mocking
```

### Install Test Dependencies

```bash
cd backend
pip install -r requirements-dev.txt
```

### pytest Configuration

Create `backend/pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Coverage settings
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    -v
    --tb=short

# Markers for test categories
markers =
    unit: Unit tests (fast, no DB)
    integration: Integration tests (DB required)
    e2e: End-to-end tests (full stack)
    slow: Slow tests (>1s)
```

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   ├── db/
│   ├── schemas/
│   └── services/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_scoring.py      # Pure functions
│   │   ├── test_schemas.py      # Pydantic models
│   │   └── test_utils.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_database.py     # DB operations
│   │   └── test_api.py          # API endpoints
│   └── e2e/
│       ├── __init__.py
│       └── test_user_flows.py   # Full user scenarios
├── pytest.ini
└── requirements-dev.txt
```

---

## Development Workflow

### Daily TDD Workflow

```bash
# 1. Pull latest code
git pull origin main

# 2. Create feature branch
git checkout -b feature/task-filtering

# 3. Write failing test
# Edit tests/integration/test_api.py

# 4. Run tests (should fail)
pytest tests/integration/test_api.py::test_filter_tasks_by_status -v

# 5. Implement minimal code
# Edit app/api/tasks.py

# 6. Run tests (should pass)
pytest tests/integration/test_api.py::test_filter_tasks_by_status -v

# 7. Refactor
# Improve code quality while keeping tests green

# 8. Run full test suite
pytest

# 9. Check coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html

# 10. Commit
git add .
git commit -m "Add task filtering by status"
git push origin feature/task-filtering
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_scoring.py

# Specific test
pytest tests/unit/test_scoring.py::test_urgency_score_overdue

# With coverage
pytest --cov=app

# Only unit tests (fast)
pytest -m unit

# Only integration tests
pytest -m integration

# Watch mode (run on file change)
pytest-watch
```

---

## Phase 1: Core Domain

### Goal: Task Scoring Logic (Pure Functions)

**Duration**: 2-3 hours

#### Step 1.1: Urgency Score Tests

Create `tests/unit/test_scoring.py`:

```python
import pytest
from datetime import datetime, timedelta
from app.services.scoring import calculate_urgency_score

class TestUrgencyScore:
    """Test urgency calculation based on deadline proximity."""

    def test_overdue_task_returns_max_urgency(self):
        """GIVEN a task that's overdue
           WHEN urgency is calculated
           THEN it returns 1.0 (maximum urgency)
        """
        # Arrange
        now = datetime(2025, 10, 30, 12, 0, 0)
        due_date = datetime(2025, 10, 29, 12, 0, 0)  # Yesterday

        # Act
        score = calculate_urgency_score(due_date, now)

        # Assert
        assert score == 1.0

    def test_due_in_2_hours_high_urgency(self):
        """GIVEN task due in 2 hours
           WHEN urgency calculated
           THEN returns 0.9
        """
        now = datetime(2025, 10, 30, 12, 0, 0)
        due_date = now + timedelta(hours=2)

        score = calculate_urgency_score(due_date, now)

        assert score == 0.9

    def test_due_in_12_hours_medium_urgency(self):
        """GIVEN task due in 12 hours
           WHEN urgency calculated
           THEN returns 0.7
        """
        now = datetime(2025, 10, 30, 12, 0, 0)
        due_date = now + timedelta(hours=12)

        score = calculate_urgency_score(due_date, now)

        assert score == 0.7

    def test_due_in_3_days_low_urgency(self):
        """GIVEN task due in 3 days
           WHEN urgency calculated
           THEN returns 0.4
        """
        now = datetime(2025, 10, 30, 12, 0, 0)
        due_date = now + timedelta(days=3)

        score = calculate_urgency_score(due_date, now)

        assert score == 0.4

    def test_no_deadline_default_urgency(self):
        """GIVEN task with no deadline
           WHEN urgency calculated
           THEN returns 0.3 (default)
        """
        now = datetime(2025, 10, 30, 12, 0, 0)

        score = calculate_urgency_score(None, now)

        assert score == 0.3
```

#### Step 1.2: Implement Urgency Function

Create `app/services/scoring.py`:

```python
from datetime import datetime
from typing import Optional

def calculate_urgency_score(due_date: Optional[datetime], now: datetime) -> float:
    """Calculate urgency score (0-1) based on deadline proximity.

    Args:
        due_date: Task deadline (None if no deadline)
        now: Current time

    Returns:
        float: Urgency score between 0 and 1
    """
    if due_date is None:
        return 0.3  # No deadline = medium urgency

    hours_until = (due_date - now).total_seconds() / 3600

    if hours_until < 0:
        return 1.0  # Overdue
    elif hours_until < 4:
        return 0.9  # Due very soon
    elif hours_until < 24:
        return 0.7  # Due today
    elif hours_until < 168:  # 1 week
        return 0.4
    else:
        return 0.1
```

#### Step 1.3: Run Tests

```bash
pytest tests/unit/test_scoring.py -v

# Expected output:
# tests/unit/test_scoring.py::TestUrgencyScore::test_overdue_task_returns_max_urgency PASSED
# tests/unit/test_scoring.py::TestUrgencyScore::test_due_in_2_hours_high_urgency PASSED
# tests/unit/test_scoring.py::TestUrgencyScore::test_due_in_12_hours_medium_urgency PASSED
# tests/unit/test_scoring.py::TestUrgencyScore::test_due_in_3_days_low_urgency PASSED
# tests/unit/test_scoring.py::TestUrgencyScore::test_no_deadline_default_urgency PASSED
```

#### Step 1.4: Priority Score Tests

Add to `tests/unit/test_scoring.py`:

```python
from app.services.scoring import calculate_priority_score

class TestPriorityScore:
    """Test priority normalization."""

    @pytest.mark.parametrize("priority,expected", [
        (1, 0.2),
        (3, 0.6),
        (5, 1.0),
    ])
    def test_priority_normalized_to_0_1(self, priority, expected):
        """GIVEN priority on 1-5 scale
           WHEN normalized
           THEN returns value between 0-1
        """
        score = calculate_priority_score(priority)
        assert score == expected

    def test_none_priority_returns_default(self):
        """GIVEN no priority set
           WHEN score calculated
           THEN returns 0.6 (default medium)
        """
        score = calculate_priority_score(None)
        assert score == 0.6
```

#### Step 1.5: Implement Priority Function

Add to `app/services/scoring.py`:

```python
def calculate_priority_score(priority: Optional[int]) -> float:
    """Normalize priority (1-5) to score (0-1).

    Args:
        priority: Priority level 1-5 (None = default 3)

    Returns:
        float: Priority score between 0 and 1
    """
    if priority is None:
        priority = 3  # Default medium

    return priority / 5.0
```

#### Step 1.6: Complete Scoring Function

**Tests** (`tests/unit/test_scoring.py`):

```python
from app.services.scoring import calculate_task_score
from app.db.models import Task

class TestTaskScoring:
    """Test complete task scoring algorithm."""

    def test_high_priority_urgent_task_scores_high(self):
        """GIVEN high priority task due today
           WHEN score calculated
           THEN returns high score (>0.8)
        """
        # Arrange
        now = datetime(2025, 10, 30, 12, 0, 0)
        task = Task(
            id="test-id",
            title="Urgent task",
            priority=5,
            due_date=now + timedelta(hours=6)
        )
        weights = {
            'urgency': 0.40,
            'priority': 0.35,
            'impact': 0.15,
            'effort': 0.10
        }

        # Act
        score, components = calculate_task_score(task, weights, now)

        # Assert
        assert score > 0.8
        assert components['urgency'] > 0.7
        assert components['priority'] == 1.0

    def test_low_priority_distant_task_scores_low(self):
        """GIVEN low priority task due in 2 weeks
           WHEN score calculated
           THEN returns low score (<0.3)
        """
        now = datetime(2025, 10, 30, 12, 0, 0)
        task = Task(
            id="test-id",
            title="Someday task",
            priority=1,
            due_date=now + timedelta(days=14)
        )
        weights = {
            'urgency': 0.40,
            'priority': 0.35,
            'impact': 0.15,
            'effort': 0.10
        }

        score, components = calculate_task_score(task, weights, now)

        assert score < 0.3
```

**Implementation** (`app/services/scoring.py`):

```python
from typing import Tuple, Dict
from app.db.models import Task

def calculate_task_score(
    task: Task,
    weights: Dict[str, float],
    now: datetime
) -> Tuple[float, Dict[str, float]]:
    """Calculate overall task relevance score.

    Args:
        task: Task to score
        weights: Weight for each component
        now: Current time

    Returns:
        Tuple of (total_score, component_scores)
    """
    components = {
        'urgency': calculate_urgency_score(task.due_date, now),
        'priority': calculate_priority_score(task.priority),
        'impact': calculate_impact_score(task),
        'effort': calculate_effort_score(task)
    }

    score = sum(weights[k] * components[k] for k in weights)

    return min(score, 1.0), components
```

---

## Phase 2: Database Layer

### Goal: CRUD Operations with Async SQLAlchemy

**Duration**: 3-4 hours

#### Step 2.1: Test Fixtures

Create `tests/conftest.py`:

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import User, Task
import uuid

# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

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

#### Step 2.2: Task CRUD Tests

Create `tests/integration/test_database.py`:

```python
import pytest
from app.db.models import Task
from app.db.crud import TaskCRUD
from datetime import datetime, timedelta

@pytest.mark.integration
class TestTaskCRUD:
    """Test task database operations."""

    @pytest.mark.asyncio
    async def test_create_task(self, db_session, test_user):
        """GIVEN user and task data
           WHEN task created
           THEN task saved to database with ID
        """
        # Arrange
        task_data = {
            "title": "Test task",
            "description": "Test description",
            "priority": 3,
            "user_id": test_user.id
        }

        # Act
        task = await TaskCRUD.create(db_session, task_data)

        # Assert
        assert task.id is not None
        assert task.title == "Test task"
        assert task.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, db_session, test_user):
        """GIVEN task exists
           WHEN retrieved by ID
           THEN returns correct task
        """
        # Arrange
        task = await TaskCRUD.create(db_session, {
            "title": "Find me",
            "user_id": test_user.id
        })

        # Act
        retrieved = await TaskCRUD.get_by_id(db_session, task.id, test_user.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == task.id
        assert retrieved.title == "Find me"

    @pytest.mark.asyncio
    async def test_list_user_tasks(self, db_session, test_user):
        """GIVEN user has multiple tasks
           WHEN tasks listed
           THEN returns only user's tasks
        """
        # Arrange
        await TaskCRUD.create(db_session, {
            "title": "Task 1",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "Task 2",
            "user_id": test_user.id
        })

        # Act
        tasks = await TaskCRUD.list_by_user(db_session, test_user.id)

        # Assert
        assert len(tasks) == 2
        assert all(t.user_id == test_user.id for t in tasks)

    @pytest.mark.asyncio
    async def test_update_task(self, db_session, test_user):
        """GIVEN task exists
           WHEN updated
           THEN changes persisted
        """
        # Arrange
        task = await TaskCRUD.create(db_session, {
            "title": "Original",
            "status": "pending",
            "user_id": test_user.id
        })

        # Act
        updated = await TaskCRUD.update(
            db_session,
            task.id,
            test_user.id,
            {"status": "completed"}
        )

        # Assert
        assert updated.status == "completed"
        assert updated.title == "Original"  # Unchanged

    @pytest.mark.asyncio
    async def test_delete_task(self, db_session, test_user):
        """GIVEN task exists
           WHEN deleted
           THEN no longer retrievable
        """
        # Arrange
        task = await TaskCRUD.create(db_session, {
            "title": "Delete me",
            "user_id": test_user.id
        })

        # Act
        await TaskCRUD.delete(db_session, task.id, test_user.id)

        # Assert
        retrieved = await TaskCRUD.get_by_id(db_session, task.id, test_user.id)
        assert retrieved is None
```

#### Step 2.3: Implement CRUD Operations

Create `app/db/crud.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
import uuid
from .models import Task

class TaskCRUD:
    """Task database operations."""

    @staticmethod
    async def create(session: AsyncSession, data: Dict[str, Any]) -> Task:
        """Create new task."""
        task = Task(**data)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

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

    @staticmethod
    async def list_by_user(
        session: AsyncSession,
        user_id: uuid.UUID,
        status: Optional[str] = None
    ) -> List[Task]:
        """List user's tasks."""
        query = select(Task).where(Task.user_id == user_id)

        if status:
            query = query.where(Task.status == status)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        session: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        data: Dict[str, Any]
    ) -> Task:
        """Update task."""
        task = await TaskCRUD.get_by_id(session, task_id, user_id)

        if not task:
            raise ValueError("Task not found")

        for key, value in data.items():
            setattr(task, key, value)

        await session.commit()
        await session.refresh(task)
        return task

    @staticmethod
    async def delete(
        session: AsyncSession,
        task_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """Delete task."""
        task = await TaskCRUD.get_by_id(session, task_id, user_id)

        if task:
            await session.delete(task)
            await session.commit()
```

---

## Phase 3: API Endpoints

### Goal: FastAPI Routes with Full Test Coverage

**Duration**: 4-5 hours

#### Step 3.1: API Test Client Fixture

Add to `tests/conftest.py`:

```python
from httpx import AsyncClient
from app.main import app

@pytest_asyncio.fixture
async def api_client(db_session):
    """Create test API client."""
    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Create auth headers for test user."""
    from app.middleware.auth import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
```

#### Step 3.2: Create Task Endpoint Tests

Create `tests/integration/test_api.py`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestTaskAPI:
    """Test task API endpoints."""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """GIVEN valid task data
           WHEN POST /api/tasks
           THEN task created and returned
        """
        # Arrange
        payload = {
            "title": "New task",
            "description": "Task description",
            "priority": 4
        }

        # Act
        response = await api_client.post(
            "/api/tasks",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New task"
        assert data["priority"] == 4
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_task_without_auth_fails(
        self,
        api_client: AsyncClient
    ):
        """GIVEN no authorization header
           WHEN POST /api/tasks
           THEN returns 401 Unauthorized
        """
        payload = {"title": "Task"}

        response = await api_client.post("/api/tasks", json=payload)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_task_invalid_priority_fails(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """GIVEN priority out of range
           WHEN POST /api/tasks
           THEN returns 422 Validation Error
        """
        payload = {
            "title": "Task",
            "priority": 10  # Max is 5
        }

        response = await api_client.post(
            "/api/tasks",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        db_session,
        test_user
    ):
        """GIVEN user has tasks
           WHEN GET /api/tasks
           THEN returns user's tasks
        """
        # Arrange (create test tasks)
        from app.db.crud import TaskCRUD
        await TaskCRUD.create(db_session, {
            "title": "Task 1",
            "user_id": test_user.id
        })
        await TaskCRUD.create(db_session, {
            "title": "Task 2",
            "user_id": test_user.id
        })

        # Act
        response = await api_client.get(
            "/api/tasks",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("title" in task for task in data)

    @pytest.mark.asyncio
    async def test_get_best_task(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        db_session,
        test_user
    ):
        """GIVEN multiple tasks
           WHEN GET /api/tasks/best
           THEN returns highest-scored task with explanation
        """
        # Arrange
        from app.db.crud import TaskCRUD
        from datetime import datetime, timedelta

        # Low priority, far deadline
        await TaskCRUD.create(db_session, {
            "title": "Low priority",
            "priority": 1,
            "due_date": datetime.now() + timedelta(days=7),
            "user_id": test_user.id
        })

        # High priority, soon deadline
        await TaskCRUD.create(db_session, {
            "title": "High priority",
            "priority": 5,
            "due_date": datetime.now() + timedelta(hours=6),
            "user_id": test_user.id
        })

        # Act
        response = await api_client.get(
            "/api/tasks/best",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task"]["title"] == "High priority"
        assert data["score"] > 0.7
        assert "explanation" in data
```

---

## Phase 4: Authentication

### Goal: JWT Auth with Tests

**Duration**: 2-3 hours

Create `tests/unit/test_auth.py`:

```python
import pytest
from app.middleware.auth import create_access_token, verify_token
from app.utils.security import hash_password, verify_password
import uuid

class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_password_hashed_not_plaintext(self):
        """GIVEN plaintext password
           WHEN hashed
           THEN hash doesn't match original
        """
        password = "supersecret123"

        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """GIVEN correct password
           WHEN verified against hash
           THEN returns True
        """
        password = "supersecret123"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_incorrect_password(self):
        """GIVEN incorrect password
           WHEN verified against hash
           THEN returns False
        """
        correct = "supersecret123"
        wrong = "wrongpassword"
        hashed = hash_password(correct)

        result = verify_password(wrong, hashed)

        assert result is False

class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_token(self):
        """GIVEN user ID
           WHEN token created
           THEN token is valid string
        """
        user_id = uuid.uuid4()

        token = create_access_token(str(user_id))

        assert isinstance(token, str)
        assert len(token) > 20

    def test_verify_valid_token(self):
        """GIVEN valid token
           WHEN verified
           THEN returns user ID
        """
        user_id = uuid.uuid4()
        token = create_access_token(str(user_id))

        decoded_id = verify_token(token)

        assert decoded_id == str(user_id)

    def test_verify_invalid_token_raises(self):
        """GIVEN invalid token
           WHEN verified
           THEN raises exception
        """
        from jose import JWTError

        with pytest.raises(JWTError):
            verify_token("invalid.token.here")
```

---

## Phase 5: Integration Tests

### Goal: End-to-End User Flows

**Duration**: 2-3 hours

Create `tests/e2e/test_user_flows.py`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestCompleteUserFlow:
    """Test complete user scenarios."""

    @pytest.mark.asyncio
    async def test_user_registration_to_task_completion(
        self,
        api_client: AsyncClient
    ):
        """GIVEN new user
           WHEN registers, logs in, creates task, completes task
           THEN full flow works
        """
        # 1. Register
        register_response = await api_client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create task
        create_response = await api_client.post(
            "/api/tasks",
            json={"title": "My first task", "priority": 5},
            headers=headers
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # 3. Get best task
        best_response = await api_client.get(
            "/api/tasks/best",
            headers=headers
        )
        assert best_response.status_code == 200
        assert best_response.json()["task"]["id"] == task_id

        # 4. Complete task
        update_response = await api_client.put(
            f"/api/tasks/{task_id}",
            json={"status": "completed"},
            headers=headers
        )
        assert update_response.status_code == 200

        # 5. Verify no tasks left
        list_response = await api_client.get(
            "/api/tasks?status=pending",
            headers=headers
        )
        assert len(list_response.json()) == 0
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: mindflow_test
          POSTGRES_USER: mindflow
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://mindflow:test_password@localhost:5432/mindflow_test
          SECRET_KEY: test-secret-key
        run: |
          cd backend
          pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          cd backend
          pytest --cov=app --cov-fail-under=85
```

---

## Development Timeline

### Week 1: Core Domain + Database

| Day | Tasks | Duration |
|-----|-------|----------|
| Mon | Setup test infrastructure, fixtures | 2h |
| Mon | Phase 1: Scoring logic tests + impl | 2h |
| Tue | Phase 2: Database CRUD tests | 3h |
| Tue | Phase 2: Implement CRUD operations | 2h |
| Wed | Refactor + 100% coverage for Phase 1-2 | 2h |

### Week 2: API + Auth

| Day | Tasks | Duration |
|-----|-------|----------|
| Thu | Phase 3: API endpoint tests | 3h |
| Thu | Phase 3: Implement API routes | 2h |
| Fri | Phase 4: Auth tests + implementation | 3h |
| Fri | Phase 5: E2E tests | 2h |

### Week 3: Polish + Deploy

| Day | Tasks | Duration |
|-----|-------|----------|
| Mon | Fix all failing tests | 2h |
| Mon | Reach 85%+ coverage | 2h |
| Tue | Setup CI/CD pipeline | 2h |
| Tue | Deploy to DigitalOcean | 2h |
| Wed | Production testing | 2h |

**Total**: ~40 hours across 3 weeks

---

## Next Steps

1. ✅ Read this TDD plan
2. Setup test environment locally
3. Start with Phase 1 (scoring tests)
4. Follow Red-Green-Refactor cycle
5. Run tests frequently (`pytest -v`)
6. Maintain >85% coverage
7. Deploy with confidence

---

**Version**: 1.0.0
**Last Updated**: 2025-10-30
**Coverage Target**: >85% (enforced in pytest.ini and CI/CD)
