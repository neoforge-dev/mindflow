"""Task API endpoints - route order is critical!"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import TaskCRUD
from app.dependencies import get_current_user_id, get_db
from app.middleware.rate_limit import limiter
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()

# ⚠️ ROUTE ORDER CRITICAL: Define /pending BEFORE /{id}
# FastAPI matches routes sequentially - wrong order causes 422 errors


@router.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_task(
    request: Request,  # noqa: ARG001
    task_data: TaskCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create new task for user."""
    data = task_data.model_dump()
    data["user_id"] = user_id
    task = await TaskCRUD.create(db, data)
    return task


@router.get("/api/tasks/pending", response_model=list[TaskResponse])
@limiter.limit("60/minute")
async def get_pending_tasks(
    request: Request,  # noqa: ARG001
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending/in-progress tasks (excludes completed and snoozed)."""
    tasks = await TaskCRUD.get_pending_tasks(db, user_id)
    return tasks


@router.get("/api/tasks", response_model=list[TaskResponse])
@limiter.limit("60/minute")
async def list_tasks(
    request: Request,  # noqa: ARG001
    status: str | None = None,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List user's tasks with optional status filter."""
    tasks = await TaskCRUD.list_by_user(db, user_id, status)
    return tasks


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit("60/minute")
async def get_task(
    request: Request,  # noqa: ARG001
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get specific task by ID."""
    task = await TaskCRUD.get_by_id(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    return task


@router.put("/api/tasks/{task_id}", response_model=TaskResponse)
@limiter.limit("60/minute")
async def update_task(
    request: Request,  # noqa: ARG001
    task_id: UUID,
    task_data: TaskUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update task fields."""
    data = task_data.model_dump(exclude_unset=True)  # Only updated fields
    try:
        task = await TaskCRUD.update(db, task_id, user_id, data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_task(
    request: Request,  # noqa: ARG001
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete task."""
    task = await TaskCRUD.get_by_id(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    await TaskCRUD.delete(db, task_id, user_id)
    return None  # 204 No Content
