"""SQLAlchemy database models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """User model with authentication and plan information."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    plan = Column(String(50), default="free")  # free, pro, enterprise
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    """Task model with scoring fields."""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Core fields
    title = Column(String(256), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, snoozed
    priority = Column(Integer, default=3)  # 1-5

    # Temporal fields
    due_date = Column(DateTime)
    snoozed_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Scoring fields (from GAS logic)
    effort_estimate_minutes = Column(Integer)  # For impact/effort calculations
    tags = Column(String(500))  # Comma-separated: "morning,urgent,deep-work"

    # Relationships
    user = relationship("User", back_populates="tasks")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_tasks_user_status", "user_id", "status"),
        Index("idx_tasks_user_due", "user_id", "due_date"),
        Index("idx_tasks_snoozed_until", "snoozed_until"),
    )


class UserPreferences(Base):
    """User preferences for task scoring weights."""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Scoring weights (stored as integers 0-100, sum to 100)
    weight_urgency = Column(Integer, default=40)
    weight_priority = Column(Integer, default=35)
    weight_impact = Column(Integer, default=15)
    weight_effort = Column(Integer, default=10)

    # Time preferences
    timezone = Column(String(50), default="UTC")
    work_start_time = Column(String(8), default="09:00")
    work_end_time = Column(String(8), default="17:00")

    # AI configuration
    enable_habit_learning = Column(Boolean, default=True)


class AuditLog(Base):
    """Audit log for tracking API operations (from GAS logs sheet)."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Action tracking
    action = Column(String(100), nullable=False)  # "CREATE_TASK", "GET_BEST_TASK", etc.
    resource_id = Column(UUID(as_uuid=True))  # Task ID if applicable
    result = Column(String(20), nullable=False)  # "success" or "error"
    error_message = Column(Text)
    request_duration_ms = Column(Integer)

    # Indexes for debugging
    __table_args__ = (
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_action", "action"),
    )
