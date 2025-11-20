"""
Shared Logging Module
=====================

Structured logging utilities for microservices.
"""

from .structured_logger import (
    StructuredLogger,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    clear_correlation_id,
    log_request,
    log_error
)

__all__ = [
    "StructuredLogger",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "clear_correlation_id",
    "log_request",
    "log_error"
]
