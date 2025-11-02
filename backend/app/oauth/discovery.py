"""OAuth 2.1 Authorization Server Metadata (RFC 8414).

Provides discovery endpoint for ChatGPT to find OAuth endpoints.
"""

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery() -> dict[str, str | list[str]]:
    """OAuth 2.1 AS metadata discovery endpoint.

    Returns:
        OAuth server metadata including all required endpoints
        for ChatGPT Apps SDK integration.

    Spec: RFC 8414 - OAuth 2.0 Authorization Server Metadata
    """
    base_url = settings.api_base_url.rstrip("/")

    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "registration_endpoint": f"{base_url}/oauth/register",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "scopes_supported": ["tasks:read", "tasks:write", "openid", "profile", "email"],
        "code_challenge_methods_supported": ["S256"],  # PKCE support
    }
