"""CRUD operations for OAuth 2.1 clients and authorization codes."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.oauth.models import OAuthAuthorizationCode, OAuthClient, OAuthRefreshToken


class OAuthClientCRUD:
    """OAuth client database operations."""

    @staticmethod
    async def get_by_client_id(session: AsyncSession, client_id: str) -> OAuthClient | None:
        """Find OAuth client by client_id."""
        result = await session.execute(
            select(OAuthClient).where(OAuthClient.client_id == client_id)
        )
        return result.scalars().first()

    @staticmethod
    async def create(session: AsyncSession, data: dict[str, Any]) -> OAuthClient:
        """Create new OAuth client with transaction handling."""
        try:
            client = OAuthClient(**data)
            session.add(client)
            await session.commit()
            await session.refresh(client)
            return client
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def validate_redirect_uri(
        session: AsyncSession, client_id: str, redirect_uri: str
    ) -> bool:
        """Validate that redirect_uri matches registered URIs for client."""
        client = await OAuthClientCRUD.get_by_client_id(session, client_id)

        if not client or not client.is_active:
            return False

        # Parse comma-separated redirect URIs
        registered_uris = [uri.strip() for uri in client.redirect_uris.split(",")]
        return redirect_uri in registered_uris

    @staticmethod
    async def validate_scopes(session: AsyncSession, client_id: str, requested_scopes: str) -> bool:
        """Validate that requested scopes are allowed for client."""
        client = await OAuthClientCRUD.get_by_client_id(session, client_id)

        if not client or not client.is_active:
            return False

        # Parse space-separated scopes
        requested_scope_set = set(requested_scopes.split())
        allowed_scope_set = set(client.allowed_scopes.split())

        # All requested scopes must be in allowed scopes
        return requested_scope_set.issubset(allowed_scope_set)


class OAuthAuthorizationCodeCRUD:
    """OAuth authorization code database operations."""

    @staticmethod
    async def create(
        session: AsyncSession,
        client_id: str,
        user_id: int,
        redirect_uri: str,
        scope: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> OAuthAuthorizationCode:
        """
        Create new authorization code for OAuth flow.

        Args:
            session: Database session
            client_id: OAuth client ID
            user_id: User ID who authorized
            redirect_uri: Redirect URI from authorization request
            scope: Granted scopes (space-separated)
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE challenge method (S256 or plain)

        Returns:
            Created OAuthAuthorizationCode object with secure code
        """
        try:
            # Generate cryptographically secure authorization code
            code = secrets.token_urlsafe(32)

            auth_code = OAuthAuthorizationCode(
                code=code,
                client_id=client_id,
                user_id=user_id,
                redirect_uri=redirect_uri,
                scope=scope,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                expires_at=datetime.now(UTC) + timedelta(minutes=10),
                is_used=False,
            )

            session.add(auth_code)
            await session.commit()
            await session.refresh(auth_code)
            return auth_code
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> OAuthAuthorizationCode | None:
        """Find authorization code by code value."""
        result = await session.execute(
            select(OAuthAuthorizationCode).where(OAuthAuthorizationCode.code == code)
        )
        return result.scalars().first()

    @staticmethod
    async def validate_and_use(
        session: AsyncSession,
        code: str,
        client_id: str,
        redirect_uri: str,
    ) -> OAuthAuthorizationCode | None:
        """
        Validate and mark authorization code as used.

        Args:
            session: Database session
            code: Authorization code to validate
            client_id: Client ID from token request
            redirect_uri: Redirect URI from token request

        Returns:
            OAuthAuthorizationCode if valid, None otherwise
        """
        try:
            now = datetime.now(UTC)

            # Get unused, non-expired code
            result = await session.execute(
                select(OAuthAuthorizationCode).where(
                    and_(
                        OAuthAuthorizationCode.code == code,
                        OAuthAuthorizationCode.client_id == client_id,
                        OAuthAuthorizationCode.redirect_uri == redirect_uri,
                        OAuthAuthorizationCode.is_used == False,  # noqa: E712
                        OAuthAuthorizationCode.expires_at > now,
                    )
                )
            )

            auth_code = result.scalars().first()

            if auth_code:
                # Mark code as used
                auth_code.is_used = True
                auth_code.used_at = datetime.now(UTC)
                await session.commit()
                return auth_code

            return None
        except Exception:
            await session.rollback()
            raise


class OAuthRefreshTokenCRUD:
    """OAuth refresh token database operations."""

    @staticmethod
    async def create(
        session: AsyncSession,
        client_id: str,
        user_id: int,
        scope: str,
        expires_delta: timedelta = timedelta(days=90),
    ) -> OAuthRefreshToken:
        """
        Create new refresh token for OAuth flow.

        Args:
            session: Database session
            client_id: OAuth client ID
            user_id: User ID who authorized
            scope: Granted scopes (space-separated)
            expires_delta: Token expiration duration (default: 90 days)

        Returns:
            Created OAuthRefreshToken object with secure token
        """
        try:
            # Generate cryptographically secure refresh token
            token = secrets.token_urlsafe(64)

            refresh_token = OAuthRefreshToken(
                token=token,
                client_id=client_id,
                user_id=user_id,
                scope=scope,
                is_active=True,
                expires_at=datetime.now(UTC) + expires_delta,
            )

            session.add(refresh_token)
            await session.commit()
            await session.refresh(refresh_token)
            return refresh_token
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def get_by_token(session: AsyncSession, token: str) -> OAuthRefreshToken | None:
        """Find refresh token by token value."""
        result = await session.execute(
            select(OAuthRefreshToken).where(OAuthRefreshToken.token == token)
        )
        return result.scalars().first()

    @staticmethod
    async def validate_and_get(
        session: AsyncSession, token: str, client_id: str
    ) -> OAuthRefreshToken | None:
        """
        Validate refresh token and return if valid.

        Args:
            session: Database session
            token: Refresh token to validate
            client_id: Client ID from token request

        Returns:
            OAuthRefreshToken if valid and active, None otherwise
        """
        now = datetime.now(UTC)

        result = await session.execute(
            select(OAuthRefreshToken).where(
                and_(
                    OAuthRefreshToken.token == token,
                    OAuthRefreshToken.client_id == client_id,
                    OAuthRefreshToken.is_active == True,  # noqa: E712
                    OAuthRefreshToken.expires_at > now,
                )
            )
        )

        return result.scalars().first()

    @staticmethod
    async def revoke(session: AsyncSession, token: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            session: Database session
            token: Refresh token to revoke

        Returns:
            True if token was revoked, False if not found
        """
        try:
            result = await session.execute(
                select(OAuthRefreshToken).where(OAuthRefreshToken.token == token)
            )
            refresh_token = result.scalars().first()

            if refresh_token:
                refresh_token.is_active = False
                refresh_token.revoked_at = datetime.now(UTC)
                await session.commit()
                return True

            return False
        except Exception:
            await session.rollback()
            raise
