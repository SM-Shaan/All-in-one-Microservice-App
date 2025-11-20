"""
User Service API Tests
======================

Unit and integration tests for User Service endpoints.
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
async def test_create_user():
    """Test user creation"""
    from app.main import app

    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/users", json=user_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "hashed_password" not in data  # Password should not be in response


@pytest.mark.asyncio
async def test_get_user():
    """Test getting user by ID"""
    from app.main import app

    # First create a user
    user_data = {
        "email": "getuser@example.com",
        "full_name": "Get User Test",
        "password": "password123"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]

        # Now get the user
        get_response = await client.get(f"/api/v1/users/{user_id}")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_duplicate_email():
    """Test that duplicate emails are rejected"""
    from app.main import app

    user_data = {
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "password": "password123"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create first user
        response1 = await client.post("/api/v1/users", json=user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create duplicate
        response2 = await client.post("/api/v1/users", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_invalid_email():
    """Test that invalid emails are rejected"""
    from app.main import app

    user_data = {
        "email": "not-an-email",
        "full_name": "Invalid Email User",
        "password": "password123"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/users", json=user_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_user_list():
    """Test listing users with pagination"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/users?page=1&page_size=10")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["users"], list)


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that metrics endpoint is accessible"""
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert "http_requests_total" in response.text
