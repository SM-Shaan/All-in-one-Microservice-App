"""
User Favorites Repository
==========================

Data access layer for user favorites.
"""

from typing import List, Optional
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.domain.user_favorite import UserFavorite


class FavoriteRepository:
    """Repository for user favorites operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_favorite(
        self,
        user_id: UUID,
        product_id: str
    ) -> UserFavorite:
        """
        Add a product to user's favorites.

        Args:
            user_id: User ID
            product_id: Product ID (MongoDB ObjectId)

        Returns:
            UserFavorite: Created favorite
        """
        favorite = UserFavorite(
            user_id=user_id,
            product_id=product_id
        )

        self.db.add(favorite)
        await self.db.flush()
        await self.db.refresh(favorite)

        return favorite

    async def remove_favorite(
        self,
        user_id: UUID,
        product_id: str
    ) -> bool:
        """
        Remove a product from user's favorites.

        Args:
            user_id: User ID
            product_id: Product ID

        Returns:
            bool: True if removed, False if not found
        """
        stmt = delete(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.product_id == product_id
            )
        )

        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def get_user_favorites(
        self,
        user_id: UUID
    ) -> List[UserFavorite]:
        """
        Get all favorites for a user.

        Args:
            user_id: User ID

        Returns:
            List[UserFavorite]: List of favorites
        """
        stmt = select(UserFavorite).where(
            UserFavorite.user_id == user_id
        ).order_by(UserFavorite.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_favorite(
        self,
        user_id: UUID,
        product_id: str
    ) -> bool:
        """
        Check if product is in user's favorites.

        Args:
            user_id: User ID
            product_id: Product ID

        Returns:
            bool: True if favorite, False otherwise
        """
        stmt = select(UserFavorite).where(
            and_(
                UserFavorite.user_id == user_id,
                UserFavorite.product_id == product_id
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_favorites(self, user_id: UUID) -> int:
        """
        Count user's favorites.

        Args:
            user_id: User ID

        Returns:
            int: Number of favorites
        """
        from sqlalchemy import func

        stmt = select(func.count(UserFavorite.id)).where(
            UserFavorite.user_id == user_id
        )

        result = await self.db.execute(stmt)
        return result.scalar_one()
