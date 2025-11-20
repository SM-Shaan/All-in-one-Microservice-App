"""
Notification Domain Model
=========================

MongoDB document model for notifications.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId


class NotificationRecipient(BaseModel):
    """Notification recipient"""
    email: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None


class Notification(BaseModel):
    """Notification document model"""
    id: Optional[str] = Field(default=None, alias="_id")

    # Type and channel
    type: str  # email, sms, push
    channel: str  # smtp, sendgrid, twilio, fcm
    template_name: Optional[str] = None  # Template to use

    # Recipient
    recipient: NotificationRecipient

    # Content
    subject: Optional[str] = None  # For emails
    body: str
    html_body: Optional[str] = None  # For HTML emails

    # Status
    status: str  # pending, sending, sent, failed, cancelled

    # Metadata
    metadata: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Provider response
    provider_id: Optional[str] = None  # ID from provider (SendGrid, Twilio, etc.)
    provider_response: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class NotificationTemplate(BaseModel):
    """Notification template"""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str  # unique template name
    type: str  # email, sms
    subject: Optional[str] = None  # For email templates
    body_template: str  # Template with placeholders
    html_template: Optional[str] = None  # HTML template for emails
    variables: List[str] = []  # List of required variables
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
