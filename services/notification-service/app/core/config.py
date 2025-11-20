"""
Notification Service Configuration
===================================

Configuration for the notification service.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Notification service settings"""

    # Service
    service_name: str = "notification-service"
    service_port: int = 8005

    # MongoDB
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "notification_db")

    # Email (SMTP)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "E-Commerce Platform")

    # SendGrid (Alternative to SMTP)
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")

    # Twilio (SMS)
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_notification_topic: str = "notification-events"

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT (for auth)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"

    # Templates
    templates_dir: str = "app/templates"

    class Config:
        env_file = ".env"


settings = Settings()
