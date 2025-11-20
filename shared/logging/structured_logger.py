"""
Structured Logger
=================

JSON-formatted logging for microservices.

Features:
- JSON output for log aggregation
- Correlation IDs for request tracing
- Contextual information
- Standard log levels
- Extra fields support
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation tools.
    """

    def __init__(self, service_name: str):
        """
        Initialize JSON formatter.

        Args:
            service_name: Name of the service (e.g., "user-service")
        """
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }

        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger wrapper with additional context.

    Provides convenient methods for logging with extra fields.
    """

    def __init__(self, name: str, service_name: str, level: int = logging.INFO):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually __name__)
            service_name: Service name (e.g., "user-service")
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.service_name = service_name

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Create console handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter(service_name))
        self.logger.addHandler(handler)

        # Don't propagate to root logger
        self.logger.propagate = False

    def _log(self, level: int, message: str, **kwargs):
        """
        Internal log method with extra fields.

        Args:
            level: Log level
            message: Log message
            **kwargs: Extra fields to include in log
        """
        # Create log record with extra fields
        extra = {'extra_fields': kwargs}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """
        Log debug message.

        Example:
            logger.debug("Cache lookup", key="user:123", ttl=300)
        """
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """
        Log info message.

        Example:
            logger.info("User created", user_id=user.id, email=user.email)
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """
        Log warning message.

        Example:
            logger.warning("Slow query", query_time_ms=1500)
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """
        Log error message.

        Example:
            logger.error("Payment failed", order_id=order.id, error=str(e))
        """
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """
        Log critical message.

        Example:
            logger.critical("Database connection lost", error=str(e))
        """
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """
        Log exception with traceback.

        Example:
            try:
                process_order()
            except Exception as e:
                logger.exception("Order processing failed", order_id=order.id)
        """
        self.logger.exception(message, extra={'extra_fields': kwargs})


def get_logger(name: str, service_name: str) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name (usually __name__)
        service_name: Service name (e.g., "user-service")

    Returns:
        StructuredLogger instance

    Example:
        logger = get_logger(__name__, "user-service")
        logger.info("Service started")
    """
    return StructuredLogger(name, service_name)


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for current context.

    This should be called at the start of request processing.

    Args:
        correlation_id: Correlation ID to set

    Example:
        set_correlation_id(str(uuid4()))
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID.

    Returns:
        Current correlation ID or None

    Example:
        correlation_id = get_correlation_id()
        if correlation_id:
            print(f"Request ID: {correlation_id}")
    """
    return correlation_id_var.get()


def clear_correlation_id():
    """
    Clear correlation ID from current context.

    This should be called after request processing is complete.

    Example:
        clear_correlation_id()
    """
    correlation_id_var.set(None)


# ============================================================================
# Convenience Functions
# ============================================================================

def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra
):
    """
    Log HTTP request with standard format.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **extra: Additional fields

    Example:
        log_request(
            method="POST",
            path="/api/users",
            status_code=201,
            duration_ms=45.2,
            user_id=user.id
        )
    """
    logger = get_logger("http", "service")
    logger.info(
        f"{method} {path} {status_code}",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra
    )


def log_error(
    error_type: str,
    message: str,
    **extra
):
    """
    Log error with standard format.

    Args:
        error_type: Type of error (e.g., "ValidationError")
        message: Error message
        **extra: Additional context

    Example:
        log_error(
            error_type="PaymentError",
            message="Payment gateway timeout",
            order_id=order.id,
            amount=order.total
        )
    """
    logger = get_logger("error", "service")
    logger.error(
        message,
        error_type=error_type,
        **extra
    )
