"""OAuth token verification for MCP server.

This module provides JWT access token verification for the MCP server,
ensuring that all requests from ChatGPT Apps SDK are properly authenticated.
"""

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from mcp_server.config import config


class TokenVerificationError(Exception):
    """Raised when token verification fails."""

    pass


def verify_bearer_token(authorization_header: str) -> dict:
    """Verify JWT access token from Authorization header.

    Args:
        authorization_header: Authorization header value (with or without 'Bearer ' prefix)

    Returns:
        Decoded token payload with user_id, scopes, etc.

    Raises:
        TokenVerificationError: If token is invalid, expired, or signature fails

    Example:
        >>> payload = verify_bearer_token("Bearer eyJhbGc...")
        >>> user_id = int(payload["sub"])
        >>> scopes = payload["scope"].split()
    """
    # Extract token from header
    if not authorization_header:
        raise TokenVerificationError("Missing authorization token")

    token = authorization_header
    if authorization_header.startswith("Bearer "):
        token = authorization_header[7:]  # Remove "Bearer " prefix

    if not token:
        raise TokenVerificationError("Empty authorization token")

    # Load public key
    try:
        public_key_pem = config.get_public_key()
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
    except FileNotFoundError as e:
        raise TokenVerificationError(f"Public key not found: {e}") from e
    except Exception as e:
        raise TokenVerificationError(f"Failed to load public key: {e}") from e

    # Verify and decode token
    try:
        payload = jwt.decode(
            token,
            public_key,  # type: ignore[arg-type]
            algorithms=["RS256"],
            audience=config.jwt_audience,
            issuer=config.oauth_issuer,
            options={
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_signature": True,
            },
        )
        return payload

    except jwt.ExpiredSignatureError as e:
        raise TokenVerificationError("Token has expired") from e
    except jwt.InvalidSignatureError as e:
        raise TokenVerificationError("Invalid token signature") from e
    except jwt.InvalidAudienceError as e:
        raise TokenVerificationError(f"Invalid token audience: {e}") from e
    except jwt.InvalidIssuerError as e:
        raise TokenVerificationError(f"Invalid token issuer: {e}") from e
    except jwt.DecodeError as e:
        raise TokenVerificationError(f"Invalid or malformed token: {e}") from e
    except Exception as e:
        raise TokenVerificationError(f"Token verification failed: {e}") from e


def extract_user_id(payload: dict) -> int:
    """Extract user ID from token payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        User ID as integer

    Raises:
        TokenVerificationError: If user ID is missing or invalid
    """
    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as e:
        raise TokenVerificationError(f"Invalid user ID in token: {e}") from e


def extract_scopes(payload: dict) -> list[str]:
    """Extract scopes from token payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        List of scope strings

    Example:
        >>> scopes = extract_scopes(payload)
        >>> if "tasks:read" in scopes:
        ...     # Allow read access
    """
    scope_string = payload.get("scope", "")
    return scope_string.split() if scope_string else []


def require_scope(payload: dict, required_scope: str) -> None:
    """Verify that token has required scope.

    Args:
        payload: Decoded JWT payload
        required_scope: Scope to check for

    Raises:
        TokenVerificationError: If required scope is not present
    """
    scopes = extract_scopes(payload)
    if required_scope not in scopes:
        raise TokenVerificationError(f"Missing required scope: {required_scope}")
