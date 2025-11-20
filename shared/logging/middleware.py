"""
Logging Middleware
==================

FastAPI middleware for correlation IDs and request logging.
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable

from .structured_logger import (
    set_correlation_id,
    clear_correlation_id,
    get_correlation_id,
    get_logger
)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for request tracing.

    This middleware:
    1. Checks for existing X-Correlation-ID header
    2. Generates new correlation ID if not present
    3. Sets correlation ID in context
    4. Adds correlation ID to response headers
    5. Clears correlation ID after request

    Usage:
        app.add_middleware(CorrelationIDMiddleware)
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Correlation-ID"):
        """
        Initialize correlation ID middleware.

        Args:
            app: FastAPI application
            header_name: HTTP header name for correlation ID
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with correlation ID.

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get(
            self.header_name,
            str(uuid.uuid4())
        )

        # Set in context for logging
        set_correlation_id(correlation_id)

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers[self.header_name] = correlation_id

            return response

        finally:
            # Clear correlation ID from context
            clear_correlation_id()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    This middleware logs:
    - Request method and path
    - Response status code
    - Request duration
    - User ID (if authenticated)
    - Correlation ID

    Usage:
        app.add_middleware(RequestLoggingMiddleware, service_name="user-service")
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        skip_paths: list = None
    ):
        """
        Initialize request logging middleware.

        Args:
            app: FastAPI application
            service_name: Name of the service
            skip_paths: Paths to skip logging (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.service_name = service_name
        self.skip_paths = skip_paths or ["/health", "/metrics"]
        self.logger = get_logger(__name__, service_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process and log request.

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Get correlation ID
        correlation_id = get_correlation_id()

        # Log incoming request
        self.logger.info(
            f"→ {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            correlation_id=correlation_id
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Determine log level based on status code
            if response.status_code >= 500:
                log_method = self.logger.error
            elif response.status_code >= 400:
                log_method = self.logger.warning
            else:
                log_method = self.logger.info

            # Log response
            log_method(
                f"← {request.method} {request.url.path} {response.status_code}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                correlation_id=correlation_id
            )

            return response

        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            self.logger.error(
                f"✗ {request.method} {request.url.path} ERROR",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2),
                correlation_id=correlation_id
            )

            # Re-raise exception
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests.

    Logs a warning if request takes longer than threshold.

    Usage:
        app.add_middleware(
            PerformanceLoggingMiddleware,
            service_name="user-service",
            threshold_ms=1000  # Log if request takes > 1 second
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        threshold_ms: float = 1000
    ):
        """
        Initialize performance logging middleware.

        Args:
            app: FastAPI application
            service_name: Name of the service
            threshold_ms: Threshold in milliseconds for slow requests
        """
        super().__init__(app)
        self.service_name = service_name
        self.threshold_ms = threshold_ms
        self.logger = get_logger(__name__, service_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log if slow.

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Log if request is slow
        if duration_ms > self.threshold_ms:
            self.logger.warning(
                f"⚠️ Slow request: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                threshold_ms=self.threshold_ms,
                correlation_id=get_correlation_id()
            )

        return response


# ============================================================================
# Helper Functions
# ============================================================================

def setup_logging_middleware(app, service_name: str):
    """
    Setup all logging middleware for a FastAPI app.

    This is a convenience function that adds all recommended middleware.

    Args:
        app: FastAPI application
        service_name: Name of the service

    Example:
        from shared.logging.middleware import setup_logging_middleware

        app = FastAPI()
        setup_logging_middleware(app, "user-service")
    """
    # Add correlation ID middleware (first, so it's available to others)
    app.add_middleware(CorrelationIDMiddleware)

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware, service_name=service_name)

    # Add performance logging middleware (log slow requests)
    app.add_middleware(
        PerformanceLoggingMiddleware,
        service_name=service_name,
        threshold_ms=1000  # 1 second threshold
    )
