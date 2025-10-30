"""Integration tests for AuthService."""

import pytest

from app.auth.security import verify_password
from app.auth.service import AuthService
from app.db.crud import UserCRUD


class TestAuthService:
    """Test authentication service functions."""

    @pytest.mark.asyncio
    async def test_register_user_creates_user_with_hashed_password(self, db_session):
        """Registration creates user, password hashed, verifies correctly."""
        email = "newuser@example.com"
        password = "securePassword123"
        full_name = "New User"

        # Register user
        user = await AuthService.register_user(
            session=db_session, email=email, password=password, full_name=full_name
        )

        # User created with correct data
        assert user.email == email
        assert user.full_name == full_name
        assert user.id is not None

        # Password is hashed (not plaintext)
        assert user.password_hash != password
        assert user.password_hash.startswith("$2b$")  # bcrypt hash format

        # Password verifies correctly
        assert verify_password(password, user.password_hash) is True

    @pytest.mark.asyncio
    async def test_register_user_raises_on_duplicate_email(self, db_session):
        """Registering same email twice raises ValueError."""
        email = "duplicate@example.com"
        password = "password123456"

        # First registration succeeds
        await AuthService.register_user(session=db_session, email=email, password=password)

        # Second registration with same email should fail
        with pytest.raises(ValueError, match="Email already registered"):
            await AuthService.register_user(session=db_session, email=email, password=password)

    @pytest.mark.asyncio
    async def test_authenticate_user_returns_user_on_correct_credentials(self, db_session):
        """Valid email/password returns User object."""
        email = "auth@example.com"
        password = "correctPassword123"

        # Create user
        await AuthService.register_user(session=db_session, email=email, password=password)

        # Authenticate with correct credentials
        user = await AuthService.authenticate_user(
            session=db_session, email=email, password=password
        )

        # Returns user object
        assert user is not None
        assert user.email == email

    @pytest.mark.asyncio
    async def test_authenticate_user_returns_none_on_wrong_password(self, db_session):
        """Valid email but wrong password returns None."""
        email = "wrongpass@example.com"
        correct_password = "correctPassword123"
        wrong_password = "wrongPassword456"

        # Create user
        await AuthService.register_user(session=db_session, email=email, password=correct_password)

        # Authenticate with wrong password
        user = await AuthService.authenticate_user(
            session=db_session, email=email, password=wrong_password
        )

        # Returns None (security: don't reveal which field is wrong)
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_returns_none_on_nonexistent_email(self, db_session):
        """Email not in database returns None without raising."""
        email = "nonexistent@example.com"
        password = "somePassword123"

        # Authenticate with non-existent email
        user = await AuthService.authenticate_user(
            session=db_session, email=email, password=password
        )

        # Returns None (security: same response as wrong password)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_user_if_exists(self, db_session):
        """Existing email returns User object."""
        email = "existing@example.com"
        password = "password123456"

        # Create user
        created_user = await AuthService.register_user(
            session=db_session, email=email, password=password
        )

        # Retrieve by email
        found_user = await UserCRUD.get_by_email(session=db_session, email=email)

        # Returns correct user
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == email

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_none_if_not_exists(self, db_session):
        """Non-existent email returns None."""
        email = "notfound@example.com"

        # Try to find non-existent user
        user = await UserCRUD.get_by_email(session=db_session, email=email)

        # Returns None
        assert user is None
