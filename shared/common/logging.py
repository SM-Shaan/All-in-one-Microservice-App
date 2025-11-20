"""
Shared Logging Module
---------------------
Provides structured logging configuration for all services.
Uses structlog for JSON-formatted logs that work well with Loki.
"""

import logging
import structlog
from typing import Any


def setup_logging(service_name: str, log_level: str = "INFO") -> None:
    """
    Configure structured logging for a service.

    Args:
        service_name: Name of the service (e.g., "user-service")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Example:
        setup_logging("user-service", "DEBUG")
        logger = get_logger()
        logger.info("User created", user_id="123")
    """

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add service name to all logs
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # Format as JSON for production, or pretty print for development
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add service name to all future log entries
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger() -> Any:
    """
    Get a logger instance.

    Returns:
        A structlog logger that outputs JSON.

    Example:
        logger = get_logger()
        logger.info("Processing request", request_id="abc123")
        logger.error("Database error", error=str(e), query=sql)
    """
    return structlog.get_logger()


# Convenience function for quick logging
logger = structlog.get_logger()
