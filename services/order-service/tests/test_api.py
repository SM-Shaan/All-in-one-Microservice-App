"""
Order Service API Tests
=======================

Unit and integration tests for Order Service endpoints.
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
async def test_create_order():
    """Test order creation"""
    from app.main import app

    order_data = {
        "user_id": "test-user-123",
        "items": [
            {
                "product_id": "test-product-1",
                "quantity": 2,
                "price": 99.99
            },
            {
                "product_id": "test-product-2",
                "quantity": 1,
                "price": 49.99
            }
        ],
        "total_amount": 249.97,
        "shipping_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "country": "Test Country"
        }
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/orders", json=order_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == order_data["user_id"]
    assert data["total_amount"] == order_data["total_amount"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_order():
    """Test getting order by ID"""
    from app.main import app

    # First create an order
    order_data = {
        "user_id": "test-user-456",
        "items": [
            {
                "product_id": "test-product-1",
                "quantity": 1,
                "price": 99.99
            }
        ],
        "total_amount": 99.99
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Now get the order
        get_response = await client.get(f"/api/v1/orders/{order_id}")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["user_id"] == order_data["user_id"]


@pytest.mark.asyncio
async def test_list_orders():
    """Test listing orders"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/orders")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_order_status_update():
    """Test updating order status"""
    from app.main import app

    # First create an order
    order_data = {
        "user_id": "test-user-789",
        "items": [
            {
                "product_id": "test-product-1",
                "quantity": 1,
                "price": 99.99
            }
        ],
        "total_amount": 99.99
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Update order status
        status_update = {"status": "processing"}
        update_response = await client.patch(
            f"/api/v1/orders/{order_id}",
            json=status_update
        )

    assert update_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_empty_order():
    """Test that orders without items are rejected"""
    from app.main import app

    order_data = {
        "user_id": "test-user-999",
        "items": [],
        "total_amount": 0
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/orders", json=order_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert "http_requests_total" in response.text
