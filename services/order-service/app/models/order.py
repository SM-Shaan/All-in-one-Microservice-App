"""
Order Models
============

Order management with Saga pattern.

Saga Pattern:
A saga is a sequence of local transactions where each transaction
updates data within a single service. If a step fails, the saga
executes compensating transactions to undo the impact.

Example Order Saga:
1. Create Order → Success
2. Reserve Inventory → Success
3. Process Payment → FAIL!
4. Compensate: Release Inventory
5. Compensate: Cancel Order
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class OrderStatus(str, Enum):
    """Order status states"""
    PENDING = "pending"          # Order created, saga starting
    CONFIRMED = "confirmed"      # All saga steps completed
    CANCELLED = "cancelled"      # Saga failed, compensated
    FAILED = "failed"           # Saga failed, compensation failed


class SagaStep(str, Enum):
    """Steps in the order saga"""
    CREATE_ORDER = "create_order"
    VERIFY_USER = "verify_user"
    CHECK_PRODUCTS = "check_products"
    RESERVE_INVENTORY = "reserve_inventory"
    PROCESS_PAYMENT = "process_payment"
    CONFIRM_ORDER = "confirm_order"


class SagaStatus(str, Enum):
    """Saga execution status"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


# ============================================================================
# Order Models
# ============================================================================

class OrderItem(BaseModel):
    """Item in an order"""
    product_id: str  # MongoDB ObjectId from Product Service
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    subtotal: float = Field(gt=0)


class ShippingAddress(BaseModel):
    """Shipping address"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class Order(BaseModel):
    """
    Order document stored in MongoDB.

    The order goes through a saga workflow to be confirmed.
    """
    # MongoDB ID
    id: Optional[str] = Field(None, alias="_id")

    # Order information
    order_number: str = Field(..., description="Unique order number")
    user_id: str  # UUID from User Service

    # Items
    items: List[OrderItem]

    # Pricing
    subtotal: float
    tax: float = 0.0
    shipping_cost: float = 0.0
    total: float

    # Shipping
    shipping_address: ShippingAddress

    # Status
    status: OrderStatus = OrderStatus.PENDING

    # Saga tracking
    saga_id: Optional[str] = None
    saga_status: Optional[SagaStatus] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    class Config:
        populate_by_name = True


# ============================================================================
# Saga State Model
# ============================================================================

class SagaStepState(BaseModel):
    """State of a single saga step"""
    step: SagaStep
    status: str  # "pending", "completed", "failed", "compensated"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    compensation_performed: bool = False


class SagaState(BaseModel):
    """
    Tracks the state of an order saga.

    This is stored separately (in Redis or MongoDB) and tracks
    each step of the saga execution.

    Example:
    {
        "saga_id": "saga-123",
        "order_id": "order-456",
        "status": "in_progress",
        "current_step": "process_payment",
        "steps": [
            {"step": "create_order", "status": "completed"},
            {"step": "verify_user", "status": "completed"},
            {"step": "check_products", "status": "completed"},
            {"step": "reserve_inventory", "status": "completed"},
            {"step": "process_payment", "status": "in_progress"}
        ]
    }
    """
    saga_id: str
    order_id: str
    status: SagaStatus
    current_step: Optional[SagaStep] = None

    # Track each step
    steps: List[SagaStepState] = []

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None
    compensation_required: bool = False

    def mark_step_started(self, step: SagaStep):
        """Mark a step as started"""
        self.current_step = step
        step_state = SagaStepState(
            step=step,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        self.steps.append(step_state)

    def mark_step_completed(self, step: SagaStep):
        """Mark a step as completed"""
        for step_state in self.steps:
            if step_state.step == step:
                step_state.status = "completed"
                step_state.completed_at = datetime.utcnow()
                break

    def mark_step_failed(self, step: SagaStep, error: str):
        """Mark a step as failed"""
        for step_state in self.steps:
            if step_state.step == step:
                step_state.status = "failed"
                step_state.error = error
                step_state.completed_at = datetime.utcnow()
                break

        self.status = SagaStatus.FAILED
        self.failed_at = datetime.utcnow()
        self.error_message = error
        self.compensation_required = True


# ============================================================================
# Request/Response Models
# ============================================================================

class OrderItemCreate(BaseModel):
    """Request model for order item"""
    product_id: str
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    """Request model for creating an order"""
    user_id: str
    items: List[OrderItemCreate]
    shipping_address: ShippingAddress
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Response model for order"""
    id: str = Field(..., alias="_id")
    order_number: str
    user_id: str
    items: List[OrderItem]
    subtotal: float
    tax: float
    shipping_cost: float
    total: float
    status: OrderStatus
    saga_status: Optional[SagaStatus]
    created_at: datetime
    shipping_address: ShippingAddress

    class Config:
        populate_by_name = True
