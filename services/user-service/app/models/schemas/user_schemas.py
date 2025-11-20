"""
User Pydantic Schemas
=====================

Request/Response models for the User API.

These are DIFFERENT from database models:
- Database models (SQLAlchemy) = How data is stored
- Pydantic models = How data is sent/received via API

Why separate?
- API might have different structure than database
- Validation happens at API level
- Sensitive data (like password) never exposed in responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# Base Schemas
# ============================================================================

class UserBase(BaseModel):
    """
    Base user fields shared across schemas.

    Contains fields that are common to most user operations.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


# ============================================================================
# Request Schemas (Input)
# ============================================================================

class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Used in POST /api/v1/users endpoint.

    Example:
    {
        "email": "john@example.com",
        "full_name": "John Doe",
        "password": "SecurePass123"
    }
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters"
    )


class UserUpdate(BaseModel):
    """
    Schema for updating a user.

    Used in PUT /api/v1/users/{id} endpoint.
    All fields are optional - only provided fields are updated.

    Example:
    {
        "full_name": "John Smith"
    }
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


# ============================================================================
# Response Schemas (Output)
# ============================================================================

class UserResponse(UserBase):
    """
    Schema for user data in API responses.

    IMPORTANT: Never include password or hashed_password in responses!

    Used in:
    - GET /api/v1/users
    - GET /api/v1/users/{id}
    - POST /api/v1/users
    - PUT /api/v1/users/{id}
    """
    id: UUID
    is_active: bool
    is_superuser: bool
    role: str  # Phase 10: Role-based access control
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration"""
        from_attributes = True  # Allow creation from SQLAlchemy model
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class UserListResponse(BaseModel):
    """
    Schema for paginated user list response.

    Includes metadata for pagination.
    """
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Internal Schemas (Not exposed via API)
# ============================================================================

class UserInDB(UserResponse):
    """
    User schema with password hash.

    Used internally, NEVER sent in API responses.
    """
    hashed_password: str
