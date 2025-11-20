"""
Payment Domain Model
====================

MongoDB document model for payments.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PaymentMethod(BaseModel):
    """Payment method details"""
    type: str  # card, bank_account, wallet
    last4: Optional[str] = None
    brand: Optional[str] = None  # visa, mastercard, amex
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None


class Payment(BaseModel):
    """Payment document model"""
    id: Optional[str] = Field(default=None, alias="_id")
    order_id: str
    user_id: str
    amount: float
    currency: str = "usd"
    status: str  # pending, processing, succeeded, failed, refunded, cancelled
    payment_method: PaymentMethod

    # Stripe
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None

    # Metadata
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Processing details
    processed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_message: Optional[str] = None

    # Refund details
    refunded_at: Optional[datetime] = None
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class PaymentHistory(BaseModel):
    """Payment history entry"""
    payment_id: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
