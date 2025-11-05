"""OAuth 2.1 Authorization Endpoint for ChatGPT Apps SDK integration.

Implements RFC 6749 (OAuth 2.0) Section 4.1 Authorization Code Grant with:
- PKCE (RFC 7636) for enhanced security
- User authentication and consent
- Comprehensive error handling per RFC 6749 Section 4.1.2.1
"""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.dependencies import get_db
from app.oauth.crud import OAuthAuthorizationCodeCRUD, OAuthClientCRUD
from app.oauth.csrf import CSRFTokenStorage
from app.oauth.schemas import AuthorizationRequest

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/oauth/templates")


def get_optional_user(request: Request) -> User | None:
    """
    Get current user from session if authenticated, otherwise return None.

    This is a simplified implementation. In production, you would:
    1. Check for session cookie
    2. Validate session token
    3. Retrieve user from database

    For now, we'll use a query parameter hack for testing.
    """
    # HACK: For testing, accept user_id from query param
    # In production, this should check session cookie and validate
    user_id = request.query_params.get("user_id")
    if user_id:
        # Create a mock user object for testing
        user = User()
        user.id = int(user_id)
        user.email = f"user{user_id}@example.com"
        user.full_name = f"Test User {user_id}"
        return user
    return None


@router.get("/authorize", response_model=None)
async def authorize_get(
    request: Request,
    client_id: Annotated[str, Query(..., description="OAuth client ID")],
    redirect_uri: Annotated[str, Query(..., description="Redirect URI for response")],
    response_type: Annotated[str, Query(..., description="Must be 'code'")],
    scope: Annotated[str, Query(..., description="Requested scopes")],
    state: Annotated[str, Query(..., description="CSRF state parameter")],
    code_challenge: Annotated[str, Query(..., description="PKCE code challenge")],
    code_challenge_method: Annotated[str, Query(..., description="PKCE method (S256)")],
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth 2.1 Authorization Endpoint (GET).

    Validates authorization request and displays consent screen if user is authenticated.

    RFC 6749 Section 4.1.1: Authorization Request
    RFC 7636: PKCE for OAuth Public Clients
    """
    # Validate request parameters using Pydantic
    try:
        auth_request = AuthorizationRequest(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
    except ValueError as e:
        # Invalid request parameters - cannot redirect, show error page
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Invalid Request</title></head>
                <body>
                    <h1>Invalid Authorization Request</h1>
                    <p>Error: {str(e)}</p>
                    <p>The authorization request is malformed or missing required parameters.</p>
                </body>
            </html>
            """,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate response_type is "code"
    if auth_request.response_type != "code":
        return _redirect_error(
            redirect_uri,
            "unsupported_response_type",
            "Only 'code' response_type is supported",
            state,
        )

    # Validate client exists and is active
    client = await OAuthClientCRUD.get_by_client_id(db, auth_request.client_id)
    if not client or not client.is_active:
        # Invalid client - cannot redirect (don't trust redirect_uri)
        return HTMLResponse(
            content="""
            <html>
                <head><title>Invalid Client</title></head>
                <body>
                    <h1>Invalid Client</h1>
                    <p>The OAuth client is not registered or has been disabled.</p>
                </body>
            </html>
            """,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate redirect_uri matches registered URIs
    if not await OAuthClientCRUD.validate_redirect_uri(db, client_id, redirect_uri):
        # Invalid redirect_uri - cannot redirect (security risk)
        return HTMLResponse(
            content="""
            <html>
                <head><title>Invalid Redirect URI</title></head>
                <body>
                    <h1>Invalid Redirect URI</h1>
                    <p>The redirect_uri does not match any registered URIs for this client.</p>
                </body>
            </html>
            """,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate requested scopes are allowed
    if not await OAuthClientCRUD.validate_scopes(db, client_id, scope):
        return _redirect_error(
            redirect_uri,
            "invalid_scope",
            "One or more requested scopes are not allowed for this client",
            state,
        )

    # Check if user is authenticated
    current_user = get_optional_user(request)

    if not current_user:
        # User not logged in - redirect to login page with return URL
        login_url = f"/api/auth/login?return_to={request.url}"
        return RedirectResponse(url=login_url, status_code=status.HTTP_303_SEE_OTHER)

    # Generate CSRF token for consent form (Redis-backed, works across workers)
    csrf_token = await CSRFTokenStorage.generate_token(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "user_id": str(current_user.id),
        }
    )

    # Display consent screen
    return templates.TemplateResponse(
        request=request,
        name="consent.html",
        context={
            "client_name": client.client_name,
            "client_logo": client.logo_uri,
            "scopes": scope.split(),
            "scope_descriptions": _get_scope_descriptions(scope),
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "csrf_token": csrf_token,
        },
    )


@router.post("/authorize", response_model=None)
async def authorize_post(
    client_id: Annotated[str, Form(...)],
    redirect_uri: Annotated[str, Form(...)],
    scope: Annotated[str, Form(...)],
    state: Annotated[str, Form(...)],
    code_challenge: Annotated[str, Form(...)],
    code_challenge_method: Annotated[str, Form(...)],
    approve: Annotated[bool, Form(...)],
    csrf_token: Annotated[str, Form(...)],
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth 2.1 Authorization Endpoint (POST) - Handle consent decision.

    Processes user's consent decision and generates authorization code if approved.

    RFC 6749 Section 4.1.2: Authorization Response
    """
    # Validate CSRF token (Redis-backed, one-time use)
    csrf_data = await CSRFTokenStorage.validate_and_consume(csrf_token)
    if not csrf_data:
        return _redirect_error(
            redirect_uri, "access_denied", "Invalid or expired CSRF token", state
        )

    # Validate CSRF data matches form data
    if (
        csrf_data.get("client_id") != client_id
        or csrf_data.get("redirect_uri") != redirect_uri
        or csrf_data.get("scope") != scope
        or csrf_data.get("state") != state
        or csrf_data.get("code_challenge") != code_challenge
        or csrf_data.get("code_challenge_method") != code_challenge_method
    ):
        return _redirect_error(redirect_uri, "access_denied", "CSRF validation failed", state)

    # Get user_id from CSRF data
    user_id = int(csrf_data["user_id"])

    # Check if user denied consent
    if not approve:
        return _redirect_error(redirect_uri, "access_denied", "User denied authorization", state)

    # User approved - generate authorization code
    auth_code = await OAuthAuthorizationCodeCRUD.create(
        session=db,
        client_id=client_id,
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    # Redirect back to client with authorization code
    params = {
        "code": auth_code.code,
        "state": state,
    }

    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


def _redirect_error(
    redirect_uri: str,
    error: str,
    error_description: str,
    state: str,
) -> RedirectResponse:
    """
    Redirect to client with OAuth error response.

    RFC 6749 Section 4.1.2.1: Error Response
    """
    params = {
        "error": error,
        "error_description": error_description,
        "state": state,
    }

    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


def _get_scope_descriptions(scope: str) -> dict[str, str]:
    """Get user-friendly descriptions for OAuth scopes."""
    scope_map = {
        "tasks:read": "View your tasks",
        "tasks:write": "Create and modify your tasks",
        "openid": "Verify your identity",
        "profile": "Access your profile information",
        "email": "Access your email address",
    }

    return {s: scope_map.get(s, s) for s in scope.split()}
