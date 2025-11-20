"""
Shared Security Module
----------------------
Handles JWT token creation/validation and password hashing.
Used by services that need authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

from jose import jwt, JWTError
from passlib.context import CryptContext

from .exceptions import InvalidTokenError, TokenExpiredError


# Password hashing configuration
# bcrypt is secure and widely used
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Example:
        hashed = hash_password("mysecretpassword")
        # Returns something like: $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to check
        hashed_password: Previously hashed password

    Returns:
        True if password matches, False otherwise

    Example:
        if verify_password("mysecretpassword", stored_hash):
            print("Password correct!")
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (usually {"sub": user_id})
        secret_key: Secret key for signing
        algorithm: JWT algorithm (default: HS256)
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token(
            data={"sub": "user123", "roles": ["user"]},
            secret_key="my-secret",
            expires_delta=timedelta(minutes=30)
        )
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,                    # Expiration time
        "iat": datetime.utcnow(),         # Issued at
        "jti": str(uuid4()),              # Unique token ID
        "type": "access"                  # Token type
    })

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(
    user_id: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens are used to get new access tokens without re-authenticating.
    They have longer expiration times than access tokens.

    Args:
        user_id: User identifier
        secret_key: Secret key for signing
        algorithm: JWT algorithm
        expires_delta: Token expiration time (default: 7 days)

    Returns:
        Encoded JWT refresh token

    Example:
        refresh_token = create_refresh_token(
            user_id="user123",
            secret_key="my-secret",
            expires_delta=timedelta(days=7)
        )
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),
        "type": "refresh"
    }

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256"
) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key used for signing
        algorithm: JWT algorithm

    Returns:
        Decoded token payload

    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid

    Example:
        try:
            payload = decode_token(token, "my-secret")
            user_id = payload["sub"]
        except TokenExpiredError:
            print("Please login again")
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")
