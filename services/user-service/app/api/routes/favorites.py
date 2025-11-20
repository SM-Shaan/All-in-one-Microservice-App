"""
User Favorites Routes
=====================

Demonstrates SERVICE-TO-SERVICE COMMUNICATION!

This is the magic of microservices:
1. User Service stores favorite product IDs (PostgreSQL)
2. Product Service has product details (MongoDB)
3. We combine them via HTTP calls to show complete data

Flow:
1. User adds product to favorites → Store product_id in PostgreSQL
2. User gets favorites → Fetch product_ids from PostgreSQL → Call Product Service → Combine data
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.db.repositories.favorite_repository import FavoriteRepository
from app.core.http_client import HTTPClient, get_http_client
from app.services.product_service_client import ProductServiceClient

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class FavoriteAdd(BaseModel):
    """Request to add favorite"""
    product_id: str


class FavoriteResponse(BaseModel):
    """
    Response with product details from Product Service.

    This combines data from TWO services:
    - favorite_id, user_id, created_at: From User Service (PostgreSQL)
    - product details: From Product Service (MongoDB) via HTTP
    """
    favorite_id: str
    user_id: str
    product_id: str
    created_at: datetime

    # Product details from Product Service
    product_name: str
    product_description: str
    product_price: float
    product_category: str
    product_image: str | None
    product_in_stock: bool


# ============================================================================
# Dependencies
# ============================================================================

def get_favorite_repo(db: AsyncSession = Depends(get_db)) -> FavoriteRepository:
    """Get favorites repository"""
    return FavoriteRepository(db)


def get_product_client(
    http_client: HTTPClient = Depends(get_http_client)
) -> ProductServiceClient:
    """Get product service client"""
    return ProductServiceClient(http_client)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/{user_id}/favorites",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add product to favorites"
)
async def add_favorite(
    user_id: UUID,
    data: FavoriteAdd,
    repo: FavoriteRepository = Depends(get_favorite_repo),
    product_client: ProductServiceClient = Depends(get_product_client)
):
    """
    Add a product to user's favorites.

    **SERVICE COMMUNICATION EXAMPLE:**
    1. Check if product exists by calling Product Service
    2. If exists, save favorite to User Service database
    3. Return combined data from both services

    Args:
        user_id: User ID
        data: Product ID to favorite
        repo: Favorites repository
        product_client: Product service client

    Returns:
        FavoriteResponse: Favorite with product details
    """
    # Step 1: Call Product Service to verify product exists
    print(f"🔄 Calling Product Service to get product {data.product_id}")

    product = await product_client.get_product(data.product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {data.product_id} not found in Product Service"
        )

    print(f"✅ Product found: {product['name']}")

    # Step 2: Check if already favorited
    is_fav = await repo.is_favorite(user_id, data.product_id)
    if is_fav:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in favorites"
        )

    # Step 3: Save to database
    favorite = await repo.add_favorite(user_id, data.product_id)

    print(f"✅ Favorite saved to User Service database")

    # Step 4: Return combined data
    return FavoriteResponse(
        favorite_id=str(favorite.id),
        user_id=str(user_id),
        product_id=data.product_id,
        created_at=favorite.created_at,
        # Product details from Product Service
        product_name=product["name"],
        product_description=product["description"],
        product_price=product["price"],
        product_category=product["category"],
        product_image=product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
        product_in_stock=product.get("stock", 0) > 0
    )


@router.get(
    "/{user_id}/favorites",
    response_model=List[FavoriteResponse],
    summary="Get user's favorite products"
)
async def get_favorites(
    user_id: UUID,
    repo: FavoriteRepository = Depends(get_favorite_repo),
    product_client: ProductServiceClient = Depends(get_product_client)
):
    """
    Get user's favorite products with details.

    **SERVICE COMMUNICATION EXAMPLE:**
    1. Get favorite product IDs from User Service database
    2. Call Product Service for each product (in parallel!)
    3. Combine and return data

    This is the POWER of microservices - combining data from different services!

    Args:
        user_id: User ID
        repo: Favorites repository
        product_client: Product service client

    Returns:
        List[FavoriteResponse]: List of favorites with product details
    """
    # Step 1: Get favorite records from PostgreSQL
    print(f"📊 Fetching favorites from User Service database")
    favorites = await repo.get_user_favorites(user_id)

    if not favorites:
        return []

    # Step 2: Extract product IDs
    product_ids = [fav.product_id for fav in favorites]
    print(f"🔄 Calling Product Service for {len(product_ids)} products")

    # Step 3: Fetch products from Product Service (IN PARALLEL!)
    products = await product_client.get_products_by_ids(product_ids)

    print(f"✅ Received {len(products)} products from Product Service")

    # Step 4: Create a mapping of product_id -> product_data
    product_map = {prod["_id"]: prod for prod in products}

    # Step 5: Combine data
    result = []
    for favorite in favorites:
        product = product_map.get(favorite.product_id)

        if product:  # Product still exists
            result.append(FavoriteResponse(
                favorite_id=str(favorite.id),
                user_id=str(user_id),
                product_id=favorite.product_id,
                created_at=favorite.created_at,
                product_name=product["name"],
                product_description=product["description"],
                product_price=product["price"],
                product_category=product["category"],
                product_image=product.get("thumbnail") or (product.get("images", [None])[0] if product.get("images") else None),
                product_in_stock=product.get("stock", 0) > 0
            ))
        else:
            # Product was deleted from Product Service
            # In production, you might want to clean this up
            print(f"⚠️ Product {favorite.product_id} no longer exists")

    return result


@router.delete(
    "/{user_id}/favorites/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove product from favorites"
)
async def remove_favorite(
    user_id: UUID,
    product_id: str,
    repo: FavoriteRepository = Depends(get_favorite_repo)
):
    """
    Remove a product from user's favorites.

    Args:
        user_id: User ID
        product_id: Product ID to remove
        repo: Favorites repository
    """
    removed = await repo.remove_favorite(user_id, product_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    return None


@router.get(
    "/{user_id}/favorites/{product_id}/check",
    summary="Check if product is favorited"
)
async def check_favorite(
    user_id: UUID,
    product_id: str,
    repo: FavoriteRepository = Depends(get_favorite_repo)
):
    """
    Check if a product is in user's favorites.

    Returns:
        dict: {"is_favorite": bool}
    """
    is_fav = await repo.is_favorite(user_id, product_id)
    return {"is_favorite": is_fav}


@router.get(
    "/{user_id}/favorites/stats",
    summary="Get favorites statistics"
)
async def get_favorites_stats(
    user_id: UUID,
    repo: FavoriteRepository = Depends(get_favorite_repo)
):
    """
    Get statistics about user's favorites.

    Returns:
        dict: Statistics
    """
    count = await repo.count_favorites(user_id)
    return {
        "total_favorites": count
    }
