"""
User Service Configuration
--------------------------
Service-specific configuration extending the base config.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    User Service specific settings.

    These can be overridden by environment variables.
    Example: Set APP_NAME=my-user-service in environment
    """

    # Application
    app_name: str = "user-service"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database - PostgreSQL for user data
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/users"

    # Redis - for session caching
    redis_url: str = "redis://localhost:6379/0"

    # Kafka - for publishing user events
    kafka_bootstrap_servers: str = "localhost:9092"

    # JWT Configuration (Phase 10: Authentication)
    jwt_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Change in production!
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 minutes (short-lived)
    refresh_token_expire_days: int = 7     # 7 days (long-lived)

    # Service settings
    service_host: str = "0.0.0.0"
    service_port: int = 8001  # User service port

    # Other service URLs (for service-to-service communication)
    product_service_url: str = "http://localhost:8002"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Usage:
        from app.core.config import get_settings
        settings = get_settings()
        print(settings.database_url)
    """
    return Settings()


# Convenience: direct access to settings
settings = get_settings()
