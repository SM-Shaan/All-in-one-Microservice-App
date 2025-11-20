"""
Database Connection
===================

MongoDB connection for payment service.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings


class Database:
    """Database connection manager"""
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_manager = Database()


async def connect_to_database():
    """Connect to MongoDB"""
    db_manager.client = AsyncIOMotorClient(settings.mongodb_url)
    db_manager.db = db_manager.client[settings.mongodb_db_name]
    print(f"Connected to MongoDB: {settings.mongodb_db_name}")


async def close_database_connection():
    """Close MongoDB connection"""
    if db_manager.client:
        db_manager.client.close()
        print("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db_manager.db
