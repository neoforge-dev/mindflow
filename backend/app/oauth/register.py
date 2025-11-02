"""OAuth 2.1 Client Registration Endpoint (RFC 7591)."""

import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.oauth.models import OAuthClient
from app.oauth.schemas import OAuthClientRegistrationRequest, OAuthClientRegistrationResponse

router = APIRouter()


def generate_client_id() -> str:
    """Generate secure random client ID.

    Returns:
        32-character hex string (128-bit security)
    """
    return secrets.token_hex(16)


def generate_client_secret() -> str:
    """Generate secure random client secret.

    Returns:
        64-character hex string (256-bit security)
    """
    return secrets.token_hex(32)


@router.post(
    "/oauth/register",
    response_model=OAuthClientRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_oauth_client(
    registration: OAuthClientRegistrationRequest, db: AsyncSession = Depends(get_db)
) -> OAuthClientRegistrationResponse:
    """Register new OAuth 2.1 client application.

    Implements Dynamic Client Registration Protocol (RFC 7591).
    Allows third-party applications like ChatGPT to register as OAuth clients.

    Args:
        registration: Client registration request with metadata
        db: Database session

    Returns:
        Client credentials and registration metadata

    Raises:
        HTTPException: If registration data is invalid

    Security:
        - Client ID: 128-bit cryptographically secure random
        - Client Secret: 256-bit cryptographically secure random
        - Redirect URIs validated as HTTPS in production
        - Scopes validated against allowed scopes
    """
    # Validate grant types
    allowed_grant_types = ["authorization_code", "refresh_token"]
    invalid_grants = [gt for gt in registration.grant_types if gt not in allowed_grant_types]
    if invalid_grants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid grant types: {', '.join(invalid_grants)}. Allowed: {', '.join(allowed_grant_types)}",
        )

    # Validate response types
    allowed_response_types = ["code"]
    invalid_responses = [
        rt for rt in registration.response_types if rt not in allowed_response_types
    ]
    if invalid_responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid response types: {', '.join(invalid_responses)}. Allowed: {', '.join(allowed_response_types)}",
        )

    # Validate scopes
    allowed_scopes = {"tasks:read", "tasks:write", "openid", "profile", "email"}
    requested_scopes = set(registration.scope.split())
    invalid_scopes = requested_scopes - allowed_scopes
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {', '.join(invalid_scopes)}. Allowed: {', '.join(allowed_scopes)}",
        )

    # Generate client credentials
    client_id = generate_client_id()
    client_secret = generate_client_secret()

    # Create OAuth client
    oauth_client = OAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        client_name=registration.client_name,
        redirect_uris=",".join(str(uri) for uri in registration.redirect_uris),
        allowed_scopes=" ".join(requested_scopes),
        grant_types=",".join(registration.grant_types),
        response_types=",".join(registration.response_types),
        logo_uri=str(registration.logo_uri) if registration.logo_uri else None,
        policy_uri=str(registration.policy_uri) if registration.policy_uri else None,
        tos_uri=str(registration.tos_uri) if registration.tos_uri else None,
        is_active=True,
    )

    db.add(oauth_client)
    await db.commit()
    await db.refresh(oauth_client)

    # Return registration response per RFC 7591
    return OAuthClientRegistrationResponse(
        client_id=client_id,
        client_secret=client_secret,
        client_name=registration.client_name,
        redirect_uris=[str(uri) for uri in registration.redirect_uris],
        grant_types=registration.grant_types,
        response_types=registration.response_types,
        scope=registration.scope,
        logo_uri=str(registration.logo_uri) if registration.logo_uri else None,
        policy_uri=str(registration.policy_uri) if registration.policy_uri else None,
        tos_uri=str(registration.tos_uri) if registration.tos_uri else None,
        client_id_issued_at=int(time.time()),
    )
