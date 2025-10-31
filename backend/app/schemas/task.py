"""Pydantic schemas for task validation."""

import html
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    """Base task schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: datetime | None = None
    tags: str | None = Field(None, max_length=500)
    effort_estimate_minutes: int | None = Field(None, ge=1, le=480)  # Max 8 hours


class TaskCreate(TaskBase):
    """Schema for creating tasks with validation."""

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Sanitize title: escape HTML and validate not just whitespace.

        Args:
            v: Raw title input

        Returns:
            Sanitized title with HTML escaped

        Raises:
            ValueError: If title is empty after stripping
        """
        if not v.strip():
            raise ValueError("Title cannot be empty")
        # Escape HTML to prevent XSS
        return html.escape(v.strip())

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        """Sanitize description: escape HTML if present.

        Args:
            v: Raw description input or None

        Returns:
            Sanitized description with HTML escaped, or None
        """
        if v is None:
            return None
        # Escape HTML to prevent XSS
        return html.escape(v)


class TaskUpdate(BaseModel):
    """Schema for updating tasks - all fields optional."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    status: str | None = None
    priority: int | None = Field(None, ge=1, le=5)
    due_date: datetime | None = None
    snoozed_until: datetime | None = None
    effort_estimate_minutes: int | None = Field(None, ge=1, le=480)
    tags: str | None = Field(None, max_length=500)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str | None) -> str | None:
        """Sanitize title: escape HTML if present.

        Args:
            v: Raw title input or None

        Returns:
            Sanitized title with HTML escaped, or None
        """
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return html.escape(v.strip())

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        """Sanitize description: escape HTML if present.

        Args:
            v: Raw description input or None

        Returns:
            Sanitized description with HTML escaped, or None
        """
        if v is None:
            return None
        return html.escape(v)


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
