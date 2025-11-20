"""
SQLAlchemy Base
===============

Base class for all database models.

All models should inherit from this Base class.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Usage:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
    """
    pass
