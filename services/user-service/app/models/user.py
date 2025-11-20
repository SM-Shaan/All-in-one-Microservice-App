"""
User Database Model
-------------------
SQLAlchemy model representing the users table.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class User(Base):
    """
    User database model.

    This defines the structure of the 'users' table in PostgreSQL.

    Columns:
        id: Unique identifier (UUID)
        email: User's email (unique)
        hashed_password: Bcrypt hashed password
        first_name: User's first name
        last_name: User's last name
        is_active: Whether user account is active
        is_verified: Whether email is verified
        created_at: When user was created
        updated_at: When user was last updated
    """

    __tablename__ = "users"

    # Primary key - UUID is better than auto-increment for distributed systems
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    # Email must be unique and is indexed for fast lookups
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # Never store plain passwords!
    hashed_password = Column(
        String(255),
        nullable=False
    )

    # User profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        """String representation for debugging."""
        return f"<User {self.email}>"
