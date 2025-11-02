"""JWKS (JSON Web Key Set) endpoint for JWT verification.

Exposes public keys used to sign JWTs so MCP server can verify tokens.
"""

import os
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter

router = APIRouter()

# Key storage path
KEYS_DIR = Path("app/oauth/keys")
PRIVATE_KEY_PATH = KEYS_DIR / "private_key.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "public_key.pem"


def generate_rsa_keypair() -> tuple[bytes, bytes]:
    """Generate RSA key pair for JWT signing.

    Returns:
        Tuple of (private_key_pem, public_key_pem)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem


def ensure_keys_exist() -> None:
    """Ensure RSA keys exist, generate if missing."""
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    if not PRIVATE_KEY_PATH.exists() or not PUBLIC_KEY_PATH.exists():
        private_pem, public_pem = generate_rsa_keypair()

        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(private_pem)

        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(public_pem)

        # Secure permissions (owner read/write only)
        os.chmod(PRIVATE_KEY_PATH, 0o600)
        os.chmod(PUBLIC_KEY_PATH, 0o644)


def load_public_key() -> bytes:
    """Load public key from file.

    Returns:
        Public key PEM bytes
    """
    ensure_keys_exist()
    with open(PUBLIC_KEY_PATH, "rb") as f:
        return f.read()


def get_jwk_from_public_key() -> dict[str, str]:
    """Convert RSA public key to JWK format.

    Returns:
        JWK (JSON Web Key) representation
    """
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    public_pem = load_public_key()
    public_key = load_pem_public_key(public_pem, backend=default_backend())

    # Extract public numbers
    numbers = public_key.public_numbers()  # type: ignore[attr-defined]

    # Convert to base64url (without padding)
    import base64

    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, byteorder="big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, byteorder="big")

    n_b64 = base64.urlsafe_b64encode(n_bytes).decode("utf-8").rstrip("=")
    e_b64 = base64.urlsafe_b64encode(e_bytes).decode("utf-8").rstrip("=")

    return {
        "kty": "RSA",
        "use": "sig",
        "kid": "mindflow-2024",  # Key ID
        "alg": "RS256",
        "n": n_b64,  # Modulus
        "e": e_b64,  # Exponent
    }


@router.get("/.well-known/jwks.json")
async def jwks() -> dict[str, list[dict[str, str]]]:
    """JWKS endpoint exposing public keys for JWT verification.

    Returns:
        JSON Web Key Set containing public keys

    Spec: RFC 7517 - JSON Web Key (JWK)
    """
    jwk = get_jwk_from_public_key()
    return {"keys": [jwk]}
