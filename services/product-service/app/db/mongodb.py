"""
MongoDB Connection Management
=============================

Handles MongoDB connection using Motor (async driver).

Key Concepts:
- Motor: Async MongoDB driver for Python
- Single client instance for connection pooling
- Database and collection access

MongoDB vs PostgreSQL:
- NoSQL (document-based) vs SQL (table-based)
- Flexible schema vs Fixed schema
- JSON-like documents vs Rows with columns
- Great for nested data vs Great for relationships
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional

from app.core.config import settings


# ============================================================================
# Global MongoDB Client
# ============================================================================

class MongoDB:
    """
    MongoDB connection manager.

    Singleton pattern - one client for the entire application.
    """
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB.

        Creates a connection pool that will be reused across requests.
        """
        print(f"🔄 Connecting to MongoDB at {settings.mongodb_url}...")

        cls.client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=10,
            minPoolSize=2,
            serverSelectionTimeoutMS=5000,  # 5 seconds timeout
        )

        # Select database
        cls.db = cls.client[settings.mongodb_db_name]

        # Test connection
        try:
            await cls.client.admin.command('ping')
            print(f"✅ Connected to MongoDB database: {settings.mongodb_db_name}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def close(cls):
        """
        Close MongoDB connection.

        Called on application shutdown.
        """
        if cls.client:
            cls.client.close()
            print("✅ MongoDB connection closed")

    @classmethod
    def get_collection(cls, collection_name: str) -> AsyncIOMotorCollection:
        """
        Get a MongoDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            AsyncIOMotorCollection: Collection instance

        Example:
            products = MongoDB.get_collection("products")
            await products.insert_one({"name": "Laptop"})
        """
        if cls.db is None:
            raise RuntimeError("MongoDB not connected. Call MongoDB.connect() first.")

        return cls.db[collection_name]


# ============================================================================
# Collection Names (Constants)
# ============================================================================

class Collections:
    """
    MongoDB collection names.

    Keeps collection names consistent across the application.
    """
    PRODUCTS = "products"
    CATEGORIES = "categories"
    REVIEWS = "reviews"


# ============================================================================
# Dependency Injection
# ============================================================================

def get_database() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance.

    Used as a FastAPI dependency.

    Usage:
        @router.get("/products")
        async def get_products(db: AsyncIOMotorDatabase = Depends(get_database)):
            products = await db.products.find().to_list(100)
            return products
    """
    if MongoDB.db is None:
        raise RuntimeError("MongoDB not connected. Call MongoDB.connect() first.")

    return MongoDB.db


def get_products_collection() -> AsyncIOMotorCollection:
    """
    Get products collection.

    Convenience function for the main collection.
    """
    return MongoDB.get_collection(Collections.PRODUCTS)
