"""JWT generation and validation utilities for OAuth 2.1.

Implements RS256 (RSA SHA-256) asymmetric signing for OAuth 2.1 access tokens.
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Key storage path (from jwks.py)
KEYS_DIR = Path("app/oauth/keys")
PRIVATE_KEY_PATH = KEYS_DIR / "private_key.pem"


def load_private_key() -> bytes:
    """Load private key from file for JWT signing.

    Returns:
        Private key PEM bytes

    Raises:
        FileNotFoundError: If private key doesn't exist
    """
    if not PRIVATE_KEY_PATH.exists():
        msg = f"Private key not found at {PRIVATE_KEY_PATH}. Run ensure_keys_exist() first."
        raise FileNotFoundError(msg)

    with open(PRIVATE_KEY_PATH, "rb") as f:
        return f.read()


def create_access_token(
    user_id: int,
    client_id: str,
    scope: str,
    expires_delta: timedelta = timedelta(hours=1),
) -> str:
    """Generate JWT access token signed with RS256.

    Args:
        user_id: User ID (becomes 'sub' claim)
        client_id: OAuth client ID
        scope: Granted scopes (space-separated string)
        expires_delta: Token expiration duration (default: 1 hour)

    Returns:
        Signed JWT access token

    Example:
        >>> token = create_access_token(123, "chatgpt-client", "tasks:read tasks:write")
        >>> # token is a JWT string like "eyJhbGciOiJSUzI1NiIs..."
    """
    private_key_pem = load_private_key()

    # Load private key for signing
    private_key = serialization.load_pem_private_key(
        private_key_pem, password=None, backend=default_backend()
    )

    now = datetime.now(UTC)
    expire = now + expires_delta

    # JWT claims (RFC 7519)
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "client_id": client_id,  # OAuth client
        "scope": scope,  # Granted scopes
        "iss": os.getenv("OAUTH_ISSUER", "https://mindflow.example.com"),  # Issuer
        "aud": "mindflow-api",  # Audience
        "exp": int(expire.timestamp()),  # Expiration time
        "iat": int(now.timestamp()),  # Issued at
        "jti": os.urandom(16).hex(),  # JWT ID (unique identifier)
    }

    # Sign with RS256 (RSA SHA-256)
    token = jwt.encode(
        payload,
        private_key,  # type: ignore[arg-type]
        algorithm="RS256",
        headers={"kid": "mindflow-2024"},  # Key ID (matches JWKS)
    )

    return token


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token.

    Args:
        token: JWT access token string

    Returns:
        Decoded payload dictionary

    Raises:
        jwt.InvalidTokenError: If token is invalid, expired, or signature fails
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidSignatureError: If signature verification fails
    """
    from app.oauth.jwks import load_public_key

    public_key_pem = load_public_key()

    # Load public key for verification
    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())

    # Verify signature and decode
    payload = jwt.decode(
        token,
        public_key,  # type: ignore[arg-type]
        algorithms=["RS256"],
        audience="mindflow-api",
        options={"verify_exp": True, "verify_aud": True},
    )

    return payload


def verify_token_claims(token: str, required_scope: str | None = None) -> dict:
    """Verify JWT token and optionally check scope.

    Args:
        token: JWT access token
        required_scope: Required scope (optional)

    Returns:
        Decoded payload if valid

    Raises:
        jwt.InvalidTokenError: If token is invalid
        PermissionError: If required scope is not present
    """
    payload = decode_access_token(token)

    # Check required scope if specified
    if required_scope:
        token_scopes = set(payload.get("scope", "").split())
        if required_scope not in token_scopes:
            msg = f"Token missing required scope: {required_scope}"
            raise PermissionError(msg)

    return payload
