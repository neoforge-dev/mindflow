"""MCP Server configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseSettings):
    """MCP Server configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server settings
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8001

    # FastAPI backend settings
    api_base_url: str = "http://localhost:8000"

    # JWT settings
    jwt_public_key_path: Path = Path("app/oauth/keys/public_key.pem")
    oauth_issuer: str = "https://mindflow.example.com"
    jwt_audience: str = "mindflow-api"

    # Rate limiting
    max_requests_per_minute: int = 60

    # Retry settings
    max_retries: int = 3
    retry_backoff_factor: float = 2.0  # Exponential backoff multiplier
    retry_base_delay: float = 1.0  # Base delay in seconds

    def get_public_key(self) -> bytes:
        """Load public key from file.

        Returns:
            Public key PEM bytes

        Raises:
            FileNotFoundError: If public key doesn't exist
        """
        if not self.jwt_public_key_path.exists():
            msg = f"Public key not found at {self.jwt_public_key_path}"
            raise FileNotFoundError(msg)

        with open(self.jwt_public_key_path, "rb") as f:
            return f.read()


# Global config instance
config = MCPServerConfig()
