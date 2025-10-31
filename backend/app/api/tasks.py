"""Task API endpoints - route order is critical!"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import TaskCRUD
from app.dependencies import get_current_user_id, get_db
from app.middleware.rate_limit import limiter
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.scoring import (
    calculate_deadline_urgency,
    calculate_effort_bonus,
    calculate_task_score,
)

router = APIRouter()

# ⚠️ ROUTE ORDER CRITICAL: Define specific routes (/pending, /best) BEFORE /{id}
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


@router.get("/api/tasks/best")
@limiter.limit("60/minute")
async def get_best_task(
    request: Request,  # noqa: ARG001
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the best task to work on right now.

    Scores tasks based on:
    - Deadline urgency (overdue > due today > due tomorrow)
    - User priority (1-5 scale)
    - Effort estimate (quick wins boosted)
    - Time of day preferences

    Returns:
        dict: {
            task: TaskResponse,
            score: float,
            reasoning: {
                deadline_urgency: float,
                priority_score: int,
                effort_bonus: int,
                total_score: float,
                recommendation: str
            }
        }

    Raises:
        404: No pending tasks available
    """
    # Get pending/in-progress tasks (excludes completed and snoozed)
    tasks = await TaskCRUD.get_pending_tasks(db, user_id)

    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending tasks",
        )

    # Score all tasks
    scored_tasks = []
    for task in tasks:
        score = calculate_task_score(task)
        scored_tasks.append((task, score))

    # Sort by score (highest first)
    scored_tasks.sort(key=lambda x: x[1], reverse=True)
    best_task, best_score = scored_tasks[0]

    # Generate reasoning components
    urgency = calculate_deadline_urgency(best_task.due_date)
    effort = calculate_effort_bonus(best_task.effort_estimate_minutes)

    # Build response with transparent reasoning
    return {
        "task": TaskResponse.model_validate(best_task),
        "score": best_score,
        "reasoning": {
            "deadline_urgency": urgency,
            "priority_score": best_task.priority * 10,
            "effort_bonus": effort * 10,
            "total_score": best_score,
            "recommendation": _generate_recommendation(best_task),
        },
    }


def _generate_recommendation(task) -> str:
    """Generate human-readable recommendation for task.

    Args:
        task: Task model instance

    Returns:
        Recommendation string based on task properties
    """
    # Check overdue
    if task.due_date:
        hours_until = (task.due_date - datetime.utcnow()).total_seconds() / 3600
        if hours_until < 0:
            return "This task is overdue - tackle it now!"
        if hours_until < 24:
            return "Due today - good time to work on this"

    # Check quick win
    if task.effort_estimate_minutes and task.effort_estimate_minutes <= 15:
        return "Quick win - knock this out fast!"

    # Default high priority
    return "High priority task worth focusing on"


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
