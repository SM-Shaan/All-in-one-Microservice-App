"""
Product Events
==============

Events published by Product Service.

Other services can listen to these events:
- Inventory Service: Update stock levels
- Search Service: Update search index
- Analytics Service: Track product changes
- Notification Service: Alert on low stock
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from shared.events.schemas.base import BaseEvent, EventMetadata


# ============================================================================
# Event Payloads
# ============================================================================

class ProductCreatedPayload(BaseModel):
    """Data for product.created event"""
    product_id: str  # MongoDB ObjectId
    name: str
    description: str
    price: float
    category: str
    tags: List[str]
    stock: int
    created_at: datetime


class ProductUpdatedPayload(BaseModel):
    """Data for product.updated event"""
    product_id: str
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    updated_at: datetime


class ProductStockChangedPayload(BaseModel):
    """
    Data for product.stock.changed event.

    This is a specialized event for stock changes.
    """
    product_id: str
    previous_stock: int
    new_stock: int
    change: int  # Positive = added, Negative = removed
    reason: str  # e.g., "sale", "restock", "return"
    changed_at: datetime


class ProductDeletedPayload(BaseModel):
    """Data for product.deleted event"""
    product_id: str
    name: str
    deleted_at: datetime


# ============================================================================
# Event Classes
# ============================================================================

class ProductCreatedEvent(BaseEvent):
    """
    Published when a new product is created.

    Consumers might:
    - Update search index
    - Send notification to admins
    - Update analytics
    """
    payload: ProductCreatedPayload


class ProductUpdatedEvent(BaseEvent):
    """Published when a product is updated"""
    payload: ProductUpdatedPayload


class ProductStockChangedEvent(BaseEvent):
    """
    Published when product stock changes.

    This is important for:
    - Inventory management
    - Low stock alerts
    - Analytics
    """
    payload: ProductStockChangedPayload


class ProductDeletedEvent(BaseEvent):
    """Published when a product is deleted"""
    payload: ProductDeletedPayload


# ============================================================================
# Event Topics
# ============================================================================

class ProductEventTopics:
    """Kafka topic names for product events"""
    PRODUCT_CREATED = "products.product.created"
    PRODUCT_UPDATED = "products.product.updated"
    PRODUCT_STOCK_CHANGED = "products.product.stock_changed"
    PRODUCT_DELETED = "products.product.deleted"
