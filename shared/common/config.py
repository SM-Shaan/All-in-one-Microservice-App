"""
Shared Configuration Module
---------------------------
This module provides base configuration that all services inherit from.
Uses Pydantic Settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class BaseConfig(BaseSettings):
    """
    Base configuration class that all services extend.

    Environment variables are automatically loaded.
    Example: DATABASE_URL environment variable maps to database_url field.
    """

    # Application Info
    app_name: str = "microservice"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Service Discovery (Consul)
    consul_host: str = "localhost"
    consul_port: int = 8500

    # Observability
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831

    class Config:
        # This tells Pydantic to read from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields


@lru_cache()
def get_base_config() -> BaseConfig:
    """
    Returns cached configuration instance.

    Using lru_cache ensures we only create one config instance.
    This is a common pattern called "singleton".
    """
    return BaseConfig()
