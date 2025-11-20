"""
Product Service - Main Application
===================================

E-commerce product catalog management using MongoDB.

Learning Points:
- MongoDB (NoSQL) vs PostgreSQL (SQL)
- Document-based storage
- Flexible schema
- Rich querying capabilities
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.cache import init_cache, close_cache
from app.db.mongodb import MongoDB
from app.api.routes import health, products


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown.

    Startup: Connect to MongoDB
    Shutdown: Close MongoDB connection
    """
    # Startup
    print("=" * 60)
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print("=" * 60)
    print(f"📍 Running on http://{settings.service_host}:{settings.service_port}")
    print(f"📚 API Docs: http://{settings.service_host}:{settings.service_port}/docs")
    print()

    # Connect to MongoDB
    try:
        await MongoDB.connect()
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        raise

    # Initialize Redis cache (Phase 8: Caching)
    print("🔄 Initializing Redis cache...")
    try:
        await init_cache()
        print("✅ Redis cache initialized successfully")
    except Exception as e:
        print(f"⚠️ Redis cache initialization failed: {e}")
        print("⚠️ Service will continue without caching")

    # TODO: Initialize Kafka producer (Phase 6)

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

    await MongoDB.close()

    # Close Redis cache (Phase 8)
    await close_cache()

    # TODO: Close Kafka producer (Phase 6)

    print("✅ Shutdown complete")
    print("=" * 60)


# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Product catalog management microservice.

    Features:
    - Product CRUD operations
    - Advanced search and filtering
    - Category management
    - Tag-based search
    - Stock management
    - MongoDB storage
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ============================================================================
# Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(health.router, tags=["Health"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "database": "MongoDB",
        "docs": "/docs"
    }


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug,
        log_level="info"
    )
