# Phase 2: Database Layer Implementation Plan

**Status**: Ready to Execute
**Approach**: Test-Driven Development (Outside-In)
**Duration**: 3-4 hours
**Coverage Target**: >90%

---

## Overview

We are building the **PostgreSQL database layer** for MindFlow's FastAPI backend from scratch. This replaces the Google Apps Script/Sheets backend.

**What We're Building**:
- SQLAlchemy async models (User, Task, UserPreferences)
- Database connection management with async sessions
- CRUD operations for tasks (Create, Read, Update, Delete)
- Complete test suite with fixtures and real database tests

**What We're NOT Building** (yet):
- API endpoints (Phase 3)
- Authentication middleware (Phase 4)
- Task scoring logic (Phase 1 - can do in parallel)
- Frontend (separate)

**Success Criteria**:
- All tests pass
- >90% code coverage for database layer
- Can create, read, update, delete tasks in PostgreSQL
- Proper async/await patterns throughout

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
│   │   ├── database.py          # CREATE: Async SQLAlchemy engine
│   │   ├── models.py            # CREATE: User, Task, UserPreferences
│   │   └── crud.py              # CREATE: Database operations
│   └── schemas/
│       ├── __init__.py          # CREATE: Empty
│       └── task.py              # CREATE: Pydantic models
├── tests/
│   ├── __init__.py              # CREATE: Empty
│   ├── conftest.py              # CREATE: Pytest fixtures
│   └── integration/
│       ├── __init__.py          # CREATE: Empty
│       └── test_database.py    # CREATE: CRUD tests
├── requirements.txt             # CREATE: Python dependencies
├── requirements-dev.txt         # CREATE: Test dependencies
├── pytest.ini                   # CREATE: Pytest configuration
├── .env.example                 # CREATE: Environment template
└── alembic.ini                  # CREATE: (later for migrations)
```

### Files to NOT Touch

```
src/gas/                         # IGNORE: Keep GAS code for reference
tests/ (root)                    # IGNORE: Old GAS tests
pyproject.toml                   # KEEP: Already configured
```

---

## Detailed Function & Test Specifications

### Part 1: Configuration (`app/config.py`)

#### Functions

**`class Settings(BaseSettings)`**
Load environment variables using Pydantic. Validates DATABASE_URL, SECRET_KEY, and environment mode.

**`get_settings() -> Settings`**
Return singleton instance of settings. Caches configuration for performance.

#### Tests (not needed for simple config)

---

### Part 2: Database Connection (`app/db/database.py`)

#### Functions

**`create_async_engine() -> AsyncEngine`**
Create SQLAlchemy async engine for PostgreSQL. Configure connection pooling with pool_size=5, pool_pre_ping=True.

**`async_session_maker() -> AsyncSession`**
Session factory for database operations. Set expire_on_commit=False for async compatibility.

**`async def get_db() -> AsyncSession`**
FastAPI dependency injection for database sessions. Yields session, ensures proper cleanup with async context manager.

**`Base = declarative_base()`**
SQLAlchemy declarative base for all models.

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
User model with id, email, password_hash, full_name, plan, timestamps. Has relationship to tasks cascade delete.

**`class Task(Base)`**
Task model with id, user_id, title, description, status, priority, due_date, timestamps, tags. Foreign key to User with CASCADE.

**`class UserPreferences(Base)`**
Preferences model with id, user_id, scoring weights, timezone, work hours. One-to-one relationship with User.

**`TaskStatus(Enum)`**
Enum for task status: pending, in_progress, completed, snoozed.

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

---

### Part 4: Pydantic Schemas (`app/schemas/task.py`)

#### Classes/Functions

**`class TaskBase(BaseModel)`**
Base task schema with title, description, priority, due_date, tags. Validates title length and priority range.

**`class TaskCreate(TaskBase)`**
Schema for creating tasks. Validates title not empty, priority 1-5.

**`class TaskUpdate(BaseModel)`**
Schema for updating tasks. All fields optional: status, priority, due_date.

**`class TaskResponse(TaskBase)`**
Response schema adds id, user_id, status, timestamps. Config from_attributes=True.

#### Tests

**`test_task_create_validates_title_required`**
TaskCreate raises ValidationError when title missing or empty.

**`test_task_create_validates_priority_range`**
TaskCreate raises ValidationError when priority outside 1-5 range.

**`test_task_update_allows_partial_updates`**
TaskUpdate accepts only status field, ignores others correctly.

**`test_task_response_serializes_from_orm_model`**
TaskResponse converts SQLAlchemy Task model to JSON successfully.

---

### Part 5: CRUD Operations (`app/db/crud.py`)

#### Functions

**`async def create_task(session, data) -> Task`**
Create new task in database. Accepts dict, returns Task model with generated ID.

**`async def get_task_by_id(session, task_id, user_id) -> Task | None`**
Retrieve task by ID with user validation. Returns None if not found or wrong user.

**`async def list_tasks_by_user(session, user_id, status=None) -> list[Task]`**
List all user's tasks with optional status filter. Orders by created_at DESC.

**`async def update_task(session, task_id, user_id, data) -> Task`**
Update task fields for given user. Raises ValueError if task not found.

**`async def delete_task(session, task_id, user_id) -> None`**
Soft or hard delete task. Validates ownership before deletion.

**`async def get_pending_tasks(session, user_id) -> list[Task]`**
Get all non-completed tasks for user. Excludes completed and snoozed.

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

**`test_update_task_raises_for_nonexistent_task`**
Update raises ValueError when task doesn't exist or wrong user.

**`test_delete_task_removes_from_database`**
After deletion, task no longer retrievable by ID query.

**`test_delete_task_validates_ownership`**
Cannot delete another user's task, operation fails silently.

**`test_get_pending_tasks_excludes_completed`**
Returns pending and in_progress, excludes completed and snoozed.

---

### Part 6: Test Fixtures (`tests/conftest.py`)

#### Functions

**`@pytest_asyncio.fixture async def db_engine()`**
Create test SQLite in-memory database engine. Creates tables, yields, drops tables.

**`@pytest_asyncio.fixture async def db_session(db_engine)`**
Create async session for tests. Yields session, rolls back after test.

**`@pytest_asyncio.fixture async def test_user(db_session)`**
Create and return test user with known credentials. Commits to database.

**`@pytest_asyncio.fixture async def test_user_2(db_session)`**
Create second test user for multi-user test scenarios.

**`@pytest_asyncio.fixture async def test_task(db_session, test_user)`**
Create sample task for test user. Returns committed task.

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
```

**backend/requirements-dev.txt**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
aiosqlite==0.19.0
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
```

### Step 3: Write Config (15 min)

**RED**: Write test (skip for config)
**GREEN**: Implement `app/config.py`
**REFACTOR**: Add type hints, docstrings

### Step 4: Write Database Connection Tests (20 min)

**RED**: Write `test_database_connection_succeeds` in `tests/integration/test_database.py`
**GREEN**: Implement `app/db/database.py` with async engine
**REFACTOR**: Extract constants, improve error handling

### Step 5: Write Model Tests (30 min)

**RED**: Write all 6 model tests in `test_database.py`
**GREEN**: Implement `app/db/models.py` with User, Task, UserPreferences
**REFACTOR**: Add indexes, improve relationships

### Step 6: Write Pydantic Schema Tests (20 min)

**RED**: Write all 4 schema validation tests
**GREEN**: Implement `app/schemas/task.py` with validators
**REFACTOR**: Add custom validators, better error messages

### Step 7: Write CRUD Tests (45 min)

**RED**: Write all 11 CRUD tests in `test_database.py`
**GREEN**: Implement each CRUD function one by one
**REFACTOR**: Extract common query patterns, add error handling

### Step 8: Write Fixtures (20 min)

**GREEN**: Implement all fixtures in `tests/conftest.py`
**REFACTOR**: Make fixtures reusable, add more test users

### Step 9: Run Full Test Suite (10 min)

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -v --cov=app
```

**Expected**: All tests pass, >90% coverage

### Step 10: Verify Coverage (10 min)

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

- [ ] All 28 tests pass
- [ ] Coverage >90% for database layer
- [ ] Can create user and task in database
- [ ] Can retrieve tasks by user
- [ ] Can update task status
- [ ] Can delete task
- [ ] Async/await used correctly throughout
- [ ] No N+1 query problems
- [ ] Proper transaction handling
- [ ] Foreign key constraints work
- [ ] Cascade delete works
- [ ] Test fixtures are reusable

---

## Next Phase Preview

**Phase 3: API Endpoints** (4-5 hours)
- FastAPI app with routes
- `/api/tasks` CRUD endpoints
- `/api/tasks/best` for scoring
- Request/response validation
- Error handling
- 15-20 API endpoint tests

---

## Time Budget

| Step | Duration | Cumulative |
|------|----------|------------|
| 1. Setup | 15 min | 15 min |
| 2. Dependencies | 10 min | 25 min |
| 3. Config | 15 min | 40 min |
| 4. Database tests + impl | 20 min | 60 min |
| 5. Model tests + impl | 30 min | 90 min |
| 6. Schema tests + impl | 20 min | 110 min |
| 7. CRUD tests + impl | 45 min | 155 min |
| 8. Fixtures | 20 min | 175 min |
| 9. Test run | 10 min | 185 min |
| 10. Coverage check | 10 min | 195 min |
| **Total** | **3h 15min** | |

**Buffer**: 45 minutes for debugging/refactoring

**Final**: 4 hours total

---

## Commands to Execute

```bash
# Start Phase 2
cd /Users/bogdan/work/neoforge-dev/mindflow

# Setup structure (Step 1)
bash -c "$(cat <<'EOF'
mkdir -p backend/{app/{db,schemas},tests/integration}
touch backend/app/{__init__,config}.py
touch backend/app/db/{__init__,database,models,crud}.py
touch backend/app/schemas/{__init__,task}.py
touch backend/tests/{__init__,conftest}.py
touch backend/tests/integration/{__init__,test_database}.py
touch backend/{pytest.ini,requirements.txt,requirements-dev.txt,.env.example}
EOF
)"

# Install dependencies (Step 2)
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests after each implementation
pytest tests/integration/test_database.py::test_database_connection_succeeds -v
pytest tests/integration/test_database.py -v
pytest -v --cov=app --cov-report=term-missing

# Final verification
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

**Status**: Ready to execute
**Next Action**: Create project structure (Step 1)
