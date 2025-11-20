"""
Inventory Routes
================

API endpoints for inventory management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas.inventory_schemas import (
    ReserveStockRequest,
    ReleaseStockRequest,
    AdjustStockRequest,
    RestockRequest,
    TransferStockRequest,
    InventoryItemResponse,
    StockCheckResponse,
    StockMovementResponse,
    StockLocationResponse,
    WarehouseResponse,
    InventoryEvent
)
from app.models.domain.inventory import InventoryItem, Warehouse, StockLocation
from app.repositories.inventory_repository import InventoryRepository
from app.core.database import get_database
from shared.events import EventPublisher

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


async def get_inventory_repo(db: AsyncIOMotorDatabase = Depends(get_database)) -> InventoryRepository:
    """Get inventory repository"""
    return InventoryRepository(db)


@router.post("/reserve", response_model=StockCheckResponse)
async def reserve_stock(
    request: ReserveStockRequest,
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """Reserve stock for an order"""
    try:
        success = await repo.reserve_stock(
            product_id=request.product_id,
            quantity=request.quantity,
            warehouse_id=request.warehouse_id,
            order_id=request.order_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock available"
            )

        # Publish event
        event = InventoryEvent(
            event_type="stock_reserved",
            product_id=request.product_id,
            quantity=request.quantity,
            warehouse_id=request.warehouse_id,
            reference_id=request.order_id
        )
        await EventPublisher.publish("inventory-events", event.model_dump())

        return StockCheckResponse(
            product_id=request.product_id,
            available=True,
            available_quantity=0,  # Would need to query again
            requested_quantity=request.quantity
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reserve stock: {str(e)}"
        )


@router.post("/release", response_model=StockCheckResponse)
async def release_stock(
    request: ReleaseStockRequest,
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """Release reserved stock"""
    try:
        success = await repo.release_stock(
            product_id=request.product_id,
            quantity=request.quantity,
            warehouse_id=request.warehouse_id,
            order_id=request.order_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Publish event
        event = InventoryEvent(
            event_type="stock_released",
            product_id=request.product_id,
            quantity=request.quantity,
            warehouse_id=request.warehouse_id,
            reference_id=request.order_id
        )
        await EventPublisher.publish("inventory-events", event.model_dump())

        return StockCheckResponse(
            product_id=request.product_id,
            available=True,
            available_quantity=0,
            requested_quantity=request.quantity
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release stock: {str(e)}"
        )


@router.post("/restock", response_model=InventoryItemResponse)
async def restock_inventory(
    request: RestockRequest,
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """Restock inventory"""
    try:
        # Check if inventory item exists, create if not
        item = await repo.get_by_product_id(request.product_id)
        if not item:
            # Create new inventory item
            from app.models.domain.inventory import InventoryItem, StockLocation
            warehouse = await repo.get_warehouse_by_id(request.warehouse_id) if request.warehouse_id else None
            warehouse_name = warehouse.name if warehouse else "Main Warehouse"

            new_item = InventoryItem(
                product_id=request.product_id,
                sku=request.product_id,  # Use product_id as SKU for now
                locations=[
                    StockLocation(
                        warehouse_id=request.warehouse_id or "main",
                        warehouse_name=warehouse_name,
                        quantity=request.quantity,
                        reserved=0,
                        available=request.quantity
                    )
                ],
                total_quantity=request.quantity,
                total_reserved=0,
                total_available=request.quantity
            )
            item = await repo.create_item(new_item)
        else:
            # Update existing inventory
            success = await repo.update_stock(
                product_id=request.product_id,
                warehouse_id=request.warehouse_id,
                quantity_change=request.quantity,
                movement_type="inbound",
                reference_type="purchase_order" if request.purchase_order_id else None,
                reference_id=request.purchase_order_id,
                notes=request.notes
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update stock"
                )

            # Get updated inventory
            item = await repo.get_by_product_id(request.product_id)

        return InventoryItemResponse(
            id=item.id,
            product_id=item.product_id,
            sku=item.sku,
            total_quantity=item.total_quantity,
            total_reserved=item.total_reserved,
            total_available=item.total_available,
            locations=[
                StockLocationResponse(**loc.model_dump())
                for loc in item.locations
            ],
            reorder_point=item.reorder_point,
            reorder_quantity=item.reorder_quantity,
            is_low_stock=item.is_low_stock,
            is_out_of_stock=item.is_out_of_stock,
            created_at=item.created_at,
            updated_at=item.updated_at,
            last_restocked_at=item.last_restocked_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restock inventory: {str(e)}"
        )


@router.get("/product/{product_id}", response_model=InventoryItemResponse)
async def get_inventory(
    product_id: str,
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """Get inventory for a product"""
    item = await repo.get_by_product_id(product_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory for product {product_id} not found"
        )

    return InventoryItemResponse(
        id=item.id,
        product_id=item.product_id,
        sku=item.sku,
        total_quantity=item.total_quantity,
        total_reserved=item.total_reserved,
        total_available=item.total_available,
        locations=[
            StockLocationResponse(**loc.model_dump())
            for loc in item.locations
        ],
        reorder_point=item.reorder_point,
        reorder_quantity=item.reorder_quantity,
        is_low_stock=item.is_low_stock,
        is_out_of_stock=item.is_out_of_stock,
        created_at=item.created_at,
        updated_at=item.updated_at,
        last_restocked_at=item.last_restocked_at
    )


@router.get("/product/{product_id}/check", response_model=StockCheckResponse)
async def check_stock_availability(
    product_id: str,
    quantity: int,
    warehouse_id: str = None,
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """Check if stock is available"""
    item = await repo.get_by_product_id(product_id)
    if not item:
        return StockCheckResponse(
            product_id=product_id,
            available=False,
            available_quantity=0,
            requested_quantity=quantity
        )

    available_qty = item.total_available
    return StockCheckResponse(
        product_id=product_id,
        available=available_qty >= quantity,
        available_quantity=available_qty,
        requested_quantity=quantity
    )


@router.get("/product/{product_id}/movements", response_model=list[StockMovementResponse])
async def get_stock_movements(
    product_id: str,
    limit: int = 50,
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """Get stock movement history"""
    movements = await repo.get_movements(product_id, limit=limit)

    return [
        StockMovementResponse(
            id=m.id,
            product_id=m.product_id,
            warehouse_id=m.warehouse_id,
            movement_type=m.movement_type,
            quantity=m.quantity,
            previous_quantity=m.previous_quantity,
            new_quantity=m.new_quantity,
            reference_type=m.reference_type,
            reference_id=m.reference_id,
            notes=m.notes,
            created_at=m.created_at
        )
        for m in movements
    ]


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    repo: InventoryRepository = Depends(get_inventory_repo)
):
    """List all warehouses"""
    warehouses = await repo.list_warehouses()

    return [
        WarehouseResponse(
            id=w.id,
            name=w.name,
            code=w.code,
            address=w.address,
            city=w.city,
            state=w.state,
            country=w.country,
            is_active=w.is_active,
            created_at=w.created_at
        )
        for w in warehouses
    ]
