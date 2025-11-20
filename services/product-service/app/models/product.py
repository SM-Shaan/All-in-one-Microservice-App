"""
Product Models
==============

Pydantic models for products stored in MongoDB.

MongoDB vs SQLAlchemy Models:
- MongoDB: Uses Pydantic for validation
- SQLAlchemy: Uses ORM models with mapped_column
- MongoDB: Flexible schema, can store nested objects
- SQLAlchemy: Fixed schema with strict types

Document Structure:
{
    "_id": "507f1f77bcf86cd799439011",
    "name": "Gaming Laptop",
    "description": "High-performance laptop...",
    "price": 1299.99,
    "category": "Electronics",
    "tags": ["laptop", "gaming", "electronics"],
    "stock": 50,
    "images": ["url1.jpg", "url2.jpg"],
    "specifications": {
        "brand": "TechCorp",
        "model": "GX-2000"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Embedded Models (Nested Documents)
# ============================================================================

class ProductSpecifications(BaseModel):
    """
    Product specifications (nested in product document).

    This is stored as a nested object in MongoDB.
    In PostgreSQL, this would need a separate table.
    """
    brand: Optional[str] = None
    model: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    # Can add any other specifications dynamically
    additional: Optional[Dict[str, str]] = Field(default_factory=dict)


# ============================================================================
# Main Product Model
# ============================================================================

class Product(BaseModel):
    """
    Product document model for MongoDB.

    This represents a product in our e-commerce catalog.

    MongoDB stores this as BSON (Binary JSON):
    - Flexible schema (can add fields dynamically)
    - Nested objects (specifications, reviews)
    - Arrays (tags, images)
    """
    # MongoDB uses _id, but we'll use id in our API
    id: Optional[str] = Field(None, alias="_id")

    # Basic Information
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")

    # Pricing
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    original_price: Optional[float] = Field(None, description="Original price before discount")
    discount_percentage: Optional[float] = Field(0, ge=0, le=100)

    # Categorization
    category: str = Field(..., description="Main category")
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list, description="Search tags")

    # Inventory
    stock: int = Field(default=0, ge=0, description="Available stock")
    low_stock_threshold: int = Field(default=10, description="Alert when stock is low")

    # Media
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    thumbnail: Optional[str] = Field(None, description="Thumbnail image URL")

    # Specifications (nested document)
    specifications: Optional[ProductSpecifications] = None

    # Ratings (we'll implement reviews in a separate collection)
    average_rating: float = Field(default=0.0, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)

    # Status
    is_active: bool = Field(default=True, description="Product is visible to customers")
    is_featured: bool = Field(default=False, description="Featured on homepage")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True  # Allow using both 'id' and '_id'
        json_schema_extra = {
            "example": {
                "name": "Gaming Laptop Pro",
                "description": "High-performance gaming laptop with RTX 4080",
                "sku": "LAPTOP-001",
                "price": 1299.99,
                "original_price": 1499.99,
                "discount_percentage": 13.33,
                "category": "Electronics",
                "subcategory": "Computers",
                "tags": ["laptop", "gaming", "rtx", "high-performance"],
                "stock": 50,
                "images": [
                    "https://example.com/images/laptop1.jpg",
                    "https://example.com/images/laptop2.jpg"
                ],
                "specifications": {
                    "brand": "TechCorp",
                    "model": "GX-2000",
                    "weight": "2.5kg",
                    "color": "Black"
                }
            }
        }

    @field_validator('tags')
    @classmethod
    def lowercase_tags(cls, v: List[str]) -> List[str]:
        """Convert all tags to lowercase for consistent searching"""
        return [tag.lower() for tag in v]

    def is_low_stock(self) -> bool:
        """Check if product stock is below threshold"""
        return self.stock < self.low_stock_threshold

    def is_in_stock(self) -> bool:
        """Check if product is available"""
        return self.stock > 0

    def calculate_discount_price(self) -> float:
        """Calculate discounted price"""
        if self.discount_percentage and self.discount_percentage > 0:
            return self.price * (1 - self.discount_percentage / 100)
        return self.price

    def to_dict(self) -> dict:
        """
        Convert to dictionary for MongoDB insertion.

        MongoDB needs datetime objects, not ISO strings.
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        # Remove _id if it's None (MongoDB will generate it)
        if data.get('_id') is None:
            data.pop('_id', None)
        return data


# ============================================================================
# API Schemas (Request/Response)
# ============================================================================

class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    sku: Optional[str] = None
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    category: str
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    stock: int = Field(default=0, ge=0)
    images: List[str] = Field(default_factory=list)
    specifications: Optional[ProductSpecifications] = None


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    specifications: Optional[ProductSpecifications] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class ProductResponse(BaseModel):
    """Schema for product in API responses"""
    id: str = Field(..., alias="_id")
    name: str
    description: str
    sku: Optional[str]
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[float]
    category: str
    subcategory: Optional[str]
    tags: List[str]
    stock: int
    images: List[str]
    thumbnail: Optional[str]
    specifications: Optional[ProductSpecifications]
    average_rating: float
    review_count: int
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list"""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
