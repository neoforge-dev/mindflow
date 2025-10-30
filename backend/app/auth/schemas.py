"""Pydantic schemas for authentication requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Password (12-128 characters, NIST 2024 standard)",
    )
    full_name: str | None = Field(None, max_length=255, description="User's full name")


class UserLogin(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class TokenData(BaseModel):
    """Decoded JWT token data."""

    user_id: UUID | None = Field(None, description="User ID from token 'sub' claim")


class UserResponse(BaseModel):
    """User data response (no password)."""

    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    full_name: str | None = Field(None, description="User's full name")
    plan: str = Field(..., description="User plan (free, pro, enterprise)")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
