"""
Product Routes
==============

CRUD operations for product management using MongoDB.

Learning Points:
- MongoDB queries with filters
- Full-text search
- Price range filtering
- Category filtering
- Tag-based search
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
import math

from app.db.mongodb import get_products_collection
from app.db.repositories.product_repository import ProductRepository
from app.models.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)

router = APIRouter()


# ============================================================================
# Dependency: Get Repository
# ============================================================================

def get_product_repo():
    """Get product repository instance"""
    collection = get_products_collection()
    return ProductRepository(collection)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new product"
)
async def create_product(
    product_data: ProductCreate,
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Create a new product in the catalog.

    **Example Request:**
    ```json
    {
        "name": "Gaming Laptop",
        "description": "High-performance laptop for gaming",
        "price": 1299.99,
        "category": "Electronics",
        "stock": 50,
        "tags": ["laptop", "gaming"]
    }
    ```
    """
    # Check if SKU already exists
    if product_data.sku:
        existing = await repo.get_by_sku(product_data.sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU {product_data.sku} already exists"
            )

    # Create product
    product = await repo.create(product_data)

    return ProductResponse(**product.model_dump(by_alias=True))


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List products with filters"
)
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of products to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock_only: bool = Query(False, description="Only products with stock"),
    active_only: bool = Query(True, description="Only active products"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Get paginated list of products with advanced filtering.

    **Query Parameters:**
    - `skip`: Pagination offset
    - `limit`: Page size (max 100)
    - `category`: Filter by category (e.g., "Electronics")
    - `search`: Search text in name, description, tags
    - `min_price`: Minimum price filter
    - `max_price`: Maximum price filter
    - `in_stock_only`: Only show products with stock > 0
    - `active_only`: Only show active products
    - `sort_by`: Field to sort by (created_at, price, name, etc.)
    - `sort_order`: "asc" or "desc"

    **Examples:**
    ```
    GET /api/v1/products?category=Electronics&min_price=500&max_price=2000
    GET /api/v1/products?search=laptop&in_stock_only=true
    GET /api/v1/products?sort_by=price&sort_order=asc
    ```
    """
    products, total = await repo.list(
        skip=skip,
        limit=limit,
        category=category,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return ProductListResponse(
        products=[ProductResponse(**p.model_dump(by_alias=True)) for p in products],
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
        total_pages=math.ceil(total / limit) if limit > 0 else 0
    )


@router.get(
    "/featured",
    response_model=List[ProductResponse],
    summary="Get featured products"
)
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50),
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Get featured products (shown on homepage).

    Sorted by average rating.
    """
    products = await repo.get_featured(limit=limit)
    return [ProductResponse(**p.model_dump(by_alias=True)) for p in products]


@router.get(
    "/category/{category}",
    response_model=List[ProductResponse],
    summary="Get products by category"
)
async def get_products_by_category(
    category: str,
    limit: int = Query(20, ge=1, le=100),
    repo: ProductRepository = Depends(get_product_repo)
):
    """Get products in a specific category"""
    products = await repo.get_by_category(category, limit=limit)
    return [ProductResponse(**p.model_dump(by_alias=True)) for p in products]


@router.get(
    "/search/tags",
    response_model=List[ProductResponse],
    summary="Search products by tags"
)
async def search_by_tags(
    tags: List[str] = Query(..., description="Tags to search for"),
    limit: int = Query(20, ge=1, le=100),
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Search products by tags.

    **Example:**
    ```
    GET /api/v1/products/search/tags?tags=laptop&tags=gaming
    ```
    """
    products = await repo.search_by_tags(tags, limit=limit)
    return [ProductResponse(**p.model_dump(by_alias=True)) for p in products]


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID"
)
async def get_product(
    product_id: str,
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Get a specific product by ID.

    **Note:** Product ID is MongoDB's ObjectId (24-character hex string)
    """
    product = await repo.get_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    return ProductResponse(**product.model_dump(by_alias=True))


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product"
)
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Update product information.

    Only provided fields will be updated.
    """
    # Check if product exists
    existing = await repo.get_by_id(product_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Update product
    updated_product = await repo.update(product_id, update_data)

    return ProductResponse(**updated_product.model_dump(by_alias=True))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product"
)
async def delete_product(
    product_id: str,
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Delete a product from the catalog.

    **Warning:** This is a hard delete. The product is permanently removed.

    In production, consider soft delete (set is_active=False).
    """
    deleted = await repo.delete(product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    return None


@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponse,
    summary="Update product stock"
)
async def update_stock(
    product_id: str,
    quantity_change: int = Query(..., description="Amount to add/subtract from stock"),
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Update product stock level.

    **Examples:**
    - Add 10 items: `PATCH /products/{id}/stock?quantity_change=10`
    - Remove 5 items: `PATCH /products/{id}/stock?quantity_change=-5`

    This is useful for inventory management.
    """
    updated_product = await repo.update_stock(product_id, quantity_change)

    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    return ProductResponse(**updated_product.model_dump(by_alias=True))


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    summary="Get product by SKU"
)
async def get_product_by_sku(
    sku: str,
    repo: ProductRepository = Depends(get_product_repo)
):
    """
    Get a product by its SKU (Stock Keeping Unit).

    Useful for barcode scanning systems.
    """
    product = await repo.get_by_sku(sku)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with SKU {sku} not found"
        )

    return ProductResponse(**product.model_dump(by_alias=True))
