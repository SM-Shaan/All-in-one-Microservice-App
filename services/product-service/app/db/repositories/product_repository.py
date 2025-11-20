"""
Product Repository
==================

MongoDB operations for product management.

MongoDB vs PostgreSQL Operations:
- find() vs SELECT
- insert_one() vs INSERT
- update_one() vs UPDATE
- delete_one() vs DELETE
- Queries use dictionaries, not SQL strings

Example MongoDB Query:
    {"category": "Electronics", "price": {"$lt": 1000}}

Equivalent SQL:
    WHERE category = 'Electronics' AND price < 1000
"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
import math

from app.models.product import Product, ProductCreate, ProductUpdate


class ProductRepository:
    """
    Repository for product CRUD operations in MongoDB.

    MongoDB collections are like tables, but more flexible.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Initialize repository with MongoDB collection.

        Args:
            collection: Motor async collection
        """
        self.collection = collection

    async def create(self, product_data: ProductCreate) -> Product:
        """
        Create a new product in MongoDB.

        Args:
            product_data: Product information

        Returns:
            Product: Created product with MongoDB _id

        Example:
            product = await repo.create(ProductCreate(
                name="Laptop",
                price=999.99,
                category="Electronics"
            ))
        """
        # Create product model
        product = Product(
            **product_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Convert to dict for MongoDB
        product_dict = product.to_dict()

        # Insert into MongoDB
        result = await self.collection.insert_one(product_dict)

        # Get the generated _id and set it in the product
        product.id = str(result.inserted_id)

        return product

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get a product by ID.

        MongoDB uses ObjectId for _id field.

        Args:
            product_id: Product ID (string)

        Returns:
            Optional[Product]: Product if found, None otherwise
        """
        try:
            # Convert string ID to MongoDB ObjectId
            object_id = ObjectId(product_id)
        except Exception:
            return None

        # Find document
        document = await self.collection.find_one({"_id": object_id})

        if not document:
            return None

        # Convert MongoDB document to Product model
        # MongoDB stores _id as ObjectId, convert to string
        document['_id'] = str(document['_id'])
        return Product(**document)

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get a product by SKU.

        Args:
            sku: Stock Keeping Unit

        Returns:
            Optional[Product]: Product if found
        """
        document = await self.collection.find_one({"sku": sku})

        if not document:
            return None

        document['_id'] = str(document['_id'])
        return Product(**document)

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        active_only: bool = True,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Product], int]:
        """
        List products with filters and pagination.

        This is more powerful than SQL's WHERE clause!
        MongoDB makes complex queries easy.

        Args:
            skip: Number of records to skip
            limit: Max records to return
            category: Filter by category
            search: Search in name and description
            min_price: Minimum price
            max_price: Maximum price
            in_stock_only: Only products with stock > 0
            active_only: Only active products
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'

        Returns:
            tuple[List[Product], int]: (products, total_count)
        """
        # Build MongoDB query (like WHERE clause in SQL)
        query: Dict[str, Any] = {}

        # Filter by category
        if category:
            query["category"] = category

        # Search in name and description
        if search:
            # $regex: MongoDB's pattern matching (like SQL LIKE)
            # $options: 'i' means case-insensitive
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}}
            ]

        # Price range filter
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price  # Greater than or equal
            if max_price is not None:
                query["price"]["$lte"] = max_price  # Less than or equal

        # Stock filter
        if in_stock_only:
            query["stock"] = {"$gt": 0}  # Greater than

        # Active filter
        if active_only:
            query["is_active"] = True

        # Get total count (for pagination)
        total = await self.collection.count_documents(query)

        # Sort order
        sort_direction = -1 if sort_order == "desc" else 1

        # Execute query with pagination and sorting
        cursor = self.collection.find(query).skip(skip).limit(limit).sort(sort_by, sort_direction)

        # Convert to list
        documents = await cursor.to_list(length=limit)

        # Convert documents to Product models
        products = []
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            products.append(Product(**doc))

        return products, total

    async def update(self, product_id: str, update_data: ProductUpdate) -> Optional[Product]:
        """
        Update a product.

        Args:
            product_id: Product ID
            update_data: Fields to update

        Returns:
            Optional[Product]: Updated product if found
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None

        # Get only fields that were actually provided
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            # Nothing to update
            return await self.get_by_id(product_id)

        # Add updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow()

        # MongoDB update operation
        # $set: Updates specified fields
        result = await self.collection.update_one(
            {"_id": object_id},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            return None

        # Return updated product
        return await self.get_by_id(product_id)

    async def delete(self, product_id: str) -> bool:
        """
        Delete a product.

        Args:
            product_id: Product ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return False

        result = await self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0

    async def update_stock(self, product_id: str, quantity_change: int) -> Optional[Product]:
        """
        Update product stock (increment or decrement).

        Args:
            product_id: Product ID
            quantity_change: Amount to change (positive or negative)

        Returns:
            Optional[Product]: Updated product

        Example:
            # Add 10 items
            await repo.update_stock(product_id, 10)

            # Remove 5 items
            await repo.update_stock(product_id, -5)
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None

        # MongoDB $inc operator: increments field value
        result = await self.collection.update_one(
            {"_id": object_id},
            {
                "$inc": {"stock": quantity_change},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        if result.matched_count == 0:
            return None

        return await self.get_by_id(product_id)

    async def get_by_category(self, category: str, limit: int = 10) -> List[Product]:
        """
        Get products by category.

        Args:
            category: Category name
            limit: Maximum number of products

        Returns:
            List[Product]: Products in category
        """
        cursor = self.collection.find(
            {"category": category, "is_active": True}
        ).limit(limit)

        documents = await cursor.to_list(length=limit)

        products = []
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            products.append(Product(**doc))

        return products

    async def get_featured(self, limit: int = 10) -> List[Product]:
        """
        Get featured products.

        Args:
            limit: Maximum number of products

        Returns:
            List[Product]: Featured products
        """
        cursor = self.collection.find(
            {"is_featured": True, "is_active": True}
        ).limit(limit).sort("average_rating", -1)

        documents = await cursor.to_list(length=limit)

        products = []
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            products.append(Product(**doc))

        return products

    async def search_by_tags(self, tags: List[str], limit: int = 20) -> List[Product]:
        """
        Search products by tags.

        Args:
            tags: List of tags to search
            limit: Maximum number of products

        Returns:
            List[Product]: Matching products
        """
        # Convert tags to lowercase
        tags_lower = [tag.lower() for tag in tags]

        # $in: matches any of the provided values (like SQL IN)
        cursor = self.collection.find(
            {"tags": {"$in": tags_lower}, "is_active": True}
        ).limit(limit)

        documents = await cursor.to_list(length=limit)

        products = []
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            products.append(Product(**doc))

        return products

    async def count(self, active_only: bool = False) -> int:
        """
        Count total products.

        Args:
            active_only: Count only active products

        Returns:
            int: Number of products
        """
        query = {"is_active": True} if active_only else {}
        return await self.collection.count_documents(query)
