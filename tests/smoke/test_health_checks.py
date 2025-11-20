"""
Smoke Tests - Health Checks
============================

Quick sanity tests to verify all services are up and running.
These tests are run immediately after deployment.
"""

import pytest
import httpx
import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost")


@pytest.mark.asyncio
async def test_api_gateway_health():
    """Test API Gateway health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user_service_health():
    """Test User Service health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/api/users/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_product_service_health():
    """Test Product Service health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/api/products/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_order_service_health():
    """Test Order Service health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/api/orders/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_payment_service_health():
    """Test Payment Service health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/api/payments/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_notification_service_health():
    """Test Notification Service health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/api/notifications/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_inventory_service_health():
    """Test Inventory Service health endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/api/inventory/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_all_services_have_metrics():
    """Verify all services expose Prometheus metrics"""
    services = [
        "/api/users/metrics",
        "/api/products/metrics",
        "/api/orders/metrics",
        "/api/payments/metrics",
        "/api/notifications/metrics",
        "/api/inventory/metrics"
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for service in services:
            response = await client.get(f"{API_BASE_URL}{service}")
            assert response.status_code == 200
            assert "http_requests_total" in response.text
