"""Application configuration using Pydantic settings."""

import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/mindflow"
    )

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # OAuth & Apps SDK
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"

    # Monitoring
    sentry_dsn: str | None = os.getenv("SENTRY_DSN", None)

    # Analytics (PostHog)
    posthog_api_key: str | None = os.getenv("POSTHOG_API_KEY", None)
    posthog_host: str = os.getenv("POSTHOG_HOST", "https://eu.posthog.com")

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",  # Ignore extra fields from .env
    )

    @property
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "testing"


settings = Settings()
