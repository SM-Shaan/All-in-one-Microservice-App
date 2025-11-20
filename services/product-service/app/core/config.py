"""
Product Service Configuration
==============================

Service-specific configuration for product catalog management.

Key differences from User Service:
- Uses MongoDB instead of PostgreSQL
- Different port (8002 vs 8001)
- Different database name
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Product Service specific settings.

    Environment variables can override these defaults.
    """

    # Application
    app_name: str = "product-service"
    app_version: str = "1.0.0"
    debug: bool = True

    # MongoDB Configuration
    # Format: mongodb://username:password@host:port/database
    mongodb_url: str = "mongodb://admin:admin123@localhost:27017"
    mongodb_db_name: str = "products"

    # Kafka - for publishing product events
    kafka_bootstrap_servers: str = "localhost:9092"

    # Redis - for product caching
    redis_url: str = "redis://localhost:6379/1"  # DB 1 for products

    # Service settings
    service_host: str = "0.0.0.0"
    service_port: int = 8002  # Different port from user service

    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Usage:
        from app.core.config import settings
        print(settings.mongodb_url)
    """
    return Settings()


# Convenience: direct access to settings
settings = get_settings()
