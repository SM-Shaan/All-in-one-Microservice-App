"""
Order Service Main Application
===============================

FastAPI application for order management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

# Import routes
from app.api.routes import orders

# Create FastAPI app
app = FastAPI(
    title="Order Service",
    description="Microservice for managing orders",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])


# Health check endpoint
@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "order-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "order-service",
        "version": "1.0.0",
        "status": "running"
    }


# Metrics endpoint (basic placeholder)
@app.get("/metrics")
async def metrics():
    """Metrics endpoint for Prometheus"""
    return {
        "service": "order-service",
        "timestamp": datetime.utcnow().isoformat()
    }
