"""
End-to-End Tests - Order Flow
==============================

Complete user journey tests from user registration to order completion.
Tests the entire flow across multiple services.
"""

import pytest
import httpx
import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost")


@pytest.mark.asyncio
async def test_complete_order_flow():
    """
    Test complete order flow:
    1. Register user
    2. Login
    3. Create product
    4. Create order
    5. Process payment
    6. Verify notifications
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Register user
        user_data = {
            "email": f"e2e-test-{os.urandom(4).hex()}@example.com",
            "full_name": "E2E Test User",
            "password": "TestPassword123!"
        }

        user_response = await client.post(
            f"{API_BASE_URL}/api/users",
            json=user_data
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        assert user_id is not None

        # 2. Login
        login_response = await client.post(
            f"{API_BASE_URL}/api/users/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        assert token is not None

        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create product
        product_data = {
            "name": "E2E Test Product",
            "description": "Product for end-to-end testing",
            "price": 99.99,
            "stock": 10
        }

        product_response = await client.post(
            f"{API_BASE_URL}/api/products",
            json=product_data,
            headers=headers
        )
        assert product_response.status_code == 201
        product_id = product_response.json()["id"]
        assert product_id is not None

        # 4. Create order
        order_data = {
            "user_id": user_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "price": 99.99
                }
            ],
            "total_amount": 199.98
        }

        order_response = await client.post(
            f"{API_BASE_URL}/api/orders",
            json=order_data,
            headers=headers
        )
        assert order_response.status_code == 201
        order_id = order_response.json()["id"]
        assert order_id is not None

        # 5. Process payment
        payment_data = {
            "order_id": order_id,
            "amount": 199.98,
            "payment_method": "card",
            "card_token": "tok_visa"  # Test token
        }

        payment_response = await client.post(
            f"{API_BASE_URL}/api/payments",
            json=payment_data,
            headers=headers
        )
        assert payment_response.status_code in [200, 201]
        payment_id = payment_response.json()["id"]
        assert payment_id is not None

        # 6. Verify order status
        order_status_response = await client.get(
            f"{API_BASE_URL}/api/orders/{order_id}",
            headers=headers
        )
        assert order_status_response.status_code == 200
        order_status = order_status_response.json()
        assert order_status["status"] in ["completed", "processing", "confirmed"]


@pytest.mark.asyncio
async def test_user_registration_and_profile():
    """Test user registration and profile retrieval"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Register user
        user_data = {
            "email": f"profile-test-{os.urandom(4).hex()}@example.com",
            "full_name": "Profile Test User",
            "password": "ProfileTest123!"
        }

        register_response = await client.post(
            f"{API_BASE_URL}/api/users",
            json=user_data
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        # Login
        login_response = await client.post(
            f"{API_BASE_URL}/api/users/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Get profile
        profile_response = await client.get(
            f"{API_BASE_URL}/api/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == user_data["email"]
        assert profile["full_name"] == user_data["full_name"]


@pytest.mark.asyncio
async def test_product_catalog_and_search():
    """Test product catalog browsing and search"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Get all products
        products_response = await client.get(f"{API_BASE_URL}/api/products")
        assert products_response.status_code == 200

        # Create test product
        product_data = {
            "name": "Search Test Product",
            "description": "Product for search testing",
            "price": 49.99,
            "stock": 25
        }

        create_response = await client.post(
            f"{API_BASE_URL}/api/products",
            json=product_data
        )
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]

        # Get specific product
        get_response = await client.get(
            f"{API_BASE_URL}/api/products/{product_id}"
        )
        assert get_response.status_code == 200
        product = get_response.json()
        assert product["name"] == product_data["name"]


@pytest.mark.asyncio
async def test_inventory_management():
    """Test inventory tracking and updates"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Create product
        product_data = {
            "name": "Inventory Test Product",
            "description": "Product for inventory testing",
            "price": 75.00,
            "stock": 100
        }

        product_response = await client.post(
            f"{API_BASE_URL}/api/products",
            json=product_data
        )
        assert product_response.status_code == 201
        product_id = product_response.json()["id"]

        # Check inventory
        inventory_response = await client.get(
            f"{API_BASE_URL}/api/inventory/{product_id}"
        )
        assert inventory_response.status_code in [200, 404]  # May not exist yet

        # Update inventory
        inventory_update = {
            "product_id": product_id,
            "quantity": 50,
            "warehouse_id": "warehouse-1"
        }

        update_response = await client.post(
            f"{API_BASE_URL}/api/inventory",
            json=inventory_update
        )
        assert update_response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling across services"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test invalid user creation
        invalid_user = {
            "email": "not-an-email",
            "full_name": "Invalid User",
            "password": "123"
        }

        response = await client.post(
            f"{API_BASE_URL}/api/users",
            json=invalid_user
        )
        assert response.status_code == 422

        # Test non-existent resource
        response = await client.get(
            f"{API_BASE_URL}/api/products/non-existent-id"
        )
        assert response.status_code == 404

        # Test unauthorized access
        response = await client.post(
            f"{API_BASE_URL}/api/orders",
            json={"items": []}
        )
        assert response.status_code in [401, 403]
