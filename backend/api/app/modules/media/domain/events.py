"""Media domain events - Pure event definitions

POLICY-010: Media Management & Trash Lifecycle
POLICY-009: Media Storage & Quota Enforcement

Emitted by Media AggregateRoot on state changes.
Consumed by event handlers for side effects (metrics tracking, notifications, etc.)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import UUID

from shared.base import DomainEvent
from .enums import MediaType, MediaMimeType, EntityTypeForMedia


@dataclass
class MediaUploaded(DomainEvent):
    """Emitted when a new Media file is uploaded (image or video)"""
    media_id: UUID
    filename: str
    media_type: MediaType
    mime_type: MediaMimeType
    file_size: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


@dataclass
class MediaAssociatedWithEntity(DomainEvent):
    """Emitted when Media is associated with an entity (Book/Bookshelf/Block)"""
    media_id: UUID
    entity_type: EntityTypeForMedia
    entity_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


@dataclass
class MediaDisassociatedFromEntity(DomainEvent):
    """Emitted when Media is removed from an entity"""
    media_id: UUID
    entity_type: EntityTypeForMedia
    entity_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


@dataclass
class MediaMovedToTrash(DomainEvent):
    """Emitted when Media is soft-deleted to Trash (POLICY-010: 30-day retention)"""
    media_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


@dataclass
class MediaRestored(DomainEvent):
    """Emitted when Media is restored from Trash to Active state"""
    media_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id


@dataclass
class MediaPurged(DomainEvent):
    """Emitted when Media is permanently deleted (hard delete after 30-day trash retention)"""
    media_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.media_id

