"""
Integration Tests - Service Communication
=========================================

Tests for inter-service communication.
"""

import pytest
import httpx


BASE_URL = "http://localhost"


@pytest.mark.asyncio
async def test_user_service_health():
    """Test User Service health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}:8001/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_product_service_health():
    """Test Product Service health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}:8002/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_user_and_product():
    """Test creating user and product"""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Create user
        user_response = await client.post(
            f"{BASE_URL}:8001/api/v1/users",
            json={
                "email": "integration@test.com",
                "full_name": "Integration Test",
                "password": "password123"
            }
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Create product
        product_response = await client.post(
            f"{BASE_URL}:8002/api/v1/products",
            json={
                "name": "Test Product",
                "description": "Integration test product",
                "price": 99.99,
                "stock": 10
            }
        )
        assert product_response.status_code == 201
        product_id = product_response.json()["id"]

    assert user_id is not None
    assert product_id is not None


@pytest.mark.asyncio
async def test_api_gateway_routing():
    """Test that API Gateway routes to services correctly"""
    async with httpx.AsyncClient() as client:
        # Test user service through gateway
        user_response = await client.get(f"{BASE_URL}/api/users")
        assert user_response.status_code in [200, 404]  # 404 if no users yet

        # Test product service through gateway
        product_response = await client.get(f"{BASE_URL}/api/products")
        assert product_response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_metrics_endpoints():
    """Test that all services expose metrics"""
    services = [8001, 8002, 8003, 8004, 8005, 8006]

    async with httpx.AsyncClient() as client:
        for port in services:
            response = await client.get(f"{BASE_URL}:{port}/metrics")
            assert response.status_code == 200
            assert "http_requests_total" in response.text
