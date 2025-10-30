"""Database connection and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine with production-ready connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    
    # Production pooling configuration
    pool_size=10,          # 10 persistent connections
    max_overflow=5,        # +5 during traffic spikes
    pool_timeout=30,       # Wait 30s for connection
    pool_pre_ping=True,    # Verify connection before use
    pool_recycle=3600,     # Recycle connections every hour (prevents stale connections)
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Declarative base for models
Base = declarative_base()


# Dependency injection for FastAPI
async def get_db() -> AsyncSession:
    """Yield database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        yield session
