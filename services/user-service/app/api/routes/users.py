"""
User Routes - Phase 8: With Redis Caching
==========================================

CRUD operations for user management using PostgreSQL + Redis Cache.

Changes from Phase 6:
- ✅ Caches user lookups (cache-aside pattern)
- ✅ Invalidates cache on updates/deletes
- ✅ Faster response times for read operations
- ✅ Reduced database load
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import math

from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.models.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse
)
from app.models.domain.user import User
from app.core.security import hash_password
from app.core.cache import get_cache_service, CacheKeys
from app.events.kafka_producer import KafkaEventProducer, get_kafka_producer
from shared.cache import RedisCacheService

# Import event schemas
from shared.events.schemas.user_events import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeletedEvent,
    UserCreatedPayload,
    UserUpdatedPayload,
    UserDeletedPayload,
    UserEventTopics
)
from shared.events.schemas.base import EventMetadata

router = APIRouter()


# ============================================================================
# Dependency: Get Repository
# ============================================================================

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency to get user repository.

    This is injected into route handlers.
    """
    return UserRepository(db)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user account with email and password"
)
async def create_user(
    user_data: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
    producer: KafkaEventProducer = Depends(get_kafka_producer)
):
    """
    Create a new user.

    **Phase 6: EVENT-DRIVEN ARCHITECTURE!**
    - Saves user to PostgreSQL
    - Publishes UserCreatedEvent to Kafka
    - Other services can react to this event!

    **Process:**
    1. Check if email already exists
    2. Hash the password
    3. Create user in database
    4. 🆕 PUBLISH EVENT to Kafka!
    5. Return user info (without password!)

    **Who might listen to this event:**
    - Notification Service → Send welcome email
    - Analytics Service → Track user registration
    - Email Service → Add to mailing list

    Args:
        user_data: User information (email, full_name, password)
        repo: User repository (injected)
        producer: Kafka producer (injected)

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException 400: If email already exists
    """
    # Check if email already exists
    existing_user = await repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email {user_data.email} is already registered"
        )

    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        is_active=True,
        is_superuser=False
    )

    # Save to database
    created_user = await repo.create(new_user)

    # 🆕 PHASE 6: Publish event to Kafka!
    print(f"\n{'='*60}")
    print(f"🎉 USER CREATED: {created_user.email}")
    print(f"{'='*60}")

    event = UserCreatedEvent(
        metadata=EventMetadata(
            event_type="user.created",
            source_service="user-service"
        ),
        payload=UserCreatedPayload(
            user_id=created_user.id,
            email=created_user.email,
            full_name=created_user.full_name,
            is_active=created_user.is_active,
            created_at=created_user.created_at
        )
    )

    await producer.publish(
        event,
        topic=UserEventTopics.USER_CREATED,
        key=str(created_user.id)
    )

    print(f"{'='*60}\n")

    return UserResponse.model_validate(created_user)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List all users",
    description="Get paginated list of users"
)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    active_only: bool = False,
    repo: UserRepository = Depends(get_user_repo)
):
    """
    Get paginated list of users.

    **Query Parameters:**
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (max 100)
    - active_only: Filter for active users only

    Args:
        skip: Offset for pagination
        limit: Page size (max 100)
        active_only: Filter for active users
        repo: User repository (injected)

    Returns:
        UserListResponse: List of users with pagination metadata
    """
    # Limit maximum page size
    limit = min(limit, 100)

    # Get users from database
    users = await repo.list(skip=skip, limit=limit, active_only=active_only)

    # Get total count for pagination
    total = await repo.count(active_only=active_only)

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        total_pages=math.ceil(total / limit) if limit > 0 else 0
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID (cached for 5 minutes)"
)
async def get_user(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repo),
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Get a specific user by ID.

    **Phase 8: CACHE-ASIDE PATTERN!**
    1. Check Redis cache first
    2. If cache HIT → Return cached data (fast!)
    3. If cache MISS → Query database, cache result, return

    **Performance:**
    - Cache hit: ~1ms ⚡
    - Cache miss: ~50ms (database query)

    Args:
        user_id: User's unique identifier (UUID)
        repo: User repository (injected)
        cache: Redis cache service (injected)

    Returns:
        UserResponse: User information

    Raises:
        HTTPException 404: If user not found
    """
    cache_key = CacheKeys.user(str(user_id))

    # 1. Try to get from cache
    cached_user = await cache.get(cache_key)

    if cached_user:
        # Cache HIT! ⚡
        print(f"✨ Cache HIT for user {user_id}")
        return UserResponse(**cached_user)

    # 2. Cache MISS - query database
    print(f"💾 Cache MISS for user {user_id} - querying database")
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # 3. Store in cache (TTL: 300 seconds = 5 minutes)
    user_dict = UserResponse.model_validate(user).model_dump()
    await cache.set(cache_key, user_dict, ttl=300)

    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information and invalidate cache"
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    repo: UserRepository = Depends(get_user_repo),
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Update an existing user.

    **Phase 8: CACHE INVALIDATION!**
    - Updates user in database
    - Invalidates cache for this user
    - Next read will be cache miss (fresh data)

    **What can be updated:**
    - Email
    - Full name
    - Active status

    **Note:** Password updates will be in Phase 4 (Authentication)

    Args:
        user_id: User's unique identifier
        user_data: Fields to update (only provided fields are updated)
        repo: User repository (injected)
        cache: Redis cache service (injected)

    Returns:
        UserResponse: Updated user information

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If email already taken by another user
    """
    # Check if user exists
    existing_user = await repo.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    old_email = existing_user.email

    # If email is being updated, check if it's already taken
    if user_data.email and user_data.email != existing_user.email:
        email_user = await repo.get_by_email(user_data.email)
        if email_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_data.email} is already taken"
            )

    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)

    updated_user = await repo.update(user_id, **update_data)

    # 🗑️ INVALIDATE CACHE
    cache_key = CacheKeys.user(str(user_id))
    await cache.delete(cache_key)

    # If email changed, also invalidate old email cache
    if old_email and user_data.email and old_email != user_data.email:
        old_email_key = CacheKeys.user_by_email(old_email)
        await cache.delete(old_email_key)

    print(f"🗑️ Cache invalidated for user {user_id}")

    return UserResponse.model_validate(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user account and invalidate cache"
)
async def delete_user(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repo),
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Delete a user from the database.

    **Phase 8: CACHE INVALIDATION!**
    - Deletes user from database
    - Invalidates cache for this user

    **Warning:** This is a hard delete. The user data is permanently removed.

    In production, you might want to:
    - Soft delete (set is_active=False)
    - Archive user data
    - Require admin permissions

    Args:
        user_id: User's unique identifier
        repo: User repository (injected)
        cache: Redis cache service (injected)

    Raises:
        HTTPException 404: If user not found
    """
    # Get user first (to invalidate email cache)
    user = await repo.get_by_id(user_id)

    deleted = await repo.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # 🗑️ INVALIDATE CACHE
    cache_key = CacheKeys.user(str(user_id))
    await cache.delete(cache_key)

    # Also invalidate email cache
    if user:
        email_key = CacheKeys.user_by_email(user.email)
        await cache.delete(email_key)

    print(f"🗑️ Cache invalidated for deleted user {user_id}")

    return None


@router.get(
    "/email/{email}",
    response_model=UserResponse,
    summary="Get user by email",
    description="Find a user by their email address (cached for 5 minutes)"
)
async def get_user_by_email(
    email: str,
    repo: UserRepository = Depends(get_user_repo),
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Get a user by email address.

    **Phase 8: CACHE-ASIDE PATTERN!**
    - Checks cache first
    - Falls back to database if not cached

    Useful for checking if an email is registered.

    Args:
        email: User's email address
        repo: User repository (injected)
        cache: Redis cache service (injected)

    Returns:
        UserResponse: User information

    Raises:
        HTTPException 404: If user not found
    """
    cache_key = CacheKeys.user_by_email(email)

    # 1. Try to get from cache
    cached_user = await cache.get(cache_key)

    if cached_user:
        # Cache HIT! ⚡
        print(f"✨ Cache HIT for user email {email}")
        return UserResponse(**cached_user)

    # 2. Cache MISS - query database
    print(f"💾 Cache MISS for user email {email} - querying database")
    user = await repo.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )

    # 3. Store in cache (TTL: 300 seconds = 5 minutes)
    user_dict = UserResponse.model_validate(user).model_dump()
    await cache.set(cache_key, user_dict, ttl=300)

    return UserResponse.model_validate(user)
