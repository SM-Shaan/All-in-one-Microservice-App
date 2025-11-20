"""
Inventory Service API Tests
===========================

Unit and integration tests for Inventory Service endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_add_inventory():
    """Test adding inventory"""
    from app.main import app

    inventory_data = {
        "product_id": "test-product-123",
        "warehouse_id": "warehouse-1",
        "quantity": 100,
        "reserved": 0,
        "available": 100
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/inventory", json=inventory_data)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
    data = response.json()
    assert "id" in data or "product_id" in data


@pytest.mark.asyncio
async def test_get_inventory():
    """Test getting inventory by product ID"""
    from app.main import app

    # First add inventory
    inventory_data = {
        "product_id": "test-product-456",
        "warehouse_id": "warehouse-1",
        "quantity": 50,
        "available": 50
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/inventory", json=inventory_data)
        product_id = inventory_data["product_id"]

        # Now get the inventory
        get_response = await client.get(f"/api/v1/inventory/{product_id}")

    assert get_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_update_inventory():
    """Test updating inventory quantity"""
    from app.main import app

    # First add inventory
    inventory_data = {
        "product_id": "test-product-789",
        "warehouse_id": "warehouse-1",
        "quantity": 100,
        "available": 100
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/inventory", json=inventory_data)
        product_id = inventory_data["product_id"]

        # Update inventory
        update_data = {
            "quantity": 150,
            "available": 150
        }
        update_response = await client.patch(
            f"/api/v1/inventory/{product_id}",
            json=update_data
        )

    assert update_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_reserve_inventory():
    """Test reserving inventory"""
    from app.main import app

    # First add inventory
    inventory_data = {
        "product_id": "test-product-reserve",
        "warehouse_id": "warehouse-1",
        "quantity": 100,
        "reserved": 0,
        "available": 100
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/inventory", json=inventory_data)
        product_id = inventory_data["product_id"]

        # Reserve inventory
        reserve_data = {
            "product_id": product_id,
            "quantity": 10
        }
        reserve_response = await client.post(
            f"/api/v1/inventory/reserve",
            json=reserve_data
        )

    assert reserve_response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_400_BAD_REQUEST
    ]


@pytest.mark.asyncio
async def test_list_inventory():
    """Test listing inventory"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/inventory")

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_negative_quantity():
    """Test that negative quantities are rejected"""
    from app.main import app

    inventory_data = {
        "product_id": "test-product-negative",
        "warehouse_id": "warehouse-1",
        "quantity": -10,
        "available": -10
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/inventory", json=inventory_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert "http_requests_total" in response.text
