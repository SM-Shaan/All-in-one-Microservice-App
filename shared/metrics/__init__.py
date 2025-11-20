"""
Shared Metrics Module
=====================

Prometheus metrics for microservices.
"""

from .prometheus import (
    PrometheusMiddleware,
    get_metrics,
    track_user_created,
    track_login_attempt,
    track_order_created,
    set_active_users,
    MetricsCollector,
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress
)

__all__ = [
    "PrometheusMiddleware",
    "get_metrics",
    "track_user_created",
    "track_login_attempt",
    "track_order_created",
    "set_active_users",
    "MetricsCollector",
    "http_requests_total",
    "http_request_duration_seconds",
    "http_requests_in_progress"
]
