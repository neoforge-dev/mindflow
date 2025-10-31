"""FastAPI application setup with health check and error handling."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.middleware.rate_limit import setup_rate_limiting
from app.middleware.request_logging import RequestIDMiddleware
from app.monitoring import init_sentry

# Initialize Sentry error monitoring (if configured)
init_sentry(settings)

# Setup structured logging
configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="MindFlow API",
        description="AI-first task manager API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.debug,
    )

    # CORS middleware (allow all in dev, specific in prod)
    if settings.debug:
        # Development: Allow all for testing
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Production: Specific origins only
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://chat.openai.com",
                "https://chatgpt.com",
                "https://*.openai.com",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_request: Request, exc: Exception):
        # Log full traceback for debugging with structured logging
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )

        # Return detailed error in dev, generic in prod
        if settings.debug:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error": str(exc),
                    "type": type(exc).__name__,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

    # Setup request ID and logging middleware
    app.add_middleware(RequestIDMiddleware)

    # Setup rate limiting
    setup_rate_limiting(app)

    # Include routers
    from app.api.auth import router as auth_router
    from app.api.health import router as health_router
    from app.api.tasks import router as tasks_router

    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(tasks_router)

    return app


app = create_app()
