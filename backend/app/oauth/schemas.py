"""OAuth 2.1 Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, HttpUrl


class OAuthClientRegistrationRequest(BaseModel):
    """OAuth 2.1 Client Registration Request (RFC 7591)."""

    client_name: str = Field(
        ..., description="Human-readable client name", min_length=1, max_length=255
    )
    redirect_uris: list[HttpUrl] = Field(
        ..., description="List of valid redirect URIs", min_length=1
    )

    # Optional metadata
    logo_uri: HttpUrl | None = Field(None, description="URL to client logo")
    policy_uri: HttpUrl | None = Field(None, description="URL to privacy policy")
    tos_uri: HttpUrl | None = Field(None, description="URL to terms of service")

    # Requested capabilities
    grant_types: list[str] = Field(
        default=["authorization_code", "refresh_token"], description="OAuth 2.1 grant types"
    )
    response_types: list[str] = Field(default=["code"], description="OAuth 2.1 response types")
    scope: str = Field(
        default="tasks:read tasks:write openid profile email",
        description="Requested scopes (space-separated)",
    )


class OAuthClientRegistrationResponse(BaseModel):
    """OAuth 2.1 Client Registration Response (RFC 7591)."""

    client_id: str = Field(..., description="Unique client identifier")
    client_secret: str = Field(..., description="Client secret for authentication")
    client_name: str = Field(..., description="Client name")

    redirect_uris: list[str] = Field(..., description="Registered redirect URIs")
    grant_types: list[str] = Field(..., description="Allowed grant types")
    response_types: list[str] = Field(..., description="Allowed response types")
    scope: str = Field(..., description="Allowed scopes")

    # Optional metadata
    logo_uri: str | None = Field(None, description="Client logo URL")
    policy_uri: str | None = Field(None, description="Privacy policy URL")
    tos_uri: str | None = Field(None, description="Terms of service URL")

    # Registration metadata
    client_id_issued_at: int = Field(..., description="Unix timestamp of client ID issuance")

    model_config = {"from_attributes": True}


class OAuthClientInfoResponse(BaseModel):
    """OAuth 2.1 Client Information Response."""

    client_id: str
    client_name: str
    redirect_uris: list[str]
    scope: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class AuthorizationRequest(BaseModel):
    """OAuth 2.1 Authorization Request (RFC 6749 Section 4.1.1)."""

    client_id: str = Field(..., description="OAuth client identifier", min_length=1)
    redirect_uri: str = Field(
        ..., description="Redirect URI for authorization response", min_length=1
    )
    response_type: str = Field(..., description="Must be 'code' for authorization code flow")
    scope: str = Field(..., description="Space-separated list of requested scopes", min_length=1)
    state: str = Field(..., description="Opaque state value for CSRF protection", min_length=1)

    # PKCE parameters (RFC 7636)
    code_challenge: str = Field(
        ..., description="PKCE code challenge", min_length=43, max_length=128
    )
    code_challenge_method: str = Field(
        ..., description="PKCE challenge method (must be S256)", pattern="^S256$"
    )


class ConsentDecision(BaseModel):
    """User's consent decision for authorization request."""

    client_id: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)
    scope: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    code_challenge: str = Field(..., min_length=43, max_length=128)
    code_challenge_method: str = Field(..., pattern="^S256$")

    # User decision
    approve: bool = Field(..., description="True if user approved, False if denied")

    # CSRF protection
    csrf_token: str = Field(..., description="CSRF token for form validation", min_length=1)
