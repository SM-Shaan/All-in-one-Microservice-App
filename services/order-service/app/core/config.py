"""
Order Service Configuration
============================

Manages order processing with Saga pattern.

This service coordinates multiple services:
- User Service: Verify user exists
- Product Service: Check product availability
- Inventory Service: Reserve stock (simulated)
- Payment Service: Process payment (simulated)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Order Service configuration"""

    # Application
    app_name: str = "order-service"
    app_version: str = "1.0.0"
    debug: bool = True

    # MongoDB Configuration
    mongodb_url: str = "mongodb://admin:admin123@localhost:27017"
    mongodb_db_name: str = "orders"

    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"

    # Redis (for saga state management)
    redis_url: str = "redis://localhost:6379/2"  # DB 2 for orders

    # Service URLs
    user_service_url: str = "http://localhost:8001"
    product_service_url: str = "http://localhost:8002"

    # Service settings
    service_host: str = "0.0.0.0"
    service_port: int = 8003  # Port 8003 for Order Service

    # Saga Configuration
    saga_timeout_seconds: int = 300  # 5 minutes
    saga_retry_attempts: int = 3

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
