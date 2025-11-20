"""
HTTP Client for Service-to-Service Communication
================================================

Handles communication between microservices using httpx.

Key Concepts:
- Async HTTP client
- Connection pooling
- Timeouts
- Retry logic
- Circuit breaker pattern (basic)

Why httpx?
- Async/await support (non-blocking)
- Connection pooling (reuses connections)
- Modern API similar to requests
- Better performance than requests library
"""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from app.core.config import settings


# ============================================================================
# Service URLs Configuration
# ============================================================================

class ServiceURLs:
    """
    URLs for other microservices.

    In production, these would come from service discovery (Consul).
    For now, we hardcode them.
    """
    PRODUCT_SERVICE = "http://localhost:8002"
    ORDER_SERVICE = "http://localhost:8003"
    INVENTORY_SERVICE = "http://localhost:8004"
    PAYMENT_SERVICE = "http://localhost:8005"


# ============================================================================
# Circuit Breaker (Basic Implementation)
# ============================================================================

class CircuitBreaker:
    """
    Circuit Breaker pattern for fault tolerance.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service recovered

    After too many failures, the circuit "opens" and stops
    sending requests to the failing service. After a timeout,
    it tries again (half-open state).
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before trying again
            success_threshold: Successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"

    def call(self):
        """
        Check if call should be allowed.

        Returns:
            bool: True if call allowed, False if circuit is open
        """
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = datetime.utcnow() - self.last_failure_time
                if elapsed.total_seconds() >= self.timeout_seconds:
                    # Try again (half-open state)
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                    return True
            return False

        return True

    def on_success(self):
        """Record successful call"""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.success_count = 0

    def on_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

        if self.state == "HALF_OPEN":
            self.state = "OPEN"


# ============================================================================
# HTTP Client
# ============================================================================

class HTTPClient:
    """
    Async HTTP client for service-to-service communication.

    Features:
    - Connection pooling
    - Automatic retries
    - Circuit breaker
    - Timeouts
    """

    def __init__(self):
        """Initialize HTTP client with connection pool"""
        self.client: Optional[httpx.AsyncClient] = None
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    async def initialize(self):
        """
        Create HTTP client with connection pool.

        Called on application startup.
        """
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),  # 10s total, 5s connect
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            follow_redirects=True,
        )
        print("✅ HTTP client initialized with connection pool")

    async def close(self):
        """
        Close HTTP client and release connections.

        Called on application shutdown.
        """
        if self.client:
            await self.client.aclose()
            print("✅ HTTP client closed")

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """
        Get circuit breaker for a service.

        Args:
            service_name: Name of the service

        Returns:
            CircuitBreaker: Circuit breaker instance
        """
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    async def request(
        self,
        method: str,
        url: str,
        service_name: str = "unknown",
        retries: int = 3,
        **kwargs
    ) -> Optional[httpx.Response]:
        """
        Make HTTP request with retries and circuit breaker.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            service_name: Name of service (for circuit breaker)
            retries: Number of retries on failure
            **kwargs: Additional arguments for httpx

        Returns:
            Optional[httpx.Response]: Response if successful, None if failed

        Example:
            response = await client.request(
                "GET",
                "http://localhost:8002/api/v1/products/123",
                service_name="product-service"
            )
        """
        if not self.client:
            raise RuntimeError("HTTP client not initialized. Call initialize() first.")

        # Check circuit breaker
        circuit_breaker = self.get_circuit_breaker(service_name)
        if not circuit_breaker.call():
            print(f"⚠️ Circuit breaker OPEN for {service_name}, request blocked")
            return None

        # Retry loop
        for attempt in range(retries):
            try:
                response = await self.client.request(method, url, **kwargs)

                # Check if response is successful
                if response.is_success:
                    circuit_breaker.on_success()
                    return response
                else:
                    print(f"⚠️ Request to {service_name} failed: {response.status_code}")
                    circuit_breaker.on_failure()

            except httpx.TimeoutException:
                print(f"⏱️ Timeout calling {service_name} (attempt {attempt + 1}/{retries})")
                circuit_breaker.on_failure()

            except httpx.ConnectError:
                print(f"🔌 Connection error to {service_name} (attempt {attempt + 1}/{retries})")
                circuit_breaker.on_failure()

            except Exception as e:
                print(f"❌ Error calling {service_name}: {e}")
                circuit_breaker.on_failure()

            # Wait before retry (exponential backoff)
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)

        return None

    async def get(self, url: str, service_name: str = "unknown", **kwargs) -> Optional[Dict[str, Any]]:
        """
        GET request that returns JSON.

        Args:
            url: Full URL
            service_name: Service name for circuit breaker
            **kwargs: Additional arguments

        Returns:
            Optional[Dict]: JSON response or None
        """
        response = await self.request("GET", url, service_name, **kwargs)
        if response and response.is_success:
            try:
                return response.json()
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
        return None

    async def post(self, url: str, service_name: str = "unknown", **kwargs) -> Optional[Dict[str, Any]]:
        """POST request that returns JSON"""
        response = await self.request("POST", url, service_name, **kwargs)
        if response and response.is_success:
            try:
                return response.json()
            except Exception:
                return {}
        return None

    async def put(self, url: str, service_name: str = "unknown", **kwargs) -> Optional[Dict[str, Any]]:
        """PUT request that returns JSON"""
        response = await self.request("PUT", url, service_name, **kwargs)
        if response and response.is_success:
            try:
                return response.json()
            except Exception:
                return {}
        return None

    async def delete(self, url: str, service_name: str = "unknown", **kwargs) -> bool:
        """DELETE request"""
        response = await self.request("DELETE", url, service_name, **kwargs)
        return response is not None and response.is_success


# ============================================================================
# Global HTTP Client Instance
# ============================================================================

http_client = HTTPClient()


async def get_http_client() -> HTTPClient:
    """
    Dependency to get HTTP client.

    Usage:
        @router.get("/...")
        async def endpoint(client: HTTPClient = Depends(get_http_client)):
            data = await client.get("http://...")
    """
    return http_client
