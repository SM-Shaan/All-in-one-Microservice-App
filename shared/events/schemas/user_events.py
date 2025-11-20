"""
User Events
===========

Events published by User Service.

Other services can listen to these events and react:
- Notification Service: Send welcome email
- Analytics Service: Track user registrations
- Email Service: Add to mailing list
"""

from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

from shared.events.schemas.base import BaseEvent, EventMetadata


# ============================================================================
# Event Payloads (The actual data)
# ============================================================================

class UserCreatedPayload(BaseModel):
    """Data for user.created event"""
    user_id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime


class UserUpdatedPayload(BaseModel):
    """Data for user.updated event"""
    user_id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    updated_at: datetime


class UserDeletedPayload(BaseModel):
    """Data for user.deleted event"""
    user_id: UUID
    email: EmailStr
    deleted_at: datetime


# ============================================================================
# Event Classes
# ============================================================================

class UserCreatedEvent(BaseEvent):
    """
    Published when a new user is created.

    Consumers might:
    - Send welcome email
    - Create user profile in other services
    - Update analytics
    - Add to mailing list

    Example:
        event = UserCreatedEvent(
            metadata=EventMetadata(
                event_type="user.created",
                source_service="user-service"
            ),
            payload=UserCreatedPayload(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )

        await producer.publish(event)
    """
    payload: UserCreatedPayload

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "event_type": "user.created",
                    "source_service": "user-service"
                },
                "payload": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z"
                }
            }
        }


class UserUpdatedEvent(BaseEvent):
    """Published when a user is updated"""
    payload: UserUpdatedPayload


class UserDeletedEvent(BaseEvent):
    """Published when a user is deleted"""
    payload: UserDeletedPayload


# ============================================================================
# Event Topics (Kafka topics)
# ============================================================================

class UserEventTopics:
    """
    Kafka topic names for user events.

    Convention: {domain}.{entity}.{action}
    """
    USER_CREATED = "users.user.created"
    USER_UPDATED = "users.user.updated"
    USER_DELETED = "users.user.deleted"
