"""
Payment Service Configuration
==============================

Configuration for the payment service.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Payment service settings"""

    # Service
    service_name: str = "payment-service"
    service_port: int = 8004

    # MongoDB
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "payment_db")

    # Stripe
    stripe_api_key: str = os.getenv("STRIPE_API_KEY", "sk_test_...")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")
    stripe_currency: str = "usd"
    stripe_mock_mode: bool = os.getenv("STRIPE_MOCK_MODE", "true").lower() == "true"

    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_payment_topic: str = "payment-events"

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT (for auth)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
