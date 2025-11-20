"""
Authentication Routes - Phase 10
================================

JWT-based authentication endpoints.

Endpoints:
- POST /auth/login - User login
- POST /auth/refresh - Refresh access token
- GET /auth/me - Get current user info
- POST /auth/logout - User logout
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.models.schemas.auth_schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    CurrentUserResponse,
    LogoutResponse
)
from app.models.domain.user import User
from app.core.security import verify_password
from app.core.jwt import jwt_service
from app.core.auth import get_current_user, verify_refresh_token


router = APIRouter()


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and return JWT tokens"
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint.

    **Process:**
    1. Verify email exists
    2. Verify password
    3. Generate access token (15 minutes)
    4. Generate refresh token (7 days)
    5. Return both tokens

    **Request:**
    ```json
    {
        "email": "alice@example.com",
        "password": "securepass123"
    }
    ```

    **Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 900
    }
    ```

    **Errors:**
    - 401: Invalid credentials
    - 403: User account inactive

    **Usage:**
    ```bash
    curl -X POST http://localhost/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"email":"alice@example.com","password":"securepass123"}'
    ```
    """
    repo = UserRepository(db)

    # Get user by email
    user = await repo.get_by_email(credentials.email)

    if user is None:
        # User not found
        print(f"❌ Login failed: User not found for email {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        # Wrong password
        print(f"❌ Login failed: Wrong password for {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user.is_active:
        print(f"❌ Login failed: Inactive account for {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate tokens
    access_token = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role
    )

    refresh_token = jwt_service.create_refresh_token(
        user_id=user.id
    )

    print(f"✅ Login successful for {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60  # Convert to seconds
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using refresh token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token.

    **Use when:** Access token has expired (after 15 minutes)

    **Process:**
    1. Verify refresh token
    2. Get user from token
    3. Generate new access token
    4. Return new access token

    **Request:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
    }
    ```

    **Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 900
    }
    ```

    **Errors:**
    - 401: Invalid or expired refresh token
    - 403: User account inactive

    **Usage:**
    ```bash
    curl -X POST http://localhost/auth/refresh \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
    ```
    """
    # Verify refresh token and get user
    user = await verify_refresh_token(request.refresh_token, db)

    # Generate new access token
    access_token = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role
    )

    print(f"✅ Token refreshed for {user.email}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get currently authenticated user's information"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.

    **Requires:** Valid access token in Authorization header

    **Response:**
    ```json
    {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "alice@example.com",
        "full_name": "Alice Johnson",
        "role": "user",
        "is_active": true,
        "created_at": "2025-01-20T10:30:00"
    }
    ```

    **Errors:**
    - 401: Invalid or expired token
    - 403: User account inactive

    **Usage:**
    ```bash
    curl http://localhost/auth/me \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
    ```
    """
    return CurrentUserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout current user (client should discard tokens)"
)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.

    **Note:** JWT tokens are stateless, so we can't truly "logout" server-side.
    The client should discard the tokens.

    For production, you might:
    - Store tokens in Redis blacklist
    - Use shorter token expiration
    - Implement token revocation list

    **Requires:** Valid access token

    **Response:**
    ```json
    {
        "message": "Successfully logged out"
    }
    ```

    **Usage:**
    ```bash
    curl -X POST http://localhost/auth/logout \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
    ```
    """
    print(f"✅ User logged out: {current_user.email}")

    return LogoutResponse(
        message="Successfully logged out"
    )


# ============================================================================
# Health Check (for testing auth service is running)
# ============================================================================

@router.get(
    "/health",
    summary="Auth service health check",
    description="Check if authentication service is running"
)
async def auth_health():
    """
    Authentication service health check.

    **Response:**
    ```json
    {
        "status": "healthy",
        "service": "authentication"
    }
    ```
    """
    return {
        "status": "healthy",
        "service": "authentication"
    }
