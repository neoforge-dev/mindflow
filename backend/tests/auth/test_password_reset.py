"""Tests for password reset functionality."""

import uuid
from datetime import datetime, timedelta

import pytest

from app.auth.security import hash_password, verify_password
from app.db.crud import PasswordResetTokenCRUD, UserCRUD
from app.services.email_service import MockEmailService, get_email_service


@pytest.mark.asyncio
class TestPasswordResetFlow:
    """Test password reset end-to-end flow."""

    async def test_forgot_password_sends_email_for_existing_user(
        self, test_client, test_user_with_password, monkeypatch
    ):
        """Test forgot password sends email for valid user."""
        # Use mock email service
        mock_service = MockEmailService()
        monkeypatch.setattr("app.api.auth.get_email_service", lambda: mock_service)

        response = await test_client.post(
            "/api/auth/forgot-password",
            json={"email": test_user_with_password.email},
        )

        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]

        # Verify email was sent
        assert len(mock_service.sent_emails) == 1
        sent_email = mock_service.sent_emails[0]
        assert sent_email["to"] == test_user_with_password.email
        assert "token" in sent_email
        assert len(sent_email["token"]) >= 32

    async def test_forgot_password_generic_response_for_nonexistent_user(
        self, test_client, monkeypatch
    ):
        """Test forgot password returns generic response for unknown email (prevent enumeration)."""
        mock_service = MockEmailService()
        monkeypatch.setattr("app.api.auth.get_email_service", lambda: mock_service)

        response = await test_client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]

        # Verify NO email was sent
        assert len(mock_service.sent_emails) == 0

    async def test_reset_password_with_valid_token_succeeds(
        self, test_client, db_engine, test_user_with_password, monkeypatch
    ):
        """Test password reset with valid token updates password."""
        # Generate and store reset token using engine (not fixture session)
        import secrets

        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker

        reset_token = secrets.token_urlsafe(32)

        # Create token in separate session
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            await PasswordResetTokenCRUD.create(
                session=session, user_id=test_user_with_password.id, token=reset_token
            )

        # Reset password
        new_password = "NewSecurePassword123"
        response = await test_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": new_password},
        )

        assert response.status_code == 200
        assert "successful" in response.json()["message"]

        # Verify password was updated in separate session
        async with async_session() as session:
            user = await UserCRUD.get_by_id(session, test_user_with_password.id)
            assert user is not None
            assert verify_password(new_password, user.password_hash)

            # Verify old password no longer works
            assert not verify_password("testPassword123", user.password_hash)

    async def test_reset_password_with_expired_token_fails(
        self, test_client, db_session, test_user_with_password
    ):
        """Test password reset fails with expired token."""
        import secrets

        from app.db.models import PasswordResetToken

        # Create expired token manually
        reset_token_str = secrets.token_urlsafe(32)
        expired_token = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=test_user_with_password.id,
            token_hash=hash_password(reset_token_str),
            expires_at=datetime.utcnow() - timedelta(hours=2),  # Expired 2 hours ago
            created_at=datetime.utcnow() - timedelta(hours=3),
        )
        db_session.add(expired_token)
        await db_session.commit()

        # Try to reset password
        response = await test_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token_str, "new_password": "NewPassword123"},
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    async def test_reset_password_with_used_token_fails(
        self, test_client, db_session, test_user_with_password
    ):
        """Test password reset fails with already used token."""
        import secrets

        # Generate and use token
        reset_token = secrets.token_urlsafe(32)
        await PasswordResetTokenCRUD.create(
            session=db_session, user_id=test_user_with_password.id, token=reset_token
        )

        # Use token once (successfully)
        response1 = await test_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "FirstPassword123"},
        )
        assert response1.status_code == 200

        # Try to use same token again
        response2 = await test_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "SecondPassword123"},
        )

        assert response2.status_code == 400
        assert "Invalid or expired" in response2.json()["detail"]

    async def test_reset_password_with_invalid_token_fails(self, test_client):
        """Test password reset fails with invalid token."""
        # Use a token that meets length requirements
        import secrets

        invalid_token = secrets.token_urlsafe(32)  # Valid format but doesn't exist in DB

        response = await test_client.post(
            "/api/auth/reset-password",
            json={"token": invalid_token, "new_password": "NewPassword123"},
        )

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    @pytest.mark.skip(reason="Rate limiting requires Redis/proper setup in tests")
    async def test_forgot_password_rate_limiting(self, test_client, test_user_with_password):
        """Test forgot password endpoint has rate limiting (3 req/hour)."""
        # Make 3 requests (should succeed)
        for _ in range(3):
            response = await test_client.post(
                "/api/auth/forgot-password",
                json={"email": test_user_with_password.email},
            )
            assert response.status_code == 200

        # 4th request should be rate limited
        response = await test_client.post(
            "/api/auth/forgot-password",
            json={"email": test_user_with_password.email},
        )
        assert response.status_code == 429  # Too Many Requests

    async def test_reset_password_with_short_password_fails(
        self, test_client, db_session, test_user_with_password
    ):
        """Test password reset fails validation with password < 12 chars."""
        import secrets

        reset_token = secrets.token_urlsafe(32)
        await PasswordResetTokenCRUD.create(
            session=db_session, user_id=test_user_with_password.id, token=reset_token
        )

        # Try with short password
        response = await test_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "short"},
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestPasswordResetTokenCRUD:
    """Test PasswordResetToken CRUD operations."""

    async def test_create_token_hashes_and_stores(self, db_session, test_user):
        """Test token creation hashes token before storage."""
        import secrets

        plain_token = secrets.token_urlsafe(32)

        reset_token = await PasswordResetTokenCRUD.create(
            session=db_session, user_id=test_user.id, token=plain_token
        )

        assert reset_token.id is not None
        assert reset_token.user_id == test_user.id
        assert reset_token.token_hash != plain_token  # Should be hashed
        assert len(reset_token.token_hash) > 50  # Bcrypt hash is long
        assert reset_token.expires_at > datetime.utcnow()
        assert reset_token.used_at is None

    async def test_validate_and_use_marks_token_as_used(self, db_session, test_user):
        """Test token validation marks token as used."""
        import secrets

        plain_token = secrets.token_urlsafe(32)

        reset_token = await PasswordResetTokenCRUD.create(
            session=db_session, user_id=test_user.id, token=plain_token
        )

        # Validate token
        user_id = await PasswordResetTokenCRUD.validate_and_use(db_session, plain_token)

        assert user_id == test_user.id

        # Verify token is marked as used
        await db_session.refresh(reset_token)
        assert reset_token.used_at is not None

    async def test_validate_rejects_wrong_token(self, db_session, test_user):
        """Test token validation rejects incorrect token."""
        import secrets

        # Create valid token
        correct_token = secrets.token_urlsafe(32)
        await PasswordResetTokenCRUD.create(
            session=db_session, user_id=test_user.id, token=correct_token
        )

        # Try with wrong token
        wrong_token = secrets.token_urlsafe(32)
        user_id = await PasswordResetTokenCRUD.validate_and_use(db_session, wrong_token)

        assert user_id is None
