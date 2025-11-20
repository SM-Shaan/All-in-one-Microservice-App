"""
Security Utilities
==================

Password hashing and verification using bcrypt.

Why bcrypt?
- Designed for password hashing
- Slow by design (prevents brute force)
- Includes salt automatically
- Industry standard
"""

from passlib.context import CryptContext


# ============================================================================
# Password Hashing Context
# ============================================================================

# Create password context
# - bcrypt: The hashing algorithm
# - deprecated="auto": Automatically mark old schemes as deprecated
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Password Functions
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a plain text password.

    Uses bcrypt with automatic salt generation.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password

    Example:
        >>> hashed = hash_password("SecurePass123")
        >>> print(hashed)
        $2b$12$somehashedpassword...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password from user
        hashed_password: Stored hashed password

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("SecurePass123")
        >>> verify_password("SecurePass123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def needs_update(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated.

    This happens when:
    - The hashing algorithm is deprecated
    - The cost factor needs to be increased

    Args:
        hashed_password: Stored hashed password

    Returns:
        bool: True if hash needs update

    Example:
        if needs_update(user.hashed_password):
            user.hashed_password = hash_password(plain_password)
    """
    return pwd_context.needs_update(hashed_password)


# ============================================================================
# Password Validation
# ============================================================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Args:
        password: Password to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_password_strength("weak")
        >>> print(is_valid, error)
        False, "Password must be at least 8 characters"
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, ""
