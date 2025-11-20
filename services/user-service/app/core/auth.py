"""
Authentication Dependencies
===========================

FastAPI dependencies for authentication and authorization.

These are used to protect endpoints and verify user identity.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.models.domain.user import User
from app.core.jwt import jwt_service


# HTTP Bearer token scheme
security = HTTPBearer()


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    This dependency:
    1. Extracts token from Authorization header
    2. Verifies token signature
    3. Extracts user ID from token
    4. Fetches user from database
    5. Returns user object

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello {current_user.email}"}

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token from credentials
    token = credentials.credentials

    # Verify token
    payload = jwt_service.verify_token(token, expected_type="access")
    if payload is None:
        raise credentials_exception

    # Extract user ID from token
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Fetch user from database
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work for both authenticated and anonymous users.

    Usage:
        @router.get("/products")
        async def list_products(
            current_user: Optional[User] = Depends(get_current_user_optional)
        ):
            # Show personalized data if authenticated
            if current_user:
                print(f"User {current_user.email} viewing products")
            return products
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ============================================================================
# Authorization Dependencies (Role-Based)
# ============================================================================

def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.

    Usage:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            current_user: User = Depends(require_role("admin"))
        ):
            # Only admins can delete users
            await repo.delete(user_id)

    Args:
        required_role: The role required (e.g., "admin")

    Returns:
        Dependency function that checks user role
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user

    return role_checker


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin role.

    Convenience function for requiring admin role.

    Usage:
        @router.get("/admin/dashboard")
        async def admin_dashboard(current_user: User = Depends(require_admin)):
            return {"message": "Admin dashboard"}
    """
    if current_user.role != "admin" and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def require_self_or_admin(user_id_param: str = "user_id"):
    """
    Require user to be accessing their own resource or be an admin.

    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            current_user: User = Depends(require_self_or_admin("user_id"))
        ):
            # User can access their own data, or admin can access any
            return await repo.get_by_id(user_id)

    Args:
        user_id_param: Name of the path parameter containing user ID

    Returns:
        Dependency function that checks authorization
    """
    async def authorization_checker(
        user_id: UUID,
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Allow if user is accessing their own resource
        if current_user.id == user_id:
            return current_user

        # Allow if user is admin
        if current_user.role == "admin" or current_user.is_superuser:
            return current_user

        # Deny otherwise
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own resources."
        )

    return authorization_checker


# ============================================================================
# Token Extraction Utilities
# ============================================================================

def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer eyJhbG...")

    Returns:
        Token string if present, None otherwise

    Example:
        token = extract_token_from_header("Bearer eyJhbGc...")
        # Returns: "eyJhbGc..."
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


async def verify_refresh_token(
    refresh_token: str,
    db: AsyncSession
) -> User:
    """
    Verify refresh token and return user.

    Args:
        refresh_token: Refresh token string
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify refresh token
    payload = jwt_service.verify_token(refresh_token, expected_type="refresh")
    if payload is None:
        raise credentials_exception

    # Extract user ID
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Fetch user
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user
