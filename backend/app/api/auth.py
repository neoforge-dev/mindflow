"""Authentication API endpoints."""

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
    TokensResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.auth.security import create_access_token, hash_password
from app.auth.service import AuthService
from app.db.crud import PasswordResetTokenCRUD, RefreshTokenCRUD, UserCRUD
from app.db.models import User
from app.dependencies import get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.services.email_service import get_email_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,  # noqa: ARG001
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.

    Creates a new user with hashed password. Email must be unique.

    Returns:
        UserResponse: Created user data (no password)

    Raises:
        HTTPException 400: Email already registered
        HTTPException 422: Invalid email format or password too short
    """
    try:
        user = await AuthService.register_user(
            session=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        return UserResponse.model_validate(user)
    except ValueError as e:
        # Email already exists
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/login", response_model=TokensResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(None),
) -> TokensResponse:
    """
    Login with email and password.

    Authenticates user credentials and returns JWT access token + refresh token.

    Returns:
        TokensResponse: Access token (24h) and refresh token (30 days)

    Raises:
        HTTPException 401: Invalid credentials (email not found or wrong password)
    """
    user = await AuthService.authenticate_user(
        session=db, email=credentials.email, password=credentials.password
    )

    if not user:
        # Invalid credentials (generic message for security)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT access token with user_id in 'sub' claim
    access_token = create_access_token(data={"sub": str(user.id)})

    # Generate refresh token (secure random string)
    refresh_token_str = secrets.token_urlsafe(32)

    # Store refresh token in database
    await RefreshTokenCRUD.create(
        session=db,
        user_id=user.id,
        token=refresh_token_str,
        user_agent=user_agent,
        ip_address=request.client.host if request.client else None,
    )

    return TokensResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid JWT in Authorization header.

    Returns:
        UserResponse: Current user data (no password)

    Raises:
        HTTPException 401: Not authenticated or invalid token
    """
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,  # noqa: ARG001
    forgot_request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Initiate password reset flow.

    Sends password reset email if account exists. Always returns success
    to prevent email enumeration attacks.

    Rate limit: 3 requests per hour per IP address.

    Returns:
        Generic success message

    Raises:
        HTTPException 429: Rate limit exceeded
    """
    # Look up user by email
    user = await UserCRUD.get_by_email(db, forgot_request.email)

    if user:
        # Generate secure random token
        reset_token = secrets.token_urlsafe(32)

        # Store hashed token in database
        await PasswordResetTokenCRUD.create(session=db, user_id=user.id, token=reset_token)

        # Send reset email
        email_service = get_email_service()
        await email_service.send_password_reset_email(
            to_email=user.email, reset_token=reset_token, user_name=user.full_name
        )

    # Always return success message (prevent email enumeration)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Reset password with token from email.

    Validates token and updates user password if valid.

    Returns:
        Success message

    Raises:
        HTTPException 400: Invalid or expired token
    """
    # Validate token and get user_id
    user_id = await PasswordResetTokenCRUD.validate_and_use(db, reset_request.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    # Hash new password
    new_password_hash = hash_password(reset_request.new_password)

    # Update user's password
    user = await UserCRUD.update(db, user_id, {"password_hash": new_password_hash})

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    return {"message": "Password reset successful"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Refresh access token using refresh token.

    Validates refresh token and issues new access token.

    Returns:
        Token: New JWT access token (24 hours)

    Raises:
        HTTPException 401: Invalid or expired refresh token
    """
    # Validate refresh token and get user_id
    user_id = await RefreshTokenCRUD.validate(db, refresh_request.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new access token
    access_token = create_access_token(data={"sub": str(user_id)})

    return Token(access_token=access_token, token_type="bearer")


@router.post("/revoke")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """
    Revoke all refresh tokens for current user.

    Requires valid JWT in Authorization header.
    Useful for logout from all devices or security breach response.

    Returns:
        Success message with count of revoked tokens

    Raises:
        HTTPException 401: Not authenticated or invalid token
    """
    # Revoke all active refresh tokens
    count = await RefreshTokenCRUD.revoke_all_for_user(db, current_user.id)

    return {"message": "All sessions revoked successfully", "count": count}
