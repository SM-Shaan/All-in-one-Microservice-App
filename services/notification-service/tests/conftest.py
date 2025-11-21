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
async def reset_database():
    """Reset database before each test"""
    # TODO: Implement database reset logic
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
