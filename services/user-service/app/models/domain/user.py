"""
User Domain Model
=================

SQLAlchemy model for the User table in PostgreSQL.

This is the DATABASE MODEL that maps to the 'users' table.
Don't confuse with Pydantic models in app/models/schemas.py
"""

from sqlalchemy import Boolean, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
import uuid

from app.db.base import Base


class User(Base):
    """
    User database model.

    Represents a user in the system with authentication and profile info.

    Attributes:
        id: Unique identifier (UUID)
        email: User's email address (unique)
        full_name: User's full name
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        is_superuser: Whether the user has admin privileges
        created_at: When the user was created
        updated_at: When the user was last updated
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Unique user identifier"
    )

    # User information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User's email address"
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User's full name"
    )

    hashed_password: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Bcrypt hashed password"
    )

    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active"
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user has admin privileges"
    )

    # Role (Phase 10: Authentication & Authorization)
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
        comment="User role: user, admin, etc."
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When the user was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="When the user was last updated"
    )

    def __repr__(self) -> str:
        """String representation of the user"""
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"

    def to_dict(self) -> dict:
        """
        Convert model to dictionary.

        Useful for serialization and debugging.
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "role": self.role,  # Phase 10: RBAC
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
