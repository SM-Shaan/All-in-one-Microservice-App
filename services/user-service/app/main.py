"""
User Service - Main Application Entry Point
===========================================

This is a beginner-friendly microservice for user management.
It handles authentication, user profiles, and related operations.

Learning Path:
- Phase 1: Basic FastAPI app with health check
- Phase 2: Add database models and CRUD operations
- Phase 3: Add authentication with JWT
- Phase 4: Add event publishing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.http_client import http_client
from app.core.cache import init_cache, close_cache
from app.events.kafka_producer import kafka_producer
from app.api.routes import health, users, favorites, cache, auth


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown.

    Phase 3: Database initialization added
    Future: Redis, Kafka will be added in later phases

    Startup: Initialize connections (database, Redis, Kafka)
    Shutdown: Close connections gracefully
    """
    from app.db.session import init_db, close_db

    # Startup
    print("=" * 60)
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print("=" * 60)
    print(f"📍 Running on http://{settings.service_host}:{settings.service_port}")
    print(f"📚 API Docs: http://{settings.service_host}:{settings.service_port}/docs")
    print()

    # Initialize database
    print("🔄 Initializing database...")
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

    # Initialize HTTP client (Phase 5: Service Communication)
    print("🔄 Initializing HTTP client for service communication...")
    try:
        await http_client.initialize()
    except Exception as e:
        print(f"❌ HTTP client initialization failed: {e}")
        raise

    # Initialize Kafka producer (Phase 6: Event-Driven Architecture)
    await kafka_producer.start()

    # Initialize Redis cache (Phase 8: Caching)
    print("🔄 Initializing Redis cache...")
    try:
        await init_cache()
        print("✅ Redis cache initialized successfully")
    except Exception as e:
        print(f"⚠️ Redis cache initialization failed: {e}")
        print("⚠️ Service will continue without caching")

    print("=" * 60)
    print("✅ Service is ready to accept requests!")
    print("=" * 60)
    print()

    yield

    # Shutdown
    print()
    print("=" * 60)
    print(f"🛑 Shutting down {settings.app_name}")
    print("=" * 60)

    await close_db()

    # Close HTTP client (Phase 5)
    await http_client.close()

    # Close Kafka producer (Phase 6)
    await kafka_producer.stop()

    # Close Redis cache (Phase 8)
    await close_cache()

    print("✅ Shutdown complete")
    print("=" * 60)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="User management microservice with authentication and profile management",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])  # Phase 10: Auth
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(favorites.router, prefix="/api/v1/users", tags=["Favorites"])
app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])


@app.get("/")
async def root():
    """
    Root endpoint - Service information
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    # Run the service
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug,
        log_level="info"
    )
