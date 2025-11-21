"""
Pytest Configuration
====================

Shared fixtures and configuration for tests.
"""

import sys
from pathlib import Path
import pytest
import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# MongoDB Configuration for Tests
# ============================================================================

# Use test MongoDB URL - check environment or use default
TEST_MONGODB_URL = os.getenv(
    "TEST_MONGODB_URL",
    "mongodb://admin:admin123@localhost:27018"
)
TEST_DB_NAME = "test_products"

# Test MongoDB client
test_mongodb_client: AsyncIOMotorClient = None


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Setup test MongoDB connection before running tests.
    This runs once per test session.
    """
    global test_mongodb_client

    test_mongodb_client = AsyncIOMotorClient(
        TEST_MONGODB_URL,
        maxPoolSize=10,
        minPoolSize=2,
        serverSelectionTimeoutMS=5000,
    )

    # Test connection
    try:
        await test_mongodb_client.admin.command('ping')
        print(f"✅ Connected to test MongoDB: {TEST_DB_NAME}")
    except Exception as e:
        print(f"❌ Failed to connect to test MongoDB: {e}")
        raise

    yield

    # Cleanup after all tests
    if test_mongodb_client:
        # Drop test database
        await test_mongodb_client.drop_database(TEST_DB_NAME)
        test_mongodb_client.close()
        print("✅ Test MongoDB connection closed")


@pytest.fixture
async def db() -> AsyncIOMotorDatabase:
    """
    Provides a test MongoDB database instance.
    """
    return test_mongodb_client[TEST_DB_NAME]


@pytest.fixture
async def clean_db(db: AsyncIOMotorDatabase):
    """
    Cleans up MongoDB collections after each test.
    This ensures test isolation.
    """
    yield

    # Clean up all collections after test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].delete_many({})


@pytest.fixture
async def products_collection(db: AsyncIOMotorDatabase):
    """Get products collection for tests"""
    return db["products"]


@pytest.fixture
async def categories_collection(db: AsyncIOMotorDatabase):
    """Get categories collection for tests"""
    return db["categories"]


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture(autouse=True)
async def mock_external_services(db):
    """Mock Kafka and Redis for unit tests, override database with test DB"""
    from app.main import app

    # Mock Kafka producer
    mock_producer = AsyncMock()
    mock_producer.publish_event = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()

    # Mock cache service
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    mock_cache.delete = AsyncMock()
    mock_cache.close = AsyncMock()

    # Override database dependency with test database
    from app.db.mongodb import get_database
    app.dependency_overrides[get_database] = lambda: db

    # Override external services
    try:
        from app.events.kafka_producer import get_kafka_producer
        app.dependency_overrides[get_kafka_producer] = lambda: mock_producer
    except (AttributeError, ImportError):
        pass

    try:
        from app.core.cache import get_cache_service
        app.dependency_overrides[get_cache_service] = lambda: mock_cache
    except (AttributeError, ImportError):
        pass

    yield

    # Clear overrides after test
    app.dependency_overrides = {}


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_product_data():
    """Sample product data for tests"""
    return {
        "name": "Test Product",
        "description": "A test product description",
        "price": 99.99,
        "stock": 100,
        "category": "Electronics"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }
