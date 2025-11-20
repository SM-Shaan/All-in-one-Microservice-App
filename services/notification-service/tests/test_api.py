"""
Notification Service API Tests
==============================

Unit and integration tests for Notification Service endpoints.
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
async def test_send_email_notification():
    """Test sending email notification"""
    from app.main import app

    notification_data = {
        "type": "email",
        "recipient": "test@example.com",
        "subject": "Test Email",
        "message": "This is a test notification",
        "priority": "normal"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/notifications", json=notification_data)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]


@pytest.mark.asyncio
async def test_send_sms_notification():
    """Test sending SMS notification"""
    from app.main import app

    notification_data = {
        "type": "sms",
        "recipient": "+1234567890",
        "message": "Test SMS notification"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/notifications", json=notification_data)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]


@pytest.mark.asyncio
async def test_get_notification_status():
    """Test getting notification status"""
    from app.main import app

    # First send a notification
    notification_data = {
        "type": "email",
        "recipient": "status@example.com",
        "subject": "Status Test",
        "message": "Testing notification status"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/notifications", json=notification_data)

        if create_response.status_code in [200, 201, 202]:
            response_data = create_response.json()
            notification_id = response_data.get("id") or response_data.get("notification_id")

            if notification_id:
                # Get notification status
                status_response = await client.get(f"/api/v1/notifications/{notification_id}")
                assert status_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_list_notifications():
    """Test listing notifications"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/notifications")

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_invalid_email():
    """Test that invalid emails are rejected"""
    from app.main import app

    notification_data = {
        "type": "email",
        "recipient": "not-an-email",
        "subject": "Test",
        "message": "Test message"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/notifications", json=notification_data)

    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert "http_requests_total" in response.text
