"""Pydantic schemas for task validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    """Base task schema with common fields."""

    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = Field(None, max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: datetime | None = None
    tags: str | None = Field(None, max_length=500)
    effort_estimate_minutes: int | None = Field(None, ge=1, le=480)  # Max 8 hours


class TaskCreate(TaskBase):
    """Schema for creating tasks with validation."""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate title is not just whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class TaskUpdate(BaseModel):
    """Schema for updating tasks - all fields optional."""

    status: str | None = None
    priority: int | None = Field(None, ge=1, le=5)
    due_date: datetime | None = None
    snoozed_until: datetime | None = None
    effort_estimate_minutes: int | None = Field(None, ge=1, le=480)
    tags: str | None = Field(None, max_length=500)


class TaskResponse(TaskBase):
    """Response schema with all fields including generated ones."""

    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    snoozed_until: datetime | None = None

    class Config:
        from_attributes = True
