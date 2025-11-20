"""
Shared Exceptions Module
------------------------
Custom exceptions used across all microservices.
These provide consistent error handling throughout the platform.
"""

from typing import Any, Dict, Optional


class BaseServiceException(Exception):
    """
    Base exception for all service errors.

    All custom exceptions should inherit from this class.
    This allows catching all service-related errors with one except clause.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# ============ Authentication Errors ============

class AuthenticationError(BaseServiceException):
    """Raised when authentication fails (wrong password, invalid token)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class TokenExpiredError(BaseServiceException):
    """Raised when a JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "TOKEN_EXPIRED")


class InvalidTokenError(BaseServiceException):
    """Raised when a JWT token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, "INVALID_TOKEN")


class InsufficientPermissionsError(BaseServiceException):
    """Raised when user doesn't have required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "INSUFFICIENT_PERMISSIONS")


# ============ Resource Errors ============

class NotFoundError(BaseServiceException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, "NOT_FOUND", {"resource": resource, "id": identifier})


class AlreadyExistsError(BaseServiceException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(
            message,
            "ALREADY_EXISTS",
            {"resource": resource, "field": field, "value": value}
        )


class ValidationError(BaseServiceException):
    """Raised when input validation fails."""

    def __init__(self, message: str, errors: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", errors or {})


# ============ Business Logic Errors ============

class InsufficientStockError(BaseServiceException):
    """Raised when there's not enough stock for an operation."""

    def __init__(self, product_id: str, requested: int, available: int):
        message = f"Insufficient stock for product {product_id}"
        super().__init__(
            message,
            "INSUFFICIENT_STOCK",
            {
                "product_id": product_id,
                "requested": requested,
                "available": available
            }
        )


class PaymentFailedError(BaseServiceException):
    """Raised when payment processing fails."""

    def __init__(self, message: str, payment_id: str = None):
        super().__init__(message, "PAYMENT_FAILED", {"payment_id": payment_id})


class OrderCancellationError(BaseServiceException):
    """Raised when an order cannot be cancelled."""

    def __init__(self, order_id: str, reason: str):
        message = f"Cannot cancel order {order_id}: {reason}"
        super().__init__(message, "ORDER_CANCELLATION_ERROR", {"order_id": order_id})


# ============ External Service Errors ============

class ServiceUnavailableError(BaseServiceException):
    """Raised when an external service is unavailable."""

    def __init__(self, service_name: str):
        message = f"Service '{service_name}' is currently unavailable"
        super().__init__(message, "SERVICE_UNAVAILABLE", {"service": service_name})


class CircuitBreakerOpenError(BaseServiceException):
    """Raised when circuit breaker is open (too many failures)."""

    def __init__(self, service_name: str):
        message = f"Circuit breaker open for '{service_name}'"
        super().__init__(message, "CIRCUIT_BREAKER_OPEN", {"service": service_name})
