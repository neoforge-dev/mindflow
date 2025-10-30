"""Authentication service for user registration and authentication."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password, verify_password
from app.db.crud import UserCRUD
from app.db.models import User


class AuthService:
    """Authentication service with user management."""

    @staticmethod
    async def register_user(
        session: AsyncSession, email: str, password: str, full_name: str | None = None
    ) -> User:
        """
        Create a new user account with hashed password.

        Args:
            session: Database session
            email: User email address
            password: Plain text password (will be hashed)
            full_name: Optional user's full name

        Returns:
            Created User object

        Raises:
            ValueError: If email already exists
        """
        # Check if email already registered
        existing_user = await UserCRUD.get_by_email(session, email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "plan": "free",  # Default plan
            "is_active": True,
        }

        user = await UserCRUD.create(session, user_data)
        return user

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
        """
        Authenticate user credentials.

        Args:
            session: Database session
            email: User email address
            password: Plain text password to verify

        Returns:
            User object if authentication successful, None otherwise

        Note:
            Returns None for both "email not found" and "wrong password"
            to prevent user enumeration attacks.
        """
        # Find user by email
        user = await UserCRUD.get_by_email(session, email)
        if not user:
            # Email not found - return None (security: same response as wrong password)
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            # Wrong password - return None
            return None

        # Authentication successful
        return user
