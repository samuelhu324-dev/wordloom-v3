"""
Library Models - SQLAlchemy ORM models for persistence

Maps Library Domain aggregate to database table.
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

from core.database import Base


class LibraryModel(Base):
    """
    Library ORM Model

    Table: libraries
    - One Library per user
    - Minimal metadata (name, timestamps)
    - Cover, icon, usage are managed by Media/Chronicle Domains
    """
    __tablename__ = "libraries"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        unique=True,  # One Library per user
        comment="User who owns this Library",
    )
    name = Column(
        String(255),
        nullable=False,
        comment="Library name",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When Library was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="When Library was last updated",
    )

    def __repr__(self) -> str:
        return f"<LibraryModel(id={self.id}, user_id={self.user_id}, name={self.name})>"
