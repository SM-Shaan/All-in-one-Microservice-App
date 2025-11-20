"""
Base Event Schema
=================

All events inherit from this base schema.

Event Structure:
- metadata: Who, what, when
- payload: The actual data
"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4, UUID
from typing import Optional


class EventMetadata(BaseModel):
    """
    Metadata for all events.

    Contains information about the event itself.
    """
    # Event identification
    event_id: UUID = Field(default_factory=uuid4, description="Unique event ID")
    event_type: str = Field(..., description="Type of event (e.g., user.created)")
    event_version: str = Field(default="1.0", description="Event schema version")

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When event occurred")

    # Tracing (for distributed tracing)
    correlation_id: Optional[UUID] = Field(None, description="ID to trace related events")
    causation_id: Optional[UUID] = Field(None, description="ID of event that caused this")

    # Source
    source_service: str = Field(..., description="Service that produced the event")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "user.created",
                "event_version": "1.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "correlation_id": "660e8400-e29b-41d4-a716-446655440000",
                "source_service": "user-service"
            }
        }


class BaseEvent(BaseModel):
    """
    Base class for all events.

    All events should:
    1. Inherit from this class
    2. Have metadata (event info)
    3. Have payload (event data)
    """
    metadata: EventMetadata

    def to_json(self) -> str:
        """Serialize event to JSON string"""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str):
        """Deserialize event from JSON string"""
        return cls.model_validate_json(json_str)
