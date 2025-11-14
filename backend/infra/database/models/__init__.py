"""
ORM Models - SQLAlchemy Declarative Models

All ORM models moved here from modules/*/models.py

Models will be imported and organized:
  from infra.database.models import (
      LibraryModel, BookshelfModel, BookModel, BlockModel,
      TagModel, TagAssociationModel,
      MediaModel, MediaAssociationModel,
      Base
  )

These models are used by Repository adapters in infra/storage/
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .tag_models import TagModel, TagAssociationModel, EntityType
from .media_models import (
    MediaModel, MediaAssociationModel,
    MediaType, MediaMimeType, MediaState, EntityTypeForMedia
)

__all__ = [
    # Base
    "Base",
    # Tag models
    "TagModel",
    "TagAssociationModel",
    "EntityType",
    # Media models
    "MediaModel",
    "MediaAssociationModel",
    "MediaType",
    "MediaMimeType",
    "MediaState",
    "EntityTypeForMedia",
]

