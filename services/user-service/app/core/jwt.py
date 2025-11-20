"""
JWT Token Management
====================

Handles JWT token generation, verification, and validation for authentication.

Features:
- Generate access tokens (short-lived: 15 minutes)
- Generate refresh tokens (long-lived: 7 days)
- Verify token signatures
- Decode token payloads
- Check expiration
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import jwt
from jwt import PyJWTError

from app.core.config import settings


class JWTService:
    """
    JWT token service for authentication.

    Handles creation and validation of access and refresh tokens.
    """

    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        role: str = "user",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new access token.

        Args:
            user_id: User's unique identifier
            email: User's email address
            role: User's role (user, admin, etc.)
            expires_delta: Custom expiration time (optional)

        Returns:
            Encoded JWT access token

        Example:
            token = jwt_service.create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role
            )
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,
            "role": role,
            "token_type": "access",
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow()  # Issued at
        }

        encoded_jwt = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )

        return encoded_jwt

    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new refresh token.

        Refresh tokens have minimal payload for security.

        Args:
            user_id: User's unique identifier
            expires_delta: Custom expiration time (optional)

        Returns:
            Encoded JWT refresh token

        Example:
            refresh_token = jwt_service.create_refresh_token(user_id=user.id)
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.refresh_token_expire_days
            )

        payload = {
            "sub": str(user_id),
            "token_type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )

        return encoded_jwt

    def verify_token(
        self,
        token: str,
        expected_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            expected_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded payload if valid, None if invalid

        Example:
            payload = jwt_service.verify_token(token, "access")
            if payload:
                user_id = payload["sub"]
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check token type
            token_type = payload.get("token_type")
            if token_type != expected_type:
                return None

            # Check expiration (handled automatically by jwt.decode)
            # But we can also check manually
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return None

            return payload

        except PyJWTError as e:
            # Token is invalid (expired, wrong signature, malformed, etc.)
            print(f"JWT verification failed: {e}")
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a JWT token without verification.

        USE WITH CAUTION: Only for debugging or non-security purposes.

        Args:
            token: JWT token string

        Returns:
            Decoded payload (unverified)

        Example:
            payload = jwt_service.decode_token(token)
            print(f"User ID: {payload['sub']}")
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except PyJWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[UUID]:
        """
        Extract user ID from a verified token.

        Args:
            token: JWT token string

        Returns:
            User UUID if token is valid, None otherwise

        Example:
            user_id = jwt_service.get_user_id_from_token(token)
            if user_id:
                user = await repo.get_by_id(user_id)
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        try:
            user_id = UUID(payload.get("sub"))
            return user_id
        except (ValueError, TypeError):
            return None

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """
        Get expiration time from token.

        Args:
            token: JWT token string

        Returns:
            Expiration datetime if token is valid

        Example:
            exp = jwt_service.get_token_expiration(token)
            if exp:
                print(f"Token expires at: {exp}")
        """
        payload = self.decode_token(token)
        if not payload:
            return None

        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp)

        return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired.

        Args:
            token: JWT token string

        Returns:
            True if expired, False otherwise

        Example:
            if jwt_service.is_token_expired(token):
                print("Token expired, please login again")
        """
        exp = self.get_token_expiration(token)
        if not exp:
            return True  # Invalid token = treat as expired

        return exp < datetime.utcnow()


# Global JWT service instance
jwt_service = JWTService()
