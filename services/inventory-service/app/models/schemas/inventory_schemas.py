"""
Inventory Schemas
=================

Pydantic schemas for inventory API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class ReserveStockRequest(BaseModel):
    """Request to reserve stock"""
    product_id: str
    quantity: int = Field(gt=0)
    order_id: str
    warehouse_id: Optional[str] = None


class ReleaseStockRequest(BaseModel):
    """Request to release reserved stock"""
    product_id: str
    quantity: int = Field(gt=0)
    order_id: str
    warehouse_id: Optional[str] = None


class AdjustStockRequest(BaseModel):
    """Request to adjust stock"""
    product_id: str
    warehouse_id: str
    quantity: int  # Can be positive or negative
    reason: str
    notes: Optional[str] = None


class RestockRequest(BaseModel):
    """Request to restock inventory"""
    product_id: str
    warehouse_id: str
    quantity: int = Field(gt=0)
    purchase_order_id: Optional[str] = None
    notes: Optional[str] = None


class TransferStockRequest(BaseModel):
    """Request to transfer stock between warehouses"""
    product_id: str
    from_warehouse_id: str
    to_warehouse_id: str
    quantity: int = Field(gt=0)
    notes: Optional[str] = None


# ============================================================================
# Response Schemas
# ============================================================================

class StockLocationResponse(BaseModel):
    """Stock location response"""
    warehouse_id: str
    warehouse_name: str
    quantity: int
    reserved: int
    available: int


class InventoryItemResponse(BaseModel):
    """Inventory item response"""
    id: str
    product_id: str
    sku: str
    total_quantity: int
    total_reserved: int
    total_available: int
    locations: List[StockLocationResponse]
    reorder_point: int
    reorder_quantity: int
    is_low_stock: bool
    is_out_of_stock: bool
    created_at: datetime
    updated_at: datetime
    last_restocked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockCheckResponse(BaseModel):
    """Stock availability check response"""
    product_id: str
    available: bool
    available_quantity: int
    requested_quantity: int


class StockMovementResponse(BaseModel):
    """Stock movement response"""
    id: str
    product_id: str
    warehouse_id: str
    movement_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WarehouseResponse(BaseModel):
    """Warehouse response"""
    id: str
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Event Schemas
# ============================================================================

class InventoryEvent(BaseModel):
    """Inventory event for Kafka"""
    event_type: str  # stock_reserved, stock_released, stock_low, stock_out
    product_id: str
    quantity: int
    warehouse_id: Optional[str] = None
    reference_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
