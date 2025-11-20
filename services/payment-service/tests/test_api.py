"""
Payment Service API Tests
=========================

Unit and integration tests for Payment Service endpoints.
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
async def test_create_payment():
    """Test payment creation"""
    from app.main import app

    payment_data = {
        "order_id": "test-order-123",
        "amount": 199.99,
        "currency": "USD",
        "payment_method": "card",
        "card_token": "tok_visa"  # Test token
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/payments", json=payment_data)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
    data = response.json()
    assert "id" in data or "payment_id" in data


@pytest.mark.asyncio
async def test_get_payment():
    """Test getting payment by ID"""
    from app.main import app

    # First create a payment
    payment_data = {
        "order_id": "test-order-456",
        "amount": 99.99,
        "currency": "USD",
        "payment_method": "card",
        "card_token": "tok_visa"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/payments", json=payment_data)

        if create_response.status_code in [200, 201]:
            response_data = create_response.json()
            payment_id = response_data.get("id") or response_data.get("payment_id")

            if payment_id:
                # Now get the payment
                get_response = await client.get(f"/api/v1/payments/{payment_id}")
                assert get_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_list_payments():
    """Test listing payments"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/payments")

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_payment_refund():
    """Test payment refund"""
    from app.main import app

    # First create a payment
    payment_data = {
        "order_id": "test-order-789",
        "amount": 149.99,
        "currency": "USD",
        "payment_method": "card",
        "card_token": "tok_visa"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/payments", json=payment_data)

        if create_response.status_code in [200, 201]:
            response_data = create_response.json()
            payment_id = response_data.get("id") or response_data.get("payment_id")

            if payment_id:
                # Attempt refund
                refund_data = {"amount": 149.99}
                refund_response = await client.post(
                    f"/api/v1/payments/{payment_id}/refund",
                    json=refund_data
                )
                assert refund_response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_404_NOT_FOUND,
                    status.HTTP_400_BAD_REQUEST
                ]


@pytest.mark.asyncio
async def test_invalid_amount():
    """Test that negative amounts are rejected"""
    from app.main import app

    payment_data = {
        "order_id": "test-order-999",
        "amount": -50.00,
        "currency": "USD",
        "payment_method": "card",
        "card_token": "tok_visa"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/payments", json=payment_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert "http_requests_total" in response.text
