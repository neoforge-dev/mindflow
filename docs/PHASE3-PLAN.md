# Phase 3: API Endpoints Implementation Plan

**Status**: Ready to Execute
**Approach**: Outside-In TDD (API Tests → Implementation)
**Duration**: 4-5 hours
**Coverage Target**: >85%
**Created**: 2025-10-30

---

## Overview

Build the **FastAPI REST API layer** that exposes our database operations over HTTP. This connects the Custom GPT to our PostgreSQL database through a clean, well-documented API.

**What We're Building**:
- FastAPI application with 7 REST endpoints
- Dependency injection for database sessions
- Request/response validation with Pydantic
- Error handling middleware with proper HTTP status codes
- OpenAPI documentation (automatic with FastAPI)
- 15-20 API integration tests

**What We're NOT Building** (yet):
- Authentication/JWT (Phase 4)
- Rate limiting (Phase 5)
- CORS middleware (add when deploying)
- Task scoring endpoint (will use existing CRUD for now)
- Background jobs/async tasks
- WebSocket support

**Success Criteria**:
- All 15-20 API tests pass
- >85% code coverage for API layer
- OpenAPI docs accessible at `/docs`
- Health check returns 200
- Can CRUD tasks via HTTP
- Proper error responses (404, 400, 500)
- User isolation enforced in all endpoints

---

## Architecture Decision

### Minimal FastAPI Structure

We'll create a **simple, flat structure** since we don't need complex patterns yet:

```
backend/app/
├── main.py              # FastAPI app, middleware, startup
├── dependencies.py      # Dependency injection (get_db, get_current_user_stub)
├── api/
│   ├── __init__.py
│   └── tasks.py         # All task endpoints in one router
├── db/                  # ✅ Already complete (Phase 2)
├── schemas/             # ✅ Already complete (Phase 2)
└── config.py            # ✅ Already complete (Phase 2)
```

**Why this structure?**
- **Simple**: Only 3 new files needed
- **Pragmatic**: No over-engineering with services/repositories
- **Testable**: Easy to test with FastAPI's TestClient
- **Scalable**: Can refactor when we add more features

**What we're avoiding**:
- ❌ Separate service layer (CRUD is sufficient)
- ❌ Repository pattern (SQLAlchemy is our repository)
- ❌ Complex middleware stack (only error handling)
- ❌ Multiple routers (one router for tasks is enough)

---

## Files to Create/Modify

### New Files (4 files)

```
backend/
├── app/
│   ├── main.py                      # CREATE: FastAPI app setup
│   ├── dependencies.py              # CREATE: Dependency injection
│   └── api/
│       ├── __init__.py              # CREATE: Empty
│       └── tasks.py                 # CREATE: Task endpoints
└── tests/
    └── api/
        ├── __init__.py              # CREATE: Empty
        └── test_tasks_api.py        # CREATE: API integration tests
```

### Existing Files (no changes needed)

```
backend/app/
├── db/                  # ✅ Phase 2 complete
│   ├── database.py      # ✅ get_db() dependency already exists
│   ├── models.py        # ✅ All models ready
│   └── crud.py          # ✅ All operations ready
├── schemas/
│   └── task.py          # ✅ Pydantic schemas ready
└── config.py            # ✅ Settings ready
```

---

## API Endpoints Design

### Endpoint List

| Method | Endpoint | Purpose | Request | Response | Status Codes |
|--------|----------|---------|---------|----------|--------------|
| GET | `/health` | Health check | None | `{"status": "healthy"}` | 200 |
| POST | `/api/tasks` | Create task | TaskCreate | TaskResponse | 201, 400 |
| GET | `/api/tasks/pending` | Get pending tasks | None | List[TaskResponse] | 200 |
| GET | `/api/tasks` | List tasks | ?status= | List[TaskResponse] | 200 |
| GET | `/api/tasks/{id}` | Get task | None | TaskResponse | 200, 404 |
| PUT | `/api/tasks/{id}` | Update task | TaskUpdate | TaskResponse | 200, 404, 400 |
| DELETE | `/api/tasks/{id}` | Delete task | None | `{"message": "deleted"}` | 204, 404 |

**⚠️ CRITICAL: Route Order Matters!**
- `/api/tasks/pending` MUST be defined BEFORE `/api/tasks/{id}` in code
- FastAPI matches routes in order - if `/{id}` comes first, it will catch "pending" as a UUID
- Define routes in the order shown above to avoid 422 validation errors

**Note**: All `/api/tasks/*` endpoints require `user_id` in query params (Phase 3). In Phase 4, we'll extract this from JWT token.

### Temporary Authentication Strategy (Phase 3)

**Problem**: We need user_id for database queries but don't have JWT auth yet.

**Solution**: Use query parameter `?user_id={uuid}` for all endpoints temporarily.

```python
# Phase 3 (temporary)
@router.get("/api/tasks")
async def list_tasks(user_id: UUID, db: AsyncSession = Depends(get_db)):
    tasks = await TaskCRUD.list_by_user(db, user_id)
    return tasks

# Phase 4 (final)
@router.get("/api/tasks")
async def list_tasks(
    current_user: User = Depends(get_current_user),  # From JWT
    db: AsyncSession = Depends(get_db)
):
    tasks = await TaskCRUD.list_by_user(db, current_user.id)
    return tasks
```

**Benefits**:
- ✅ Simple to implement right now
- ✅ Easy to test without auth complexity
- ✅ Clear migration path to JWT in Phase 4
- ✅ User isolation still enforced

**Custom GPT Integration**: Custom GPT will pass `user_id` as query param until Phase 4.

---

## Detailed Function & Test Specifications

### Part 1: FastAPI Application (`app/main.py`)

#### Functions

**`create_app() -> FastAPI`**
Creates FastAPI application instance with metadata, exception handlers, and CORS middleware. Returns configured app.

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="MindFlow API",
        description="AI-first task manager API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware (allow all in dev, specific in prod)
    if app.debug:
        # Development: Allow all for testing
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Production: Specific origins only
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://chat.openai.com",
                "https://chatgpt.com",
                "https://*.openai.com",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include routers
    from app.api.tasks import router as tasks_router
    app.include_router(tasks_router)

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log full traceback for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Unhandled exception", exc_info=exc)

        # Return detailed error in dev, generic in prod
        if app.debug:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error": str(exc),
                    "type": type(exc).__name__
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    return app

app = create_app()
```

**`@app.get("/health")`**
Health check endpoint. Returns status 200 with `{"status": "healthy"}`.

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}
```

#### Tests

**`test_health_check_returns_200`**
GET /health returns 200 with healthy status

**`test_openapi_docs_accessible`**
GET /docs returns 200 with HTML documentation

**`test_cors_headers_present`**
OPTIONS request includes CORS headers for chat.openai.com

---

### Part 2: Dependencies (`app/dependencies.py`)

#### Functions

**`async def get_db() -> AsyncSession`**
Yields database session for request scope. Automatically closes session after request.

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal

async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session
```

**`async def get_current_user_id(user_id: UUID) -> UUID`**
Temporary dependency that returns user_id from query param. Will be replaced with JWT auth in Phase 4.

```python
from uuid import UUID
from fastapi import Query

async def get_current_user_id(
    user_id: UUID = Query(..., description="User ID (temporary - will use JWT in Phase 4)")
) -> UUID:
    """Temporary: Extract user_id from query param. Phase 4: Extract from JWT token."""
    return user_id
```

#### Tests

**`test_get_db_yields_session`**
Dependency yields valid AsyncSession instance

**`test_get_db_closes_session_after_request`**
Session automatically closed after request completes

**`test_get_current_user_id_returns_uuid`**
Returns valid UUID from query parameter

---

### Part 3: Task Endpoints (`app/api/tasks.py`)

#### Functions

**`@router.post("/api/tasks", status_code=201)`**
Creates new task for user. Accepts TaskCreate, returns TaskResponse with 201 status.

```python
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.crud import TaskCRUD
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.dependencies import get_db, get_current_user_id

router = APIRouter()

# ⚠️ ROUTE ORDER CRITICAL: Define /pending BEFORE /{id}
# FastAPI matches routes sequentially - wrong order causes 422 errors

@router.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create new task for user."""
    data = task_data.model_dump()
    data["user_id"] = user_id
    task = await TaskCRUD.create(db, data)
    return task
```

**`@router.get("/api/tasks/pending")`**
Gets all pending/in-progress tasks (excludes completed and snoozed). Returns List[TaskResponse].

```python
@router.get("/api/tasks/pending", response_model=list[TaskResponse])
async def get_pending_tasks(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending/in-progress tasks."""
    tasks = await TaskCRUD.get_pending_tasks(db, user_id)
    return tasks
```

**`@router.get("/api/tasks")`**
Lists all tasks for user with optional status filter. Returns List[TaskResponse].

```python
@router.get("/api/tasks", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: str | None = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List user's tasks with optional status filter."""
    tasks = await TaskCRUD.list_by_user(db, user_id, status_filter)
    return tasks
```

**`@router.get("/api/tasks/{task_id}")`**
Retrieves specific task by ID. Returns TaskResponse or 404 if not found/wrong user.

```python
@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get specific task by ID."""
    task = await TaskCRUD.get_by_id(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task
```

**`@router.put("/api/tasks/{task_id}")`**
Updates task fields. Accepts TaskUpdate, returns TaskResponse or 404 if not found.

```python
@router.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update task fields."""
    data = task_data.model_dump(exclude_unset=True)  # Only updated fields
    try:
        task = await TaskCRUD.update(db, task_id, user_id, data)
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

**`@router.delete("/api/tasks/{task_id}", status_code=204)`**
Deletes task. Returns 204 No Content on success, 404 if not found.

```python
@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete task."""
    task = await TaskCRUD.get_by_id(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    await TaskCRUD.delete(db, task_id, user_id)
    return None  # 204 No Content
```

#### Tests

**`test_create_task_returns_201_with_task`**
POST /api/tasks returns 201 with created task

**`test_create_task_validates_required_fields`**
POST /api/tasks returns 400 if title missing

**`test_create_task_validates_priority_range`**
POST /api/tasks returns 400 if priority outside 1-5

**`test_list_tasks_returns_200_with_tasks`**
GET /api/tasks returns 200 with user's tasks

**`test_list_tasks_filters_by_status`**
GET /api/tasks?status=pending returns only pending tasks

**`test_list_tasks_empty_for_new_user`**
GET /api/tasks returns empty list for user with no tasks

**`test_get_task_returns_200_with_task`**
GET /api/tasks/{id} returns 200 with task details

**`test_get_task_returns_404_for_nonexistent`**
GET /api/tasks/{fake-id} returns 404 not found

**`test_get_task_returns_404_for_other_user`**
GET /api/tasks/{id} returns 404 if task belongs to different user

**`test_update_task_returns_200_with_updated_task`**
PUT /api/tasks/{id} returns 200 with updated fields

**`test_update_task_validates_partial_update`**
PUT /api/tasks/{id} updates only provided fields, leaves others unchanged

**`test_update_task_returns_404_for_nonexistent`**
PUT /api/tasks/{fake-id} returns 404 not found

**`test_update_task_validates_priority_range`**
PUT /api/tasks/{id} returns 400 if priority invalid

**`test_delete_task_returns_204`**
DELETE /api/tasks/{id} returns 204 with no content

**`test_delete_task_returns_404_for_nonexistent`**
DELETE /api/tasks/{fake-id} returns 404 not found

**`test_delete_task_removes_from_database`**
After DELETE /api/tasks/{id}, GET returns 404

**`test_get_pending_tasks_returns_actionable_tasks`**
GET /api/tasks/pending returns pending and in_progress tasks only

**`test_get_pending_tasks_excludes_completed`**
GET /api/tasks/pending excludes completed tasks

**`test_get_pending_tasks_excludes_snoozed`**
GET /api/tasks/pending excludes tasks with future snoozed_until

---

## Implementation Order (Outside-In TDD)

### Step 1: Setup API Structure (10 min)

```bash
cd backend

# Create directories
mkdir -p app/api
mkdir -p tests/api

# Create files
touch app/main.py
touch app/dependencies.py
touch app/api/__init__.py
touch app/api/tasks.py
touch tests/api/__init__.py
touch tests/api/test_tasks_api.py
```

### Step 2: Write Health Check Test + Implementation (15 min)

**RED**: Write health check test in `tests/api/test_tasks_api.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check_returns_200():
    """GET /health returns 200 with healthy status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "2.0.0"}
```

**GREEN**: Implement `app/main.py` with health check

**REFACTOR**: Add OpenAPI metadata, improve structure

### Step 3: Write ALL Route Tests First (45 min)

**Purpose**: Define all route tests upfront to ensure correct ordering from the start.

**Write tests in this exact order** (matches route definition order):

```python
# tests/api/test_tasks_api.py

# 1. Health check
@pytest.mark.asyncio
async def test_health_check_returns_200():
    """GET /health returns 200 with healthy status"""

# 2. Create task
@pytest.mark.asyncio
async def test_create_task_returns_201_with_task(test_user):
    """POST /api/tasks returns 201 with created task"""

# 3. Get pending tasks (BEFORE get single task!)
@pytest.mark.asyncio
async def test_get_pending_tasks_returns_tasks(test_user):
    """GET /api/tasks/pending returns pending and in_progress tasks"""

# 4. List tasks
@pytest.mark.asyncio
async def test_list_tasks_returns_200_with_tasks(test_user):
    """GET /api/tasks returns 200 with user's tasks"""

# 5. Get single task (AFTER pending route)
@pytest.mark.asyncio
async def test_get_task_returns_200_with_task(test_user, test_task):
    """GET /api/tasks/{id} returns 200 with task details"""

# 6. Update task
@pytest.mark.asyncio
async def test_update_task_returns_200_with_updated_task(test_user, test_task):
    """PUT /api/tasks/{id} returns 200 with updated fields"""

# 7. Delete task
@pytest.mark.asyncio
async def test_delete_task_returns_204(test_user, test_task):
    """DELETE /api/tasks/{id} returns 204 with no content"""

# Continue with validation/error tests...
```

**Key Point**: This order matches the route definition order in `app/api/tasks.py`.

### Step 4: Implement Routes in Correct Order (75 min)

**RED → GREEN → REFACTOR** for each route:

1. Run tests (all should fail)
2. Implement routes in `app/api/tasks.py` in **exact same order as tests**
3. Run tests again (should pass one by one)
4. Refactor for elegance

**Route implementation order** (in `app/api/tasks.py`):
```python
router = APIRouter()

# 1. POST /api/tasks
@router.post("/api/tasks", ...)
async def create_task(...): pass

# 2. GET /api/tasks/pending (BEFORE /{id}!)
@router.get("/api/tasks/pending", ...)
async def get_pending_tasks(...): pass

# 3. GET /api/tasks
@router.get("/api/tasks", ...)
async def list_tasks(...): pass

# 4. GET /api/tasks/{task_id} (AFTER /pending!)
@router.get("/api/tasks/{task_id}", ...)
async def get_task(...): pass

# 5. PUT /api/tasks/{task_id}
@router.put("/api/tasks/{task_id}", ...)
async def update_task(...): pass

# 6. DELETE /api/tasks/{task_id}
@router.delete("/api/tasks/{task_id}", ...)
async def delete_task(...): pass
```

### Step 5: Write Error Handling Tests (20 min)

```python
@pytest.mark.asyncio
async def test_validation_error_returns_400():
    """POST /api/tasks with invalid data returns 400"""

@pytest.mark.asyncio
async def test_internal_error_returns_500():
    """Unexpected error returns 500 with generic message"""
```

### Step 6: Add Dependencies (15 min)

Implement `app/dependencies.py` with:
- `get_db()` - Database session
- `get_current_user_id()` - User ID from query param

### Step 7: Run Full Test Suite (10 min)

```bash
make test
```

Expected output:
- All 15-20 API tests pass
- Database layer tests still pass (19 tests)
- Total: 34-39 tests passing
- Coverage: >85% overall

### Step 8: Manual API Testing (20 min)

```bash
# Start server
make run

# Test with curl
curl http://localhost:8000/health
curl http://localhost:8000/docs  # OpenAPI docs

# Create task
curl -X POST "http://localhost:8000/api/tasks?user_id=$(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "priority": 3}'

# List tasks
curl "http://localhost:8000/api/tasks?user_id=YOUR_USER_ID"
```

### Step 9: Update Documentation (15 min)

Update `backend/README.md`:
- Add "Running the API" section
- Document endpoints with examples
- Add OpenAPI docs link

---

## Testing Strategy

### Test Fixtures (add to `tests/conftest.py`)

```python
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def test_client():
    """Async HTTP client for API testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest_asyncio.fixture
async def authenticated_client(test_client, test_user):
    """Client with pre-set user_id for convenience."""
    # Add user_id to all requests automatically
    test_client.params = {"user_id": str(test_user.id)}
    return test_client
```

### Test Organization

```
tests/
├── conftest.py              # ✅ Existing fixtures + new API fixtures
├── integration/
│   └── test_database.py     # ✅ 19 existing tests
└── api/
    └── test_tasks_api.py    # NEW: 15-20 API tests
```

### Coverage Targets

- `app/main.py`: >90% (health check + error handlers)
- `app/dependencies.py`: >80% (simple functions)
- `app/api/tasks.py`: >90% (all endpoints + error paths)
- Overall: >85%

---

## Verification Checklist

Before considering Phase 3 complete:

### Functionality
- [ ] All 15-20 API tests pass
- [ ] Health check returns 200
- [ ] Can create task via POST
- [ ] Can list tasks via GET
- [ ] Can get specific task via GET
- [ ] Can update task via PUT
- [ ] Can delete task via DELETE
- [ ] Can get pending tasks via GET
- [ ] Status filter works for list endpoint

### Error Handling
- [ ] 404 for nonexistent tasks
- [ ] 400 for validation errors
- [ ] 500 for unexpected errors
- [ ] User isolation enforced (can't access other user's tasks)

### Documentation
- [ ] OpenAPI docs accessible at /docs
- [ ] ReDoc accessible at /redoc
- [ ] All endpoints documented with descriptions
- [ ] Request/response schemas visible in docs

### Code Quality
- [ ] Coverage >85% for API layer
- [ ] All endpoints use async/await correctly
- [ ] Proper dependency injection
- [ ] Type hints on all functions
- [ ] No linting errors

---

## Time Budget

| Step | Duration | Cumulative | Notes |
|------|----------|------------|-------|
| 1. Setup API structure | 15 min | 15 min | +5min for CORS/fixture fixes |
| 2. Health check test + impl | 15 min | 30 min | Same |
| 3. ALL route tests (define order) | 45 min | 75 min | +15min to avoid ordering bugs |
| 4. Implement routes in order | 75 min | 150 min | -15min (tests written) |
| 5. Error handling tests | 20 min | 170 min | Same |
| 6. Dependencies implementation | 15 min | 185 min | Same |
| 7. Run full test suite | 10 min | 195 min | Same |
| 8. Manual API testing | 20 min | 215 min | Same |
| 9. Update documentation | 15 min | 230 min | Same |
| **Total** | **3h 50min** | | |

**Buffer**: 40 minutes for debugging/refactoring

**Final**: 4.5 hours total

**Key Changes from Original**:
- Step 1: +5 min for implementing CORS/fixture fixes
- Step 3: +15 min to write all route tests upfront (ensures correct order)
- Step 4: -15 min because tests are already written

---

## Success Metrics

**Definition of Done**:
1. ✅ All 15-20 API tests passing
2. ✅ Coverage >85% for API layer
3. ✅ OpenAPI docs accessible and complete
4. ✅ Can perform all CRUD operations via HTTP
5. ✅ Proper error responses (404, 400, 500)
6. ✅ User isolation enforced
7. ✅ No linting errors
8. ✅ Documentation updated

**Phase 3 Complete When**:
- Developer can start FastAPI server with `make run`
- Custom GPT can call API endpoints with user_id query param
- All database operations accessible via REST API
- Ready for Phase 4 (JWT authentication)

---

## Next Phase Preview

**Phase 4: Authentication** (5-6 hours):
- JWT token generation and validation
- Password hashing with bcrypt
- `/api/auth/register` endpoint
- `/api/auth/login` endpoint
- `get_current_user()` dependency (replaces `get_current_user_id()`)
- Protected routes with `Depends(get_current_user)`
- Remove `user_id` query parameter
- 10-15 auth tests

---

## Critical Fixes Applied (v1.1)

**Updated**: 2025-10-30 (Post-Review)

### 1. 🚨 Fixed Route Ordering Bug
- **Issue**: `/api/tasks/{id}` would catch "pending" as UUID parameter
- **Fix**: Reordered endpoints - `/pending` now defined BEFORE `/{id}` everywhere
- **Impact**: Prevents 422 validation errors, saves 30-60 min debugging

### 2. 🟡 Improved CORS Configuration
- **Issue**: Too restrictive - only allowed `chat.openai.com`
- **Fix**: Allow all origins in dev mode, specific list in production
- **Impact**: Enables local testing, Postman usage, future dashboard

### 3. 🟡 Enhanced Test Fixtures
- **Issue**: Fixture wasn't truly async, missing cleanup
- **Fix**: Use `pytest_asyncio` with proper async context manager
- **Impact**: Proper async handling, automatic cleanup, convenience fixture

### 4. 🟡 Better Error Handling
- **Issue**: Generic 500 errors hide debugging info
- **Fix**: Log exceptions, show details in dev mode
- **Impact**: Faster debugging during development

### 5. ⏱️ Revised Time Budget
- **Change**: Write all route tests upfront (Step 3: +15 min)
- **Benefit**: Ensures correct route ordering from start
- **Total**: Still 4.5 hours with buffer

---

**Status**: Ready to execute with critical fixes applied
**Next Action**: Create API structure (Step 1)
**Document Version**: 1.1 (Post-Review)
**Last Updated**: 2025-10-30
