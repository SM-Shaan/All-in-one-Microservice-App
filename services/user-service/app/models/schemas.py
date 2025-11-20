"""
Pydantic Schemas
----------------
These define the shape of request/response data.
Pydantic validates data automatically.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============ User Schemas ============

class UserBase(BaseModel):
    """Base user fields shared across schemas."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Example request body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters"
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.

    All fields are optional - only provided fields are updated.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """
    Schema for user data in responses.

    Note: password is never included in responses!
    """
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        # Allows creating from SQLAlchemy model
        from_attributes = True


class UserInDB(UserResponse):
    """User with hashed password (for internal use only)."""
    hashed_password: str


# ============ Authentication Schemas ============

class LoginRequest(BaseModel):
    """
    Schema for login request.

    Example:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Schema for token response after login.

    Example response:
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 1800
    }
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access token."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8)


# ============ Generic Response Schemas ============

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """
    Standard error response format.

    Example:
    {
        "success": false,
        "error": {
            "code": "NOT_FOUND",
            "message": "User not found",
            "details": {}
        }
    }
    """
    success: bool = False
    error: dict
