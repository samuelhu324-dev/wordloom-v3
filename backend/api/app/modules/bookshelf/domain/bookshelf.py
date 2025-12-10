"""
Bookshelf Domain Layer - Aggregate Root & Enums

Purpose:
- Represents unlimited classification containers under a Library
- Manages state: is_pinned, is_favorite, status
- Does NOT manage: cover_url (→ Media), icon (→ Media), usage_count (→ Chronicle)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Emits DomainEvents on state changes
- Uses Repository pattern for persistence abstraction
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

from api.app.shared.base import AggregateRoot, DomainEvent

from .bookshelf_name import BookshelfName
from .bookshelf_description import BookshelfDescription
from .events import (
    BookshelfCreated,
    BookshelfRenamed,
    BookshelfStatusChanged,
    BookshelfDeleted,
)

# Default display name for the hidden Basement bookshelf
DEFAULT_BASEMENT_NAME = "Basement"


# ============================================================================
# Enums
# ============================================================================

class BookshelfType(str, Enum):
    """Type of Bookshelf"""
    NORMAL = "normal"
    BASEMENT = "basement"  # ← Special type: recycle bin (trash)


class BookshelfStatus(str, Enum):
    """Status of a Bookshelf"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================================================
# Aggregate Root
# ============================================================================

@dataclass
class Bookshelf(AggregateRoot):
    """
    Bookshelf Aggregate Root (独立聚合根)

    Invariants (Business Rules):
    1. Bookshelf 通过 library_id FK 关联到 Library（不包含 Library 对象）
    2. Name 必须存在且 ≤ 255 字符（RULE-006）
    3. Description 可选，≤ 1000 字符
    4. Status 只能是 ACTIVE / ARCHIVED / DELETED 之一（RULE-005）
    5. Type 用于区分普通书架与 Basement（RULE-010）
    6. Bookshelf 不直接包含 Books（Books 通过 bookshelf_id FK 关联）
    7. is_pinned 和 is_favorite 状态可独立管理
    8. Basement 类型的 Bookshelf 隐藏且不能删除

    Design Decision: 独立聚合根
    - 每个聚合（Library/Bookshelf/Book/Block）都是独立的根
    - 通过 FK 关联，而非对象包含
    - 避免大型对象锁和并发争用
    - Service 层负责跨聚合协调

    Events Emitted:
    - BookshelfCreated: 创建时
    - BookshelfRenamed: 名称变更时
    - BookshelfStatusChanged: 状态变更时
    - BookshelfDeleted: 删除时
    """

    # Identifier
    id: UUID = field(default_factory=uuid4)
    library_id: UUID = field(default=None)

    # Core attributes
    name: BookshelfName = field(default=None)
    description: Optional[BookshelfDescription] = field(default=None)

    # State
    type: BookshelfType = field(default=BookshelfType.NORMAL)
    status: BookshelfStatus = field(default=BookshelfStatus.ACTIVE)

    # Metadata
    is_pinned: bool = field(default=False)
    is_favorite: bool = field(default=False)

    # Timestamps (timezone-aware)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Domain events (internal, not persisted)
    events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @staticmethod
    def create(
        library_id: UUID,
        name: str,
        description: Optional[str] = None,
        type_: BookshelfType = BookshelfType.NORMAL,
        bookshelf_id: Optional[UUID] = None,
    ) -> Bookshelf:
        """
        Factory method to create a new Bookshelf

        RULE-004: 每个 Library 可包含无限个 Bookshelf
        RULE-005: Bookshelf 创建时状态为 ACTIVE
        RULE-006: Name 必须非空，≤255 字符
        """
        # Validate name (will raise if invalid)
        bookshelf_name = BookshelfName(name)

        # Validate description if provided
        bookshelf_description = None
        if description is not None:
            bookshelf_description = BookshelfDescription(description)

        bookshelf = Bookshelf(
            id=bookshelf_id or uuid4(),
            library_id=library_id,
            name=bookshelf_name,
            description=bookshelf_description,
            type=type_,
            status=BookshelfStatus.ACTIVE,
            is_pinned=False,
            is_favorite=False,
        )

        # Emit event
        bookshelf.events.append(
            BookshelfCreated(
                aggregate_id=bookshelf.id,
                library_id=library_id,
                name=bookshelf_name.value,
                type=type_.value,
            )
        )

        return bookshelf

    @staticmethod
    def create_basement(
        library_id: UUID,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        bookshelf_id: Optional[UUID] = None,
    ) -> Bookshelf:
        """Factory helper for the special Basement bookshelf."""
        return Bookshelf.create(
            library_id=library_id,
            name=name or DEFAULT_BASEMENT_NAME,
            description=description,
            type_=BookshelfType.BASEMENT,
            bookshelf_id=bookshelf_id,
        )

    # ========================================================================
    # Business Methods
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """
        Rename the bookshelf

        RULE-006: 验证新名称有效性
        Emits: BookshelfRenamed event
        """
        if self.status == BookshelfStatus.DELETED:
            raise ValueError("Cannot rename a deleted bookshelf")

        new_bookshelf_name = BookshelfName(new_name)

        if self.name == new_bookshelf_name:
            return  # No change

        self.name = new_bookshelf_name
        self.updated_at = datetime.now(timezone.utc)

        self.events.append(
            BookshelfRenamed(
                aggregate_id=self.id,
                library_id=self.library_id,
                old_name=self.name.value,
                new_name=new_bookshelf_name.value,
            )
        )

    def update_description(self, new_description: Optional[str]) -> None:
        """
        Update the bookshelf description
        """
        if self.status == BookshelfStatus.DELETED:
            raise ValueError("Cannot update description of deleted bookshelf")

        if new_description is not None:
            self.description = BookshelfDescription(new_description)
        else:
            self.description = None

        self.updated_at = datetime.now(timezone.utc)

    def change_status(self, new_status: BookshelfStatus) -> None:
        """
        Change bookshelf status (ACTIVE → ARCHIVED → DELETED)

        RULE-005: 状态变更必须遵循有效转移规则
        Emits: BookshelfStatusChanged event
        """
        # Basement bookshelf cannot be deleted
        if self.type == BookshelfType.BASEMENT and new_status == BookshelfStatus.DELETED:
            raise ValueError("Cannot delete the Basement bookshelf")

        if self.status == new_status:
            return  # No change

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        self.events.append(
            BookshelfStatusChanged(
                aggregate_id=self.id,
                library_id=self.library_id,
                old_status=self.status.value,
                new_status=new_status.value,
            )
        )

    def mark_as_pinned(self, pinned: bool = True) -> None:
        """Mark bookshelf as pinned or unpinned"""
        if self.is_pinned == pinned:
            return
        self.is_pinned = pinned
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_favorite(self, favorite: bool = True) -> None:
        """Mark bookshelf as favorite or unfavorite"""
        if self.is_favorite == favorite:
            return
        self.is_favorite = favorite
        self.updated_at = datetime.now(timezone.utc)

    def mark_deleted(self) -> None:
        """
        Mark bookshelf as deleted (soft delete)

        RULE-005: 删除操作遵循状态机
        Emits: BookshelfDeleted event
        """
        if self.type == BookshelfType.BASEMENT:
            raise ValueError("Cannot delete the Basement bookshelf")

        if self.status == BookshelfStatus.DELETED:
            return  # Already deleted

        self.status = BookshelfStatus.DELETED
        self.updated_at = datetime.now(timezone.utc)

        self.events.append(
            BookshelfDeleted(
                aggregate_id=self.id,
                library_id=self.library_id,
                name=self.name.value,
            )
        )

    def restore(self) -> None:
        """
        Restore a deleted bookshelf (from Basement view) to ACTIVE status

        Part of the unified deletion & recovery framework (ADR-038).

        BASEMENT-001: Parent Library must not be deleted (verified by UseCase before calling)
        BASEMENT-002: Restoration doesn't move data, just updates status

        Invariants:
        - Only deleted bookshelves can be restored
        - Sets status back to ACTIVE
        - Emits BookshelfStatusChanged event

        Raises:
        - ValueError: If bookshelf is not in DELETED status

        Events:
        - Emits BookshelfStatusChanged event
        """
        if self.status != BookshelfStatus.DELETED:
            raise ValueError(
                f"Cannot restore bookshelf {self.id}: status is {self.status}, "
                f"not DELETED"
            )

        self.status = BookshelfStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

        # Emit status change event
        self.events.append(
            BookshelfStatusChanged(
                aggregate_id=self.id,
                library_id=self.library_id,
                old_status=BookshelfStatus.DELETED.value,
                new_status=BookshelfStatus.ACTIVE.value,
            )
        )

    def mark_as_basement(self) -> None:
        """
        Mark this bookshelf as the special Basement (recycle bin)

        RULE-010: Basement 是特殊的书架类型，用于回收站功能
        """
        if self.type == BookshelfType.BASEMENT:
            return  # Already basement

        self.type = BookshelfType.BASEMENT
        self.updated_at = datetime.now(timezone.utc)

    # ========================================================================
    # Query Methods
    # ========================================================================

    @property
    def is_basement(self) -> bool:
        """Check if this bookshelf is the Basement (recycle bin)"""
        return self.type == BookshelfType.BASEMENT

    @property
    def is_active(self) -> bool:
        """Check if bookshelf is in ACTIVE status"""
        return self.status == BookshelfStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
        """Check if bookshelf is in ARCHIVED status"""
        return self.status == BookshelfStatus.ARCHIVED

    @property
    def is_deleted(self) -> bool:
        """Check if bookshelf is in DELETED status (soft deleted)"""
        return self.status == BookshelfStatus.DELETED

    @property
    def can_be_deleted(self) -> bool:
        """Check if bookshelf can be deleted"""
        return self.type != BookshelfType.BASEMENT

    def get_name_value(self) -> str:
        """Expose the primitive shelf name used by legacy callers."""
        return self.name.value
