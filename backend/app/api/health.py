"""Health check API endpoints with database connectivity validation."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check endpoint.

    Returns:
        JSON response with health status, version, environment, and component checks

    Status Codes:
        200: All systems healthy
        503: Service degraded (database connectivity issues)
    """
    health = {
        "status": "healthy",
        "version": "4.0.0",
        "environment": settings.environment,
        "checks": {},
    }

    # Database connectivity check
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = "unhealthy"
        health["status"] = "degraded"
        logger.error("Database health check failed", error=str(e), exc_info=True)

    # Return appropriate status code
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)
