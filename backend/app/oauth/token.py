"""OAuth 2.1 Token Endpoint (/oauth/token).

Implements RFC 6749 Section 3.2 (Token Endpoint) with OAuth 2.1 enhancements:
- Authorization code exchange with PKCE (RFC 7636)
- Refresh token grant
- Client authentication
"""

import base64
import hashlib
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.oauth.crud import OAuthAuthorizationCodeCRUD, OAuthClientCRUD, OAuthRefreshTokenCRUD
from app.oauth.jwt import create_access_token
from app.oauth.schemas import TokenErrorResponse, TokenResponse

router = APIRouter()


def verify_pkce(code_verifier: str, code_challenge: str, code_challenge_method: str) -> bool:
    """Verify PKCE code_verifier against stored code_challenge.

    Args:
        code_verifier: Code verifier from token request
        code_challenge: Code challenge from authorization request
        code_challenge_method: Challenge method (S256 or plain)

    Returns:
        True if verification succeeds, False otherwise

    Spec: RFC 7636 Section 4.6
    """
    if code_challenge_method == "S256":
        # SHA256 hash and base64url encode (without padding)
        verifier_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed_challenge = base64.urlsafe_b64encode(verifier_hash).decode("ascii").rstrip("=")
        return computed_challenge == code_challenge
    elif code_challenge_method == "plain":
        # Plain text comparison
        return code_verifier == code_challenge
    else:
        # Unknown method
        return False


async def authenticate_client(
    session: AsyncSession, client_id: str, client_secret: str
) -> bool:
    """Authenticate OAuth client using client_id and client_secret.

    Args:
        session: Database session
        client_id: Client ID
        client_secret: Client secret

    Returns:
        True if authentication succeeds, False otherwise
    """
    client = await OAuthClientCRUD.get_by_client_id(session, client_id)

    if not client or not client.is_active:
        return False

    # Constant-time comparison to prevent timing attacks
    import secrets

    return secrets.compare_digest(client.client_secret, client_secret)


@router.post("/oauth/token", response_model=TokenResponse, responses={400: {"model": TokenErrorResponse}, 401: {"model": TokenErrorResponse}})
async def token_endpoint(
    grant_type: str = Form(...),
    code: str | None = Form(None),
    redirect_uri: str | None = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code_verifier: str | None = Form(None),
    refresh_token: str | None = Form(None),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth 2.1 Token Endpoint.

    Supports two grant types:
    1. authorization_code: Exchange authorization code for tokens
    2. refresh_token: Exchange refresh token for new access token

    Args:
        grant_type: Grant type (authorization_code or refresh_token)
        code: Authorization code (required for authorization_code grant)
        redirect_uri: Redirect URI (required for authorization_code grant)
        client_id: OAuth client ID
        client_secret: OAuth client secret
        code_verifier: PKCE code verifier (required for authorization_code grant)
        refresh_token: Refresh token (required for refresh_token grant)
        session: Database session

    Returns:
        TokenResponse with access_token and optional refresh_token

    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 401: Client authentication failed

    Spec:
        RFC 6749 Section 3.2 (Token Endpoint)
        RFC 7636 Section 4.5 (PKCE Verification)
    """
    # Authenticate client
    if not await authenticate_client(session, client_id, client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client authentication failed",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Handle authorization_code grant
    if grant_type == "authorization_code":
        return await handle_authorization_code_grant(
            session, code, redirect_uri, client_id, code_verifier
        )

    # Handle refresh_token grant
    elif grant_type == "refresh_token":
        return await handle_refresh_token_grant(session, refresh_token, client_id)

    # Unsupported grant type
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant type: {grant_type}",
        )


async def handle_authorization_code_grant(
    session: AsyncSession,
    code: str | None,
    redirect_uri: str | None,
    client_id: str,
    code_verifier: str | None,
) -> TokenResponse:
    """Handle authorization_code grant type.

    Args:
        session: Database session
        code: Authorization code
        redirect_uri: Redirect URI
        client_id: Client ID
        code_verifier: PKCE code verifier

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If validation fails
    """
    # Validate required parameters
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: code",
        )

    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: redirect_uri",
        )

    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: code_verifier (PKCE required)",
        )

    # Validate and mark authorization code as used
    auth_code = await OAuthAuthorizationCodeCRUD.validate_and_use(
        session, code, client_id, redirect_uri
    )

    if not auth_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code or code expired/used",
        )

    # Verify PKCE code_verifier
    if not auth_code.code_challenge or not auth_code.code_challenge_method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code missing PKCE challenge",
        )

    if not verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PKCE verification failed: invalid code_verifier",
        )

    # Generate JWT access token
    access_token = create_access_token(
        user_id=auth_code.user_id,
        client_id=client_id,
        scope=auth_code.scope,
        expires_delta=timedelta(hours=1),
    )

    # Generate refresh token
    refresh_token_obj = await OAuthRefreshTokenCRUD.create(
        session,
        client_id=client_id,
        user_id=auth_code.user_id,
        scope=auth_code.scope,
        expires_delta=timedelta(days=90),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600,  # 1 hour in seconds
        refresh_token=refresh_token_obj.token,
        scope=auth_code.scope,
    )


async def handle_refresh_token_grant(
    session: AsyncSession,
    refresh_token: str | None,
    client_id: str,
) -> TokenResponse:
    """Handle refresh_token grant type.

    Args:
        session: Database session
        refresh_token: Refresh token
        client_id: Client ID

    Returns:
        TokenResponse with new access token (same refresh token)

    Raises:
        HTTPException: If validation fails
    """
    # Validate required parameter
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: refresh_token",
        )

    # Validate refresh token
    refresh_token_obj = await OAuthRefreshTokenCRUD.validate_and_get(
        session, refresh_token, client_id
    )

    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token or token expired/revoked",
        )

    # Generate new JWT access token
    access_token = create_access_token(
        user_id=refresh_token_obj.user_id,
        client_id=client_id,
        scope=refresh_token_obj.scope,
        expires_delta=timedelta(hours=1),
    )

    # Don't rotate refresh token (OAuth 2.1 recommendation for public clients)
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=3600,  # 1 hour in seconds
        refresh_token=refresh_token,  # Return same refresh token
        scope=refresh_token_obj.scope,
    )
