"""Tests for JWKS (JSON Web Key Set) endpoint."""

import base64
import shutil
from pathlib import Path

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from fastapi.testclient import TestClient

from app.main import app
from app.oauth.jwks import KEYS_DIR, ensure_keys_exist, load_public_key

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_keys():
    """Clean up generated keys after each test."""
    yield
    # Remove keys directory after test
    if KEYS_DIR.exists():
        shutil.rmtree(KEYS_DIR)


@pytest.mark.asyncio
async def test_jwks_endpoint_returns_valid_jwk():
    """Test that JWKS endpoint returns a valid JWK."""
    response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    data = response.json()

    # Must have keys array
    assert "keys" in data
    assert isinstance(data["keys"], list)
    assert len(data["keys"]) > 0

    # First key should be RSA
    key = data["keys"][0]
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert key["alg"] == "RS256"
    assert "kid" in key


@pytest.mark.asyncio
async def test_jwks_contains_modulus_and_exponent():
    """Test that JWK contains RSA public key components."""
    response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    key = response.json()["keys"][0]

    # Must have modulus (n) and exponent (e)
    assert "n" in key
    assert "e" in key

    # Should be base64url encoded (no padding)
    assert "=" not in key["n"]
    assert "=" not in key["e"]


@pytest.mark.asyncio
async def test_jwks_key_can_be_decoded():
    """Test that JWK modulus and exponent can be decoded."""
    response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    key = response.json()["keys"][0]

    # Decode modulus and exponent
    n_bytes = base64.urlsafe_b64decode(key["n"] + "==")  # Add padding
    e_bytes = base64.urlsafe_b64decode(key["e"] + "==")

    # Should decode to integers
    n = int.from_bytes(n_bytes, byteorder="big")
    e = int.from_bytes(e_bytes, byteorder="big")

    assert n > 0
    assert e > 0
    assert e == 65537  # Standard RSA exponent


@pytest.mark.asyncio
async def test_keys_are_generated_automatically():
    """Test that RSA keys are generated automatically on first request."""
    assert not KEYS_DIR.exists()

    # First request should generate keys
    response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    assert KEYS_DIR.exists()
    assert (KEYS_DIR / "private_key.pem").exists()
    assert (KEYS_DIR / "public_key.pem").exists()


@pytest.mark.asyncio
async def test_keys_are_reused_on_subsequent_requests():
    """Test that existing keys are reused, not regenerated."""
    # First request generates keys
    response1 = client.get("/.well-known/jwks.json")
    key1 = response1.json()["keys"][0]

    # Second request should return same key
    response2 = client.get("/.well-known/jwks.json")
    key2 = response2.json()["keys"][0]

    assert key1 == key2


@pytest.mark.asyncio
async def test_public_key_can_be_loaded_and_used():
    """Test that public key can be loaded from PEM format."""
    ensure_keys_exist()

    public_pem = load_public_key()

    # Should be valid PEM
    assert public_pem.startswith(b"-----BEGIN PUBLIC KEY-----")
    assert public_pem.endswith(b"-----END PUBLIC KEY-----\n")

    # Should be loadable
    public_key = load_pem_public_key(public_pem, backend=default_backend())
    assert public_key is not None


@pytest.mark.asyncio
async def test_private_key_has_secure_permissions():
    """Test that private key file has restrictive permissions (600)."""
    ensure_keys_exist()

    private_key_path = KEYS_DIR / "private_key.pem"

    # Check file permissions (owner read/write only)
    import stat

    st = private_key_path.stat()
    mode = st.st_mode

    # Should be readable and writable by owner only
    assert mode & stat.S_IRUSR  # Owner read
    assert mode & stat.S_IWUSR  # Owner write
    assert not (mode & stat.S_IRGRP)  # No group read
    assert not (mode & stat.S_IWGRP)  # No group write
    assert not (mode & stat.S_IROTH)  # No others read
    assert not (mode & stat.S_IWOTH)  # No others write
