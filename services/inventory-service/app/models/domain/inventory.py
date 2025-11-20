"""
Inventory Domain Model
======================

MongoDB document model for inventory.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class WarehouseLocation(BaseModel):
    """Warehouse location"""
    id: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class StockLocation(BaseModel):
    """Stock at a specific location"""
    warehouse_id: str
    warehouse_name: str
    quantity: int
    reserved: int = 0  # Reserved for pending orders
    available: int = 0  # quantity - reserved


class InventoryItem(BaseModel):
    """Inventory item document model"""
    id: Optional[str] = Field(default=None, alias="_id")
    product_id: str
    sku: str

    # Stock information
    total_quantity: int = 0
    total_reserved: int = 0
    total_available: int = 0

    # Stock by location
    locations: List[StockLocation] = []

    # Reorder information
    reorder_point: int = 10
    reorder_quantity: int = 100

    # Status
    is_low_stock: bool = False
    is_out_of_stock: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_restocked_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class StockMovement(BaseModel):
    """Stock movement record (for audit trail)"""
    id: Optional[str] = Field(default=None, alias="_id")
    product_id: str
    warehouse_id: str

    # Movement details
    movement_type: str  # inbound, outbound, transfer, adjustment
    quantity: int
    previous_quantity: int
    new_quantity: int

    # Reference
    reference_type: Optional[str] = None  # order, purchase_order, return
    reference_id: Optional[str] = None

    # User
    performed_by: Optional[str] = None
    notes: Optional[str] = None

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class Warehouse(BaseModel):
    """Warehouse document model"""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    code: str  # Unique warehouse code
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    # Status
    is_active: bool = True

    # Capacity
    capacity: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
