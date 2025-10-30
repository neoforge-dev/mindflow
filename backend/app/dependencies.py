"""FastAPI dependency injection for database sessions and user context."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.db.crud import UserCRUD
from app.db.database import AsyncSessionLocal
from app.db.models import User

# OAuth2 scheme for JWT token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.

    Yields database session for request scope, automatically commits
    if no exception and closes session after request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """
    Extract and validate user_id from JWT token.

    Args:
        token: JWT token from Authorization header

    Returns:
        User ID extracted from token 'sub' claim

    Raises:
        HTTPException 401: If token is invalid, expired, or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = decode_access_token(token)

        # Extract user_id from 'sub' claim
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Convert to UUID
        user_id = UUID(user_id_str)
        return user_id

    except (JWTError, ValueError) as e:
        # Invalid token, expired token, or invalid UUID format
        raise credentials_exception from e


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT and retrieve full User object from database.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User object for authenticated user

    Raises:
        HTTPException 401: If token is invalid OR if user not found
            (security: never reveal whether user exists from a valid JWT)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = decode_access_token(token)

        # Extract user_id from 'sub' claim
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Convert to UUID
        user_id = UUID(user_id_str)

        # Fetch user from database
        user = await UserCRUD.get_by_id(db, user_id)

        if user is None:
            # User not found (possibly deleted) - return 401, not 404
            # Security: never reveal user existence from valid JWT
            raise credentials_exception

        return user

    except (JWTError, ValueError) as e:
        # Invalid token, expired token, or invalid UUID format
        raise credentials_exception from e
