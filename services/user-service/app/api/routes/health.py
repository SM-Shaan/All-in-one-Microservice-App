"""
Health Check Routes
===================

Endpoints for monitoring service health and readiness.

- GET /health - Basic health check
- GET /health/ready - Readiness probe (checks dependencies)
- GET /health/live - Liveness probe (checks if service is alive)
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime
from typing import Dict

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
    checks: Dict[str, bool]


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check"
)
async def health_check():
    """
    Basic health check endpoint.

    This is used by load balancers and monitoring systems to verify
    the service is running.

    Returns:
        HealthResponse: Service status and information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="user-service",
        version="1.0.0"
    )


@router.api_route(
    "/health/ready",
    methods=["GET", "HEAD"],
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Check"
)
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Kafka connectivity

    Returns:
        ReadinessResponse: Status of all dependencies
    """
    checks = {
        "database": True,  # TODO: Check actual database connection
        "redis": True,     # TODO: Check actual Redis connection
        "kafka": True,     # TODO: Check actual Kafka connection
    }

    # Service is ready if all checks pass
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
    status_code=status.HTTP_200_OK,
    summary="Liveness Check"
)
async def liveness_check():
    """
    Liveness check - verifies the service process is alive.

    This is simpler than readiness - it just checks if the service
    can respond to requests.

    Returns:
        HealthResponse: Service liveness status
    """
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow(),
        service="user-service",
        version="1.0.0"
    )
