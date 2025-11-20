"""
Event Schemas Package
=====================

Shared event schemas used across all microservices.
"""

from shared.events.schemas.base import BaseEvent, EventMetadata
from shared.events.schemas.user_events import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeletedEvent,
    UserEventTopics
)
from shared.events.schemas.product_events import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductStockChangedEvent,
    ProductDeletedEvent,
    ProductEventTopics
)

__all__ = [
    "BaseEvent",
    "EventMetadata",
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserDeletedEvent",
    "UserEventTopics",
    "ProductCreatedEvent",
    "ProductUpdatedEvent",
    "ProductStockChangedEvent",
    "ProductDeletedEvent",
    "ProductEventTopics",
]
