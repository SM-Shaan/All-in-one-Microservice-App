"""
Database Session Management
===========================

Handles database connection pooling and session management.

Key Concepts:
- AsyncEngine: Async database connection pool
- AsyncSession: Individual database session
- Dependency Injection: FastAPI dependency for routes
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from typing import AsyncGenerator

from app.core.config import settings


# ============================================================================
# Database Engine
# ============================================================================

# Create async engine
# - pool_pre_ping: Check connection health before using
# - echo: Log SQL queries (useful for debugging, disable in production)
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
# - expire_on_commit=False: Keep objects usable after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI routes.

    This is used as a dependency in route handlers to get a database session.

    Usage in routes:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            users = await db.execute(select(User))
            return users.scalars().all()

    The session is automatically:
    - Created when the request starts
    - Committed if no errors occur
    - Rolled back if an error occurs
    - Closed when the request ends

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# Database Initialization
# ============================================================================

async def init_db() -> None:
    """
    Initialize database - create all tables.

    This is called on application startup.
    In production, use Alembic migrations instead.
    """
    from app.db.base import Base
    # Import models to register them with Base
    from app.models.domain import user  # noqa
    from app.models.domain import user_favorite  # noqa

    async with engine.begin() as conn:
        # Create all tables defined in Base
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")


async def close_db() -> None:
    """
    Close database connections.

    This is called on application shutdown.
    """
    await engine.dispose()
    print("✅ Database connections closed")
