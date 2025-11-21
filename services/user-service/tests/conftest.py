"""
Pytest Configuration
====================

Shared fixtures and configuration for tests.
"""

import sys
from pathlib import Path
import pytest
import asyncio
from typing import AsyncGenerator

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def mock_dependencies(monkeypatch):
    """Mock external dependencies for testing"""
    # Mock database session
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.ext.asyncio import AsyncSession

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.scalars = MagicMock()

    # Mock Kafka producer
    mock_producer = AsyncMock()
    mock_producer.publish_event = AsyncMock()

    # Mock cache service
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    mock_cache.delete = AsyncMock()

    # Patch dependencies
    monkeypatch.setattr("app.db.session.get_db", lambda: mock_db)
    monkeypatch.setattr("app.events.kafka_producer.get_kafka_producer", lambda: mock_producer)
    monkeypatch.setattr("app.core.cache.get_cache_service", lambda: mock_cache)

    yield
    # Cleanup after test


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }
