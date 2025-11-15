"""Search Domain Events - Domain event definitions

Events emitted by Search module (optional - if Search owns lifecycle).

Current scope: Search is a read-only query adapter.
Events are optional - only if Search needs to notify other modules of index changes.

Future: SearchIndexUpdated event when search_index table changes.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from shared.base import DomainEvent


@dataclass
class SearchIndexUpdated(DomainEvent):
    """
    Emitted when search index is updated

    This is optional - currently handled by EventBus handlers directly.
    Can be used for audit logging or downstream notifications.
    """
    entity_type: str
    entity_id: UUID
    operation: str  # INSERT, UPDATE, DELETE
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


__all__ = [
    "SearchIndexUpdated",
]
