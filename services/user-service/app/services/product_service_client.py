"""
Product Service Client
======================

Client for communicating with Product Service.

This abstracts away the HTTP details and provides
a clean Python API for other services.

Example:
    product_client = ProductServiceClient(http_client)
    product = await product_client.get_product(product_id)
"""

from typing import Optional, List, Dict, Any
from app.core.http_client import HTTPClient, ServiceURLs


class ProductServiceClient:
    """
    Client for Product Service API.

    Provides methods to interact with Product Service.
    """

    def __init__(self, http_client: HTTPClient):
        """
        Initialize product service client.

        Args:
            http_client: HTTP client instance
        """
        self.http_client = http_client
        self.base_url = ServiceURLs.PRODUCT_SERVICE
        self.service_name = "product-service"

    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a product by ID.

        Args:
            product_id: Product ID

        Returns:
            Optional[Dict]: Product data or None if not found

        Example:
            product = await client.get_product("65abc123...")
            if product:
                print(f"Product: {product['name']}")
        """
        url = f"{self.base_url}/api/v1/products/{product_id}"
        return await self.http_client.get(url, service_name=self.service_name)

    async def get_products(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get list of products with filters.

        Args:
            skip: Pagination offset
            limit: Page size
            category: Filter by category
            search: Search text
            min_price: Minimum price
            max_price: Maximum price
            in_stock_only: Only in-stock products

        Returns:
            Optional[Dict]: Product list response with pagination

        Example:
            result = await client.get_products(
                category="Electronics",
                min_price=1000,
                limit=10
            )
            products = result['products']
        """
        url = f"{self.base_url}/api/v1/products"

        # Build query parameters
        params = {
            "skip": skip,
            "limit": limit,
            "in_stock_only": in_stock_only
        }

        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        return await self.http_client.get(
            url,
            service_name=self.service_name,
            params=params
        )

    async def get_featured_products(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get featured products.

        Args:
            limit: Maximum number of products

        Returns:
            Optional[List]: List of featured products
        """
        url = f"{self.base_url}/api/v1/products/featured"
        params = {"limit": limit}

        result = await self.http_client.get(
            url,
            service_name=self.service_name,
            params=params
        )

        return result if result else []

    async def get_products_by_category(
        self,
        category: str,
        limit: int = 20
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get products in a category.

        Args:
            category: Category name
            limit: Maximum number of products

        Returns:
            Optional[List]: List of products
        """
        url = f"{self.base_url}/api/v1/products/category/{category}"
        params = {"limit": limit}

        result = await self.http_client.get(
            url,
            service_name=self.service_name,
            params=params
        )

        return result if result else []

    async def get_products_by_ids(
        self,
        product_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get multiple products by their IDs.

        Makes parallel requests for better performance.

        Args:
            product_ids: List of product IDs

        Returns:
            List[Dict]: List of products (excludes not found)

        Example:
            products = await client.get_products_by_ids([
                "65abc123...",
                "65def456...",
                "65ghi789..."
            ])
        """
        import asyncio

        # Make parallel requests
        tasks = [
            self.get_product(product_id)
            for product_id in product_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        products = []
        for result in results:
            if result and not isinstance(result, Exception):
                products.append(result)

        return products

    async def check_product_availability(
        self,
        product_id: str,
        quantity: int = 1
    ) -> bool:
        """
        Check if product has sufficient stock.

        Args:
            product_id: Product ID
            quantity: Required quantity

        Returns:
            bool: True if available, False otherwise
        """
        product = await self.get_product(product_id)

        if not product:
            return False

        return product.get("stock", 0) >= quantity

    async def health_check(self) -> bool:
        """
        Check if Product Service is healthy.

        Returns:
            bool: True if service is up, False otherwise
        """
        url = f"{self.base_url}/health"

        try:
            result = await self.http_client.get(
                url,
                service_name=self.service_name
            )
            return result is not None and result.get("status") == "healthy"
        except Exception:
            return False


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_product_service_client(
    http_client: HTTPClient
) -> ProductServiceClient:
    """
    Dependency to get product service client.

    Usage:
        @router.get("/...")
        async def endpoint(
            product_client: ProductServiceClient = Depends(get_product_service_client),
            http_client: HTTPClient = Depends(get_http_client)
        ):
            product = await product_client.get_product("123")
    """
    return ProductServiceClient(http_client)
