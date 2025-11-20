"""
Notification Schemas
====================

Pydantic schemas for notification API requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, field_validator


# ============================================================================
# Request Schemas
# ============================================================================

class RecipientInput(BaseModel):
    """Recipient input"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            # Basic phone validation
            cleaned = ''.join(filter(str.isdigit, v))
            if len(cleaned) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v


class SendEmailRequest(BaseModel):
    """Request to send an email"""
    recipient: RecipientInput
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    html_body: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SendSMSRequest(BaseModel):
    """Request to send an SMS"""
    recipient: RecipientInput
    body: str = Field(..., min_length=1, max_length=1600)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('body')
    @classmethod
    def validate_body(cls, v):
        if len(v) > 1600:
            raise ValueError('SMS body cannot exceed 1600 characters')
        return v


class SendNotificationRequest(BaseModel):
    """Generic notification request"""
    type: str = Field(..., description="Notification type: email, sms, push")
    recipient: RecipientInput
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    template_name: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['email', 'sms', 'push']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of {allowed_types}')
        return v


class BulkNotificationRequest(BaseModel):
    """Request to send bulk notifications"""
    type: str
    recipients: List[RecipientInput]
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    template_name: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None


# ============================================================================
# Response Schemas
# ============================================================================

class RecipientResponse(BaseModel):
    """Recipient response"""
    email: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None


class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    type: str
    channel: str
    recipient: RecipientResponse
    subject: Optional[str] = None
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications"""
    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int


class NotificationStatusResponse(BaseModel):
    """Notification status response"""
    notification_id: str
    status: str
    message: str


class BulkNotificationResponse(BaseModel):
    """Bulk notification response"""
    total_sent: int
    total_failed: int
    notification_ids: List[str]
    failed_recipients: List[RecipientResponse]


# ============================================================================
# Template Schemas
# ============================================================================

class CreateTemplateRequest(BaseModel):
    """Request to create a template"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Template type: email, sms")
    subject: Optional[str] = None
    body_template: str = Field(..., min_length=1)
    html_template: Optional[str] = None
    variables: List[str] = []

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        # Template name should be alphanumeric with underscores
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Template name must be alphanumeric with underscores/hyphens')
        return v


class TemplateResponse(BaseModel):
    """Template response"""
    id: str
    name: str
    type: str
    subject: Optional[str] = None
    body_template: str
    html_template: Optional[str] = None
    variables: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """List of templates"""
    templates: List[TemplateResponse]
    total: int


# ============================================================================
# Event Schemas
# ============================================================================

class NotificationEvent(BaseModel):
    """Notification event for Kafka"""
    event_type: str  # notification_created, notification_sent, notification_failed
    notification_id: str
    type: str  # email, sms, push
    recipient: RecipientResponse
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
