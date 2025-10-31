"""Rate limiting middleware using slowapi.

Implements in-memory rate limiting for API endpoints:
- Task endpoints: 60 requests per minute
- Auth endpoints: 10 requests per minute
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded


def get_remote_address_safe(request: Request) -> str:
    """Get remote address safely handling proxies.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Return first IP in chain (original client)
        return forwarded.split(",")[0].strip()

    # Fall back to direct connection IP
    client = request.client
    if client:
        return client.host

    # Default fallback
    return "127.0.0.1"


# Create global limiter instance
limiter = Limiter(
    key_func=get_remote_address_safe,
    default_limits=["100/minute"],  # Global default
    storage_uri="memory://",  # In-memory storage (no Redis)
)


def rate_limit_handler(_request: Request, _exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors.

    Args:
        _request: FastAPI request object (unused)
        _exc: RateLimitExceeded exception (unused)

    Returns:
        JSON response with 429 status code
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "type": "rate_limit_error",
        },
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Store limiter on app state
    app.state.limiter = limiter

    # Register exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
