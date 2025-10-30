"""Pydantic schemas for task validation."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid


class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[datetime] = None
    tags: Optional[str] = Field(None, max_length=500)
    effort_estimate_minutes: Optional[int] = Field(None, ge=1, le=480)  # Max 8 hours


class TaskCreate(TaskBase):
    """Schema for creating tasks with validation."""
    
    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate title is not just whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class TaskUpdate(BaseModel):
    """Schema for updating tasks - all fields optional."""
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    effort_estimate_minutes: Optional[int] = Field(None, ge=1, le=480)
    tags: Optional[str] = Field(None, max_length=500)


class TaskResponse(TaskBase):
    """Response schema with all fields including generated ones."""
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None

    class Config:
        from_attributes = True
