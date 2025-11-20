"""
Health Check Routes
===================

Endpoints for monitoring Product Service health.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime

from app.db.mongodb import MongoDB

router = APIRouter()


class HealthResponse(BaseModel):
    """Response model for health checks"""
    status: str
    timestamp: datetime
    service: str
    version: str


class ReadinessResponse(BaseModel):
    """Response model for readiness checks"""
    status: str
    timestamp: datetime
    checks: dict


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK
)
async def health_check():
    """Basic health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="product-service",
        version="1.0.0"
    )


@router.api_route(
    "/health/ready",
    methods=["GET", "HEAD"],
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK
)
async def readiness_check():
    """
    Readiness check - verifies MongoDB connection.
    """
    checks = {}

    # Check MongoDB connection
    try:
        if MongoDB.client:
            await MongoDB.client.admin.command('ping')
            checks["mongodb"] = True
        else:
            checks["mongodb"] = False
    except Exception:
        checks["mongodb"] = False

    # Future checks
    checks["redis"] = True  # TODO: Check Redis (Phase 8)
    checks["kafka"] = True  # TODO: Check Kafka (Phase 6)

    all_ready = all(checks.values())

    return ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        timestamp=datetime.utcnow(),
        checks=checks
    )


@router.api_route(
    "/health/live",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK
)
async def liveness_check():
    """Liveness check"""
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow(),
        service="product-service",
        version="1.0.0"
    )
