"""
User Repository
===============

Repository Pattern for User data access.

Why Repository Pattern?
- Separates data access logic from business logic
- Makes testing easier (can mock the repository)
- Provides clean abstraction over database operations
- Centralizes database queries

Architecture:
    Routes -> Repository -> Database
"""

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.domain.user import User


class UserRepository:
    """
    Repository for User database operations.

    All database queries for users go through this class.
    This keeps the route handlers clean and focused on HTTP logic.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def create(self, user: User) -> User:
        """
        Create a new user in the database.

        Args:
            user: User model instance

        Returns:
            User: Created user with ID and timestamps
        """
        self.db.add(user)
        await self.db.flush()  # Flush to get the ID without committing
        await self.db.refresh(user)  # Refresh to get default values
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[User]: User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.

        Useful for login and checking if email already exists.

        Args:
            email: User's email address

        Returns:
            Optional[User]: User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 10,
        active_only: bool = False
    ) -> List[User]:
        """
        Get list of users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Filter for active users only

        Returns:
            List[User]: List of users
        """
        query = select(User)

        if active_only:
            query = query.where(User.is_active == True)

        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """
        Update a user's fields.

        Args:
            user_id: User's unique identifier
            **kwargs: Fields to update

        Returns:
            Optional[User]: Updated user if found, None otherwise

        Example:
            await repo.update(user_id, full_name="New Name", is_active=True)
        """
        # First check if user exists
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Update the fields
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )

        await self.db.execute(stmt)
        await self.db.flush()

        # Return the updated user
        return await self.get_by_id(user_id)

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a user from the database.

        Args:
            user_id: User's unique identifier

        Returns:
            bool: True if deleted, False if not found
        """
        # Check if user exists
        user = await self.get_by_id(user_id)
        if not user:
            return False

        # Delete the user
        stmt = delete(User).where(User.id == user_id)
        await self.db.execute(stmt)
        return True

    async def count(self, active_only: bool = False) -> int:
        """
        Count total number of users.

        Args:
            active_only: Count only active users

        Returns:
            int: Number of users
        """
        from sqlalchemy import func

        query = select(func.count(User.id))

        if active_only:
            query = query.where(User.is_active == True)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with given email exists.

        Useful for validation during registration.

        Args:
            email: Email address to check

        Returns:
            bool: True if email exists, False otherwise
        """
        user = await self.get_by_email(email)
        return user is not None


# ============================================================================
# Dependency Injection Helper
# ============================================================================

def get_user_repository(db: AsyncSession) -> UserRepository:
    """
    Dependency function to get UserRepository instance.

    Usage in routes:
        @router.get("/users")
        async def get_users(
            repo: UserRepository = Depends(get_user_repository)
        ):
            users = await repo.list()
            return users
    """
    return UserRepository(db)
