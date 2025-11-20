"""
Payment Schemas
===============

Pydantic schemas for payment API requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Schemas
# ============================================================================

class PaymentMethodInput(BaseModel):
    """Payment method input"""
    type: str = Field(..., description="Payment method type: card, bank_account, wallet")
    card_number: Optional[str] = Field(None, description="Card number (will be tokenized)")
    exp_month: Optional[int] = Field(None, ge=1, le=12)
    exp_year: Optional[int] = Field(None, ge=2025)
    cvv: Optional[str] = Field(None, min_length=3, max_length=4)

    # Stripe token (if already tokenized on client side)
    stripe_token: Optional[str] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['card', 'bank_account', 'wallet']
        if v not in allowed_types:
            raise ValueError(f'Payment type must be one of {allowed_types}')
        return v


class CreatePaymentRequest(BaseModel):
    """Request to create a payment"""
    order_id: str = Field(..., description="Order ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="usd", description="Currency code")
    payment_method: PaymentMethodInput
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 999999:
            raise ValueError('Amount too large')
        return round(v, 2)


class ProcessPaymentRequest(BaseModel):
    """Request to process a payment"""
    payment_id: str


class RefundPaymentRequest(BaseModel):
    """Request to refund a payment"""
    payment_id: str
    amount: Optional[float] = Field(None, gt=0, description="Refund amount (partial or full)")
    reason: Optional[str] = Field(None, description="Refund reason")


class CancelPaymentRequest(BaseModel):
    """Request to cancel a payment"""
    payment_id: str
    reason: Optional[str] = None


# ============================================================================
# Response Schemas
# ============================================================================

class PaymentMethodResponse(BaseModel):
    """Payment method response"""
    type: str
    last4: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None


class PaymentResponse(BaseModel):
    """Payment response"""
    id: str
    order_id: str
    user_id: str
    amount: float
    currency: str
    status: str
    payment_method: PaymentMethodResponse
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_message: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """List of payments"""
    payments: list[PaymentResponse]
    total: int
    page: int
    page_size: int


class RefundResponse(BaseModel):
    """Refund response"""
    payment_id: str
    refund_amount: float
    refunded_at: datetime
    reason: Optional[str] = None
    status: str


class PaymentStatusResponse(BaseModel):
    """Payment status response"""
    payment_id: str
    status: str
    message: str


# ============================================================================
# Event Schemas
# ============================================================================

class PaymentEvent(BaseModel):
    """Payment event for Kafka"""
    event_type: str  # payment_created, payment_succeeded, payment_failed, payment_refunded
    payment_id: str
    order_id: str
    user_id: str
    amount: float
    currency: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
