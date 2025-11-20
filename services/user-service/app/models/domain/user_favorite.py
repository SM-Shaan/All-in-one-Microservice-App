"""
User Favorite Products Model
=============================

Stores user's favorite products.

This demonstrates service-to-service communication:
- We store only product IDs here (User Service database)
- We fetch product details from Product Service (via HTTP)
"""

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
import uuid

from app.db.base import Base


class UserFavorite(Base):
    """
    User's favorite products.

    Stores the relationship between users and their favorite products.
    Product details are fetched from Product Service.
    """

    __tablename__ = "user_favorites"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    # User reference (foreign key to users table)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product ID (from Product Service - MongoDB ObjectId as string)
    # We don't use foreign key because product is in different database!
    product_id: Mapped[str] = mapped_column(
        String(24),  # MongoDB ObjectId is 24 characters
        nullable=False,
        index=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<UserFavorite(user_id={self.user_id}, product_id={self.product_id})>"
