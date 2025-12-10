"""
Database Module - Persistence Layer

Contains:
  - models/: SQLAlchemy ORM models (moved from modules/*/models.py)
  - migrations/: Alembic database migration scripts
  - session.py: Database session management (lazy-loaded engine)
"""

from .models import (
    Base,
    LibraryModel,
    BookshelfModel,
    BookModel,
    BlockModel,
    TagModel,
    TagAssociationModel,
    MediaModel,
    MediaAssociationModel,
    SearchIndexModel,
)
from .session import get_db_session, get_engine, get_session_factory

__all__ = [
    "Base",
    "LibraryModel",
    "BookshelfModel",
    "BookModel",
    "BlockModel",
    "TagModel",
    "TagAssociationModel",
    "MediaModel",
    "MediaAssociationModel",
    "SearchIndexModel",
    "get_db_session",
    "get_engine",
    "get_session_factory",
]

