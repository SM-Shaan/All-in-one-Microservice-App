"""
Payment Service
===============

FastAPI application for payment processing.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_to_database, close_database_connection
from app.api.routes import payments
from shared.logging.middleware import setup_logging_middleware
from shared.metrics import PrometheusMiddleware, get_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.service_name}...")
    await connect_to_database()
    print(f"{settings.service_name} started successfully!")

    yield

    # Shutdown
    print(f"Shutting down {settings.service_name}...")
    await close_database_connection()
    print(f"{settings.service_name} stopped.")


# Create FastAPI app
app = FastAPI(
    title="Payment Service",
    description="Payment processing service with Stripe integration",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Middleware
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware (correlation ID, request logging, performance)
setup_logging_middleware(app, settings.service_name)

# Prometheus metrics
app.add_middleware(PrometheusMiddleware)


# ============================================================================
# Routes
# ============================================================================

# Payment routes
app.include_router(payments.router)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True
    )
