"""
Inventory Service Configuration
================================

Configuration for the inventory service.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Inventory service settings"""

    # Service
    service_name: str = "inventory-service"
    service_port: int = 8006

    # MongoDB
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "inventory_db")

    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_inventory_topic: str = "inventory-events"

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT (for auth)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"

    # Low stock threshold
    low_stock_threshold: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
