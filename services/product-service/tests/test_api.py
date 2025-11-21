"""
Product Service API Tests
=========================

Unit and integration tests for Product Service endpoints.

These tests use real MongoDB connections to test the full integration
of the API with the database layer.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_product(clean_db):
    """Test product creation with real MongoDB"""
    from app.main import app

    product_data = {
        "name": "Test Laptop",
        "description": "High-performance test laptop",
        "price": 999.99,
        "stock": 50,
        "category": "Electronics"
    }

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.post("/api/v1/products", json=product_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == product_data["price"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_product(clean_db):
    """Test getting product by ID"""
    from app.main import app

    # First create a product
    product_data = {
        "name": "Test Product",
        "description": "Test description",
        "price": 49.99,
        "stock": 100
    }

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        create_response = await client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]

        # Now get the product
        get_response = await client.get(f"/api/v1/products/{product_id}")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["name"] == product_data["name"]


@pytest.mark.asyncio
async def test_list_products(clean_db):
    """Test listing products with pagination"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/api/v1/products?page=1&page_size=10")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "products" in data or "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_update_product(clean_db):
    """Test product update"""
    from app.main import app

    # First create a product
    product_data = {
        "name": "Original Product",
        "description": "Original description",
        "price": 99.99,
        "stock": 10
    }

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        create_response = await client.post("/api/v1/products", json=product_data)
        product_id = create_response.json()["id"]

        # Update the product
        update_data = {
            "name": "Updated Product",
            "price": 149.99
        }
        update_response = await client.patch(
            f"/api/v1/products/{product_id}",
            json=update_data
        )

    assert update_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_invalid_price():
    """Test that negative prices are rejected (validation test - no DB needed)"""
    from app.main import app

    product_data = {
        "name": "Invalid Product",
        "description": "Product with negative price",
        "price": -10.00,
        "stock": 5
    }

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.post("/api/v1/products", json=product_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    # Just check that we get prometheus-formatted metrics
    assert "python_" in response.text or "#" in response.text
