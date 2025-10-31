"""Pydantic schemas for authentication requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode for SQLAlchemy models


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset flow."""

    email: EmailStr = Field(..., description="Email address of account to reset")


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token."""

    token: str = Field(..., min_length=32, description="Password reset token from email")
    new_password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="New password (12-128 characters, NIST 2024 standard)",
    )


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str = Field(..., description="Refresh token from login")


class TokensResponse(BaseModel):
    """Response with both access and refresh tokens."""

    access_token: str = Field(..., description="JWT access token (24 hours)")
    refresh_token: str = Field(..., description="Refresh token (30 days)")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
