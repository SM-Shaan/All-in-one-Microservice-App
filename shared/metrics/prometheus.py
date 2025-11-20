"""
Prometheus Metrics
==================

Prometheus metrics for FastAPI microservices.

Metrics tracked:
- HTTP requests (count, duration, in progress)
- Business metrics (custom counters, gauges)
"""

import time
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable


# ============================================================================
# Metrics Registry
# ============================================================================

# Create a custom registry (optional, can use default)
registry = CollectorRegistry()


# ============================================================================
# HTTP Metrics
# ============================================================================

# Total HTTP requests
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# HTTP request duration (histogram with buckets)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

# HTTP requests in progress
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint'],
    registry=registry
)


# ============================================================================
# Business Metrics (Examples)
# ============================================================================

# Users created
users_created_total = Counter(
    'users_created_total',
    'Total users created',
    registry=registry
)

# User login attempts
user_login_attempts_total = Counter(
    'user_login_attempts_total',
    'Total user login attempts',
    ['status'],  # success, failure
    registry=registry
)

# Orders created
orders_created_total = Counter(
    'orders_created_total',
    'Total orders created',
    ['status'],  # confirmed, cancelled
    registry=registry
)

# Active users (gauge - can go up/down)
active_users = Gauge(
    'active_users',
    'Number of currently active users',
    registry=registry
)


# ============================================================================
# Prometheus Middleware
# ============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for HTTP requests.

    This middleware tracks:
    - Total requests (counter)
    - Request duration (histogram)
    - Requests in progress (gauge)

    Usage:
        app.add_middleware(PrometheusMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        skip_paths: list = None
    ):
        """
        Initialize Prometheus middleware.

        Args:
            app: FastAPI application
            skip_paths: Paths to skip metrics (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip metrics for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Increment in-progress gauge
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            status = response.status_code
            duration = time.time() - start_time

            # Increment total requests counter
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            # Record request duration
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            return response

        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()

            # Re-raise exception
            raise

        finally:
            # Decrement in-progress gauge
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


# ============================================================================
# Metrics Endpoint
# ============================================================================

def get_metrics() -> Response:
    """
    Generate Prometheus metrics in text format.

    This is the endpoint that Prometheus scrapes.

    Usage:
        @app.get("/metrics")
        async def metrics():
            return get_metrics()

    Returns:
        Response with Prometheus metrics
    """
    metrics_data = generate_latest(registry)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Helper Functions for Business Metrics
# ============================================================================

def track_user_created():
    """
    Track user creation.

    Example:
        user = await create_user(...)
        track_user_created()
    """
    users_created_total.inc()


def track_login_attempt(success: bool):
    """
    Track login attempt.

    Args:
        success: Whether login was successful

    Example:
        if verify_password(...):
            track_login_attempt(success=True)
        else:
            track_login_attempt(success=False)
    """
    status = "success" if success else "failure"
    user_login_attempts_total.labels(status=status).inc()


def track_order_created(status: str):
    """
    Track order creation.

    Args:
        status: Order status (confirmed, cancelled)

    Example:
        if saga_successful:
            track_order_created("confirmed")
        else:
            track_order_created("cancelled")
    """
    orders_created_total.labels(status=status).inc()


def set_active_users(count: int):
    """
    Set number of active users.

    Args:
        count: Number of active users

    Example:
        # Update every minute
        count = await count_active_users()
        set_active_users(count)
    """
    active_users.set(count)


# ============================================================================
# Custom Metrics Helper
# ============================================================================

class MetricsCollector:
    """
    Helper class for creating custom metrics.

    Example:
        metrics = MetricsCollector()

        # Create custom counter
        api_calls = metrics.counter(
            "api_calls_total",
            "Total API calls",
            ["service", "method"]
        )
        api_calls.labels(service="user-service", method="get_user").inc()

        # Create custom gauge
        queue_size = metrics.gauge(
            "queue_size",
            "Current queue size"
        )
        queue_size.set(42)
    """

    def __init__(self, registry=registry):
        """
        Initialize metrics collector.

        Args:
            registry: Prometheus registry (uses global by default)
        """
        self.registry = registry

    def counter(self, name: str, description: str, labels: list = None):
        """
        Create a counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names (optional)

        Returns:
            Counter metric
        """
        return Counter(
            name,
            description,
            labels or [],
            registry=self.registry
        )

    def gauge(self, name: str, description: str, labels: list = None):
        """
        Create a gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names (optional)

        Returns:
            Gauge metric
        """
        return Gauge(
            name,
            description,
            labels or [],
            registry=self.registry
        )

    def histogram(self, name: str, description: str, labels: list = None, buckets=None):
        """
        Create a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names (optional)
            buckets: Histogram buckets (optional)

        Returns:
            Histogram metric
        """
        return Histogram(
            name,
            description,
            labels or [],
            buckets=buckets or [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
