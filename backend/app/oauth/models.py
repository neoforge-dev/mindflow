"""OAuth 2.1 database models for client registration and authorization codes."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class OAuthClient(Base):
    """OAuth 2.1 client application registration.

    Represents a registered third-party application (e.g., ChatGPT)
    that can request user authorization.
    """

    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), unique=True, index=True, nullable=False)
    client_secret = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)

    # Redirect URIs (comma-separated for multiple URIs)
    redirect_uris = Column(Text, nullable=False)

    # Scopes this client is allowed to request
    allowed_scopes = Column(Text, nullable=False)

    # OAuth 2.1 metadata
    grant_types = Column(Text, nullable=False, default="authorization_code,refresh_token")
    response_types = Column(Text, nullable=False, default="code")
    token_endpoint_auth_method = Column(String(50), nullable=False, default="client_secret_post")

    # Client metadata
    logo_uri = Column(String(500), nullable=True)
    policy_uri = Column(String(500), nullable=True)
    tos_uri = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class OAuthAuthorizationCode(Base):
    """OAuth 2.1 authorization code for code exchange flow.

    Temporary code issued after user authorization, exchanged for
    access token. Implements PKCE for security.
    """

    __tablename__ = "oauth_authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, index=True, nullable=False)

    # Associated client and user
    client_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Redirect URI used in authorization request (must match token request)
    redirect_uri = Column(String(500), nullable=False)

    # Granted scopes
    scope = Column(Text, nullable=False)

    # PKCE (Proof Key for Code Exchange) - RFC 7636
    code_challenge = Column(String(255), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)  # S256 or plain

    # Expiration and usage tracking
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OAuthRefreshToken(Base):
    """OAuth 2.1 refresh token for obtaining new access tokens.

    Long-lived token that can be exchanged for new access tokens
    without requiring user re-authentication.
    """

    __tablename__ = "oauth_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)

    # Associated client and user
    client_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Granted scopes
    scope = Column(Text, nullable=False)

    # Status and expiration
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
