"""
Inventory Repository
====================

Repository for inventory data access.
"""

from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.domain.inventory import InventoryItem, StockMovement, Warehouse, StockLocation


class InventoryRepository:
    """Repository for inventory operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.inventory
        self.movements_collection = db.stock_movements
        self.warehouses_collection = db.warehouses

    async def create_item(self, item: InventoryItem) -> InventoryItem:
        """Create inventory item"""
        item_dict = item.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(item_dict)
        item.id = str(result.inserted_id)
        return item

    async def get_by_product_id(self, product_id: str) -> Optional[InventoryItem]:
        """Get inventory by product ID"""
        doc = await self.collection.find_one({"product_id": product_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            return InventoryItem(**doc)
        return None

    async def update_stock(
        self,
        product_id: str,
        warehouse_id: str,
        quantity_change: int,
        movement_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update stock and record movement"""
        item = await self.get_by_product_id(product_id)
        if not item:
            return False

        # Find location
        location_idx = None
        for idx, loc in enumerate(item.locations):
            if loc.warehouse_id == warehouse_id:
                location_idx = idx
                break

        if location_idx is None:
            # Create new location
            warehouse = await self.get_warehouse_by_id(warehouse_id)
            new_location = StockLocation(
                warehouse_id=warehouse_id,
                warehouse_name=warehouse.name if warehouse else "Unknown",
                quantity=max(0, quantity_change),
                reserved=0,
                available=max(0, quantity_change)
            )
            item.locations.append(new_location)
            previous_qty = 0
        else:
            # Update existing location
            previous_qty = item.locations[location_idx].quantity
            item.locations[location_idx].quantity = max(0, previous_qty + quantity_change)
            item.locations[location_idx].available = item.locations[location_idx].quantity - item.locations[location_idx].reserved

        # Recalculate totals
        item.total_quantity = sum(loc.quantity for loc in item.locations)
        item.total_reserved = sum(loc.reserved for loc in item.locations)
        item.total_available = item.total_quantity - item.total_reserved

        # Update flags
        item.is_low_stock = item.total_available <= item.reorder_point
        item.is_out_of_stock = item.total_available == 0

        if movement_type == "inbound":
            item.last_restocked_at = datetime.utcnow()

        item.updated_at = datetime.utcnow()

        # Update database
        await self.collection.update_one(
            {"product_id": product_id},
            {"$set": item.model_dump(by_alias=True, exclude={"id"})}
        )

        # Record movement
        movement = StockMovement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=abs(quantity_change),
            previous_quantity=previous_qty,
            new_quantity=max(0, previous_qty + quantity_change),
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )
        await self._record_movement(movement)

        return True

    async def reserve_stock(
        self,
        product_id: str,
        quantity: int,
        warehouse_id: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> bool:
        """Reserve stock for an order"""
        item = await self.get_by_product_id(product_id)
        if not item:
            return False

        # Find best warehouse if not specified
        if not warehouse_id:
            for loc in sorted(item.locations, key=lambda x: x.available, reverse=True):
                if loc.available >= quantity:
                    warehouse_id = loc.warehouse_id
                    break

        if not warehouse_id:
            return False

        # Reserve stock
        for loc in item.locations:
            if loc.warehouse_id == warehouse_id:
                if loc.available < quantity:
                    return False
                loc.reserved += quantity
                loc.available -= quantity
                break

        # Update totals
        item.total_reserved += quantity
        item.total_available -= quantity

        await self.collection.update_one(
            {"product_id": product_id},
            {"$set": item.model_dump(by_alias=True, exclude={"id"})}
        )

        return True

    async def release_stock(
        self,
        product_id: str,
        quantity: int,
        warehouse_id: str,
        order_id: Optional[str] = None
    ) -> bool:
        """Release reserved stock"""
        item = await self.get_by_product_id(product_id)
        if not item:
            return False

        for loc in item.locations:
            if loc.warehouse_id == warehouse_id:
                loc.reserved = max(0, loc.reserved - quantity)
                loc.available = loc.quantity - loc.reserved
                break

        item.total_reserved = max(0, item.total_reserved - quantity)
        item.total_available = item.total_quantity - item.total_reserved

        await self.collection.update_one(
            {"product_id": product_id},
            {"$set": item.model_dump(by_alias=True, exclude={"id"})}
        )

        return True

    async def _record_movement(self, movement: StockMovement):
        """Record stock movement"""
        movement_dict = movement.model_dump(by_alias=True, exclude={"id"})
        await self.movements_collection.insert_one(movement_dict)

    async def get_movements(
        self,
        product_id: str,
        limit: int = 50
    ) -> List[StockMovement]:
        """Get stock movements for a product"""
        cursor = self.movements_collection.find(
            {"product_id": product_id}
        ).sort("created_at", -1).limit(limit)

        movements = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            movements.append(StockMovement(**doc))
        return movements

    # Warehouse methods
    async def create_warehouse(self, warehouse: Warehouse) -> Warehouse:
        """Create warehouse"""
        warehouse_dict = warehouse.model_dump(by_alias=True, exclude={"id"})
        result = await self.warehouses_collection.insert_one(warehouse_dict)
        warehouse.id = str(result.inserted_id)
        return warehouse

    async def get_warehouse_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """Get warehouse by ID"""
        try:
            doc = await self.warehouses_collection.find_one({"_id": ObjectId(warehouse_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Warehouse(**doc)
        except Exception:
            pass
        return None

    async def list_warehouses(self) -> List[Warehouse]:
        """List all warehouses"""
        cursor = self.warehouses_collection.find({}).sort("name", 1)
        warehouses = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            warehouses.append(Warehouse(**doc))
        return warehouses
