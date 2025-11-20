"""
Authentication Schemas
======================

Pydantic models for authentication endpoints.

These are REQUEST and RESPONSE models for API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class LoginRequest(BaseModel):
    """
    Login request model.

    Example:
        {
            "email": "alice@example.com",
            "password": "securepass123"
        }
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request model.

    Example:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        }
    """
    refresh_token: str = Field(..., description="Refresh token")


# ============================================================================
# Response Models
# ============================================================================

class TokenResponse(BaseModel):
    """
    Token response model (for login and refresh).

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "expires_in": 900
        }
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class CurrentUserResponse(BaseModel):
    """
    Current user response model (for /auth/me endpoint).

    Example:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "alice@example.com",
            "full_name": "Alice Johnson",
            "role": "user",
            "is_active": true,
            "created_at": "2025-01-20T10:30:00"
        }
    """
    id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    role: str = Field(..., description="User's role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="When user was created")

    class Config:
        from_attributes = True


class LogoutResponse(BaseModel):
    """
    Logout response model.

    Example:
        {
            "message": "Successfully logged out"
        }
    """
    message: str = Field(default="Successfully logged out")


# ============================================================================
# Token Payload Models (for internal use)
# ============================================================================

class TokenPayload(BaseModel):
    """
    JWT token payload model.

    This represents the decoded token data.
    """
    sub: str = Field(..., description="Subject (user ID)")
    email: Optional[str] = Field(None, description="User's email")
    role: Optional[str] = Field(None, description="User's role")
    token_type: str = Field(..., description="Token type (access/refresh)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
