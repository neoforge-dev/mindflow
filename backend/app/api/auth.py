"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import Token, UserLogin, UserRegister, UserResponse
from app.auth.security import create_access_token
from app.auth.service import AuthService
from app.db.models import User
from app.dependencies import get_current_user, get_db
from app.middleware.rate_limit import limiter

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


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,  # noqa: ARG001
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login with email and password.

    Authenticates user credentials and returns JWT access token.

    Returns:
        Token: JWT access token and token type

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

    # Create JWT token with user_id in 'sub' claim
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, token_type="bearer")


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
