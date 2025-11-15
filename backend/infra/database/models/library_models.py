"""
Library Models - SQLAlchemy ORM models for persistence

Maps Library Domain aggregate to database table.
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from uuid import uuid4

from .base import Base


class LibraryModel(Base):
    """
    Library ORM Model

    Table: libraries
    - One Library per user
    - Minimal metadata (name, timestamps)
    - Cover, icon, usage are managed by Media/Chronicle Domains

    Mapping Strategy (ADR-012):
    - Primary Key: id (UUID)
    - Business Key: user_id (unique per RULE-001)
    - Timestamps: created_at, updated_at (timezone-aware)

    Round-Trip Validation:
    Use _to_domain() for ORM → Domain conversion
    Use _from_domain() for Domain → ORM conversion
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
        unique=True,  # One Library per user (RULE-001),
    )
    name = Column(
        String(255),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    soft_deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<LibraryModel(id={self.id}, user_id={self.user_id}, name={self.name})>"

    # ========================================================================
    # Round-Trip Mapping Methods (for testing and repository conversion)
    # ========================================================================

    def to_dict(self) -> dict:
        """
        Convert ORM model to dictionary for serialization or testing.

        Returns:
            dict with all fields

        Usage:
            model = library_model_factory()
            data = model.to_dict()
            assert data["id"] == model.id
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "soft_deleted_at": self.soft_deleted_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "LibraryModel":
        """
        Create ORM model from dictionary.

        Inverse of to_dict(). Used for testing and data migration.

        Args:
            data: Dictionary with model fields

        Returns:
            LibraryModel instance

        Usage:
            model = LibraryModel.from_dict({
                "id": uuid4(),
                "user_id": uuid4(),
                "name": "Test"
            })
        """
        return LibraryModel(
            id=data.get("id"),
            user_id=data.get("user_id"),
            name=data.get("name"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            soft_deleted_at=data.get("soft_deleted_at"),
        )
