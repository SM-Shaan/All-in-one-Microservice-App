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

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


# ============================================================================
# Database Configuration for Tests
# ============================================================================

# Use test database URL - check environment or use default
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/test_users"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


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
    Setup test database tables before running tests.
    This runs once per test session.
    """
    from app.db.base import Base
    # Import models to register them
    from app.models.domain import user  # noqa
    from app.models.domain import user_favorite  # noqa

    async with test_engine.begin() as conn:
        # Drop all tables first (clean slate)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a test database session.
    Data is automatically cleaned up after each test.
    """
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def clean_db(db_session: AsyncSession):
    """
    Cleans up database tables after each test.
    This ensures test isolation.
    """
    yield

    # Clean up all tables after test
    from app.models.domain.user import User
    from app.models.domain.user_favorite import UserFavorite

    await db_session.execute(UserFavorite.__table__.delete())
    await db_session.execute(User.__table__.delete())
    await db_session.commit()


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture(autouse=True)
async def mock_external_services(db_session):
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
    from app.db.session import get_db
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

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
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123"
    }
