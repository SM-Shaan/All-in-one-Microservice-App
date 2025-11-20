"""
Order Routes
============

API endpoints for order management.
"""

from fastapi import APIRouter, HTTPException, status, Body
from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel

from app.models.order import (
    OrderCreate,
    OrderResponse,
    Order,
    OrderItem,
    OrderStatus,
    SagaStatus
)


class StatusUpdate(BaseModel):
    """Request model for status updates"""
    status: OrderStatus

router = APIRouter()

# In-memory storage (replace with MongoDB in production)
orders_db = {}


# ============================================================================
# Helper Functions
# ============================================================================

def generate_order_number() -> str:
    """Generate unique order number"""
    return f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def calculate_order_totals(items: List[OrderItem]) -> dict:
    """Calculate order totals"""
    subtotal = sum(item.subtotal for item in items)
    tax = subtotal * 0.08  # 8% tax
    shipping_cost = 10.0 if subtotal < 100 else 0.0  # Free shipping over $100
    total = subtotal + tax + shipping_cost

    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "shipping_cost": round(shipping_cost, 2),
        "total": round(total, 2)
    }


# ============================================================================
# Order Endpoints
# ============================================================================

@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new order"
)
async def create_order(order_data: OrderCreate):
    """
    Create a new order.

    This will:
    1. Generate order number
    2. Calculate prices
    3. Create order with PENDING status
    4. Return order details

    Note: In production, this would trigger a saga workflow to:
    - Verify user exists
    - Check product availability
    - Reserve inventory
    - Process payment
    """
    order_id = str(uuid.uuid4())

    # Mock: Get product details and calculate subtotals
    # In production, would call Product Service
    items = []
    for item in order_data.items:
        # Mock product data
        product_name = f"Product {item.product_id}"
        unit_price = 29.99  # Would fetch from Product Service
        subtotal = unit_price * item.quantity

        items.append(OrderItem(
            product_id=item.product_id,
            product_name=product_name,
            quantity=item.quantity,
            unit_price=unit_price,
            subtotal=subtotal
        ))

    # Calculate totals
    totals = calculate_order_totals(items)

    # Create order
    order = Order(
        _id=order_id,
        order_number=generate_order_number(),
        user_id=order_data.user_id,
        items=items,
        subtotal=totals["subtotal"],
        tax=totals["tax"],
        shipping_cost=totals["shipping_cost"],
        total=totals["total"],
        shipping_address=order_data.shipping_address,
        status=OrderStatus.PENDING,
        saga_id=str(uuid.uuid4()),
        saga_status=SagaStatus.STARTED,
        notes=order_data.notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Store order
    orders_db[order_id] = order

    return OrderResponse(
        _id=order_id,
        order_number=order.order_number,
        user_id=order.user_id,
        items=order.items,
        subtotal=order.subtotal,
        tax=order.tax,
        shipping_cost=order.shipping_cost,
        total=order.total,
        status=order.status,
        saga_status=order.saga_status,
        created_at=order.created_at,
        shipping_address=order.shipping_address
    )


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List all orders"
)
async def list_orders(
    user_id: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 10
):
    """
    List orders with optional filters.

    Args:
        user_id: Filter by user ID
        status: Filter by order status
        skip: Number of records to skip
        limit: Maximum number of records to return
    """
    orders = list(orders_db.values())

    # Apply filters
    if user_id:
        orders = [o for o in orders if o.user_id == user_id]
    if status:
        orders = [o for o in orders if o.status == status]

    # Sort by created_at descending
    orders.sort(key=lambda x: x.created_at, reverse=True)

    # Pagination
    orders = orders[skip:skip + limit]

    return [
        OrderResponse(
            _id=o.id,
            order_number=o.order_number,
            user_id=o.user_id,
            items=o.items,
            subtotal=o.subtotal,
            tax=o.tax,
            shipping_cost=o.shipping_cost,
            total=o.total,
            status=o.status,
            saga_status=o.saga_status,
            created_at=o.created_at,
            shipping_address=o.shipping_address
        )
        for o in orders
    ]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID"
)
async def get_order(order_id: str):
    """Get a specific order by ID"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )

    order = orders_db[order_id]
    return OrderResponse(
        _id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        items=order.items,
        subtotal=order.subtotal,
        tax=order.tax,
        shipping_cost=order.shipping_cost,
        total=order.total,
        status=order.status,
        saga_status=order.saga_status,
        created_at=order.created_at,
        shipping_address=order.shipping_address
    )


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status"
)
async def update_order_status(
    order_id: str,
    status_update: StatusUpdate
):
    """
    Update order status.

    Valid transitions:
    - PENDING → CONFIRMED
    - PENDING → CANCELLED
    - CONFIRMED → CANCELLED (with conditions)
    """
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )

    order = orders_db[order_id]
    new_status = status_update.status

    # Update status
    order.status = new_status
    order.updated_at = datetime.utcnow()

    if new_status == OrderStatus.CONFIRMED:
        order.confirmed_at = datetime.utcnow()
        order.saga_status = SagaStatus.COMPLETED
    elif new_status == OrderStatus.CANCELLED:
        order.cancelled_at = datetime.utcnow()
        order.saga_status = SagaStatus.COMPENSATED

    return OrderResponse(
        _id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        items=order.items,
        subtotal=order.subtotal,
        tax=order.tax,
        shipping_cost=order.shipping_cost,
        total=order.total,
        status=order.status,
        saga_status=order.saga_status,
        created_at=order.created_at,
        shipping_address=order.shipping_address
    )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order"
)
async def cancel_order(
    order_id: str,
    reason: Optional[str] = None
):
    """Cancel an order"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )

    order = orders_db[order_id]

    # Check if order can be cancelled
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already cancelled"
        )

    # Cancel order
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    order.cancellation_reason = reason
    order.saga_status = SagaStatus.COMPENSATING

    return OrderResponse(
        _id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        items=order.items,
        subtotal=order.subtotal,
        tax=order.tax,
        shipping_cost=order.shipping_cost,
        total=order.total,
        status=order.status,
        saga_status=order.saga_status,
        created_at=order.created_at,
        shipping_address=order.shipping_address
    )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete order"
)
async def delete_order(order_id: str):
    """Delete an order (admin only)"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )

    del orders_db[order_id]
    return None
