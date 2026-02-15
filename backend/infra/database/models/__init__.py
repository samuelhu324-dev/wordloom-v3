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

from .base import Base

# Import all models
from .library_models import LibraryModel
from .bookshelf_models import BookshelfModel
from .book_models import BookModel
from .block_models import BlockModel
from .tag_models import TagModel, TagAssociationModel, EntityType
from .media_models import (
    MediaModel, MediaAssociationModel,
    MediaType, MediaMimeType, MediaState, EntityTypeForMedia
)
from .search_index_models import SearchIndexModel
from .projection_status_models import ProjectionStatusModel
from .chronicle_models import ChronicleEventModel
from .chronicle_outbox_models import ChronicleOutboxEventModel
from .chronicle_entries_models import ChronicleEntryModel
from .chronicle_dedupe_models import ChronicleEventDedupeStateModel
from .maturity_models import MaturitySnapshotModel

__all__ = [
    # Base
    "Base",
    # Library models
    "LibraryModel",
    "BookshelfModel",
    "BookModel",
    "BlockModel",
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
    # Search
    "SearchIndexModel",
    "ProjectionStatusModel",
    # Chronicle
    "ChronicleEventModel",
    "ChronicleOutboxEventModel",
    "ChronicleEntryModel",
    "ChronicleEventDedupeStateModel",
    # Maturity
    "MaturitySnapshotModel",
]

