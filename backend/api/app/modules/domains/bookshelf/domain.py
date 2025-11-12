"""
Bookshelf Domain - Business logic for organizing Books

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

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Enums
# ============================================================================

class BookshelfType(str, Enum):
    """Type of Bookshelf"""
    NORMAL = "normal"
    BASEMENT = "basement"  # ← 特殊类型：回收站


class BookshelfStatus(str, Enum):
    """Status of a Bookshelf"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BookshelfCreated(DomainEvent):
    """Emitted when a new Bookshelf is created"""
    bookshelf_id: UUID
    library_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfRenamed(DomainEvent):
    """Emitted when Bookshelf is renamed"""
    bookshelf_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfStatusChanged(DomainEvent):
    """Emitted when Bookshelf status changes (active/archived/deleted)"""
    bookshelf_id: UUID
    old_status: BookshelfStatus
    new_status: BookshelfStatus
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfDeleted(DomainEvent):
    """Emitted when Bookshelf is deleted (soft delete)"""
    bookshelf_id: UUID
    library_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class BookshelfName(ValueObject):
    """Value object for Bookshelf name"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Bookshelf name cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Bookshelf name cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BookshelfDescription(ValueObject):
    """Value object for Bookshelf description"""
    value: Optional[str] = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("Bookshelf description cannot exceed 1000 characters")

    def __str__(self) -> str:
        return self.value or ""


# ============================================================================
# Aggregate Root
# ============================================================================

class Bookshelf(AggregateRoot):
    """
    Bookshelf Aggregate Root (独立聚合根)

    Invariants:
    - Bookshelf 通过 library_id FK 关联到 Library（不包含 Library 对象）
    - Name 必须存在且 ≤ 255 字符
    - Status 只能是 ACTIVE / ARCHIVED / DELETED 之一
    - Type 用于区分普通书架与 Basement（回收站）
    - Bookshelf 不直接包含 Books（Books 通过 bookshelf_id FK 关联）

    Design Decision: 独立聚合根
    - 每个聚合（Library/Bookshelf/Book/Block）都是独立的根
    - 通过 FK 关联，而非对象包含
    - 避免大型对象锁和并发争用
    - Service 层负责跨聚合协调

    Business Rules:
    - 创建时带 initial name 和 library_id
    - 名称可更新（BookshelfRenamed 事件）
    - 状态可更新（BookshelfStatusChanged 事件）
    - Pin/Favorite 在 Service 层处理（暂不发出事件）
    - Basement 类型的 Bookshelf 隐藏且不能删除
    """

    def __init__(
        self,
        bookshelf_id: UUID,
        library_id: UUID,
        name: BookshelfName,
        description: BookshelfDescription = None,
        bookshelf_type: BookshelfType = BookshelfType.NORMAL,
        is_hidden: bool = False,
        is_pinned: bool = False,
        pinned_at: Optional[datetime] = None,
        is_favorite: bool = False,
        status: BookshelfStatus = BookshelfStatus.ACTIVE,
        book_count: int = 0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = bookshelf_id
        self.library_id = library_id  # ← FK（不是 Library 对象）
        self.name = name
        self.description = description or BookshelfDescription()
        self.type = bookshelf_type  # ← NORMAL or BASEMENT
        self.is_hidden = is_hidden  # ← Basement 设为 True
        self.is_pinned = is_pinned
        self.pinned_at = pinned_at
        self.is_favorite = is_favorite
        self.status = status
        self.book_count = book_count
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        library_id: UUID,
        name: str,
        description: Optional[str] = None,
    ) -> Bookshelf:
        """
        Factory method to create a new Bookshelf

        Args:
            library_id: ID of the parent Library
            name: Name of the Bookshelf
            description: Optional description

        Returns:
            New Bookshelf instance with BookshelfCreated event

        Raises:
            ValueError: If name or description invalid
        """
        bookshelf_id = uuid4()
        bookshelf_name = BookshelfName(value=name)
        bookshelf_desc = BookshelfDescription(value=description)
        now = datetime.now(timezone.utc)

        bookshelf = cls(
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            name=bookshelf_name,
            description=bookshelf_desc,
            status=BookshelfStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        bookshelf.emit(
            BookshelfCreated(
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                name=name,
                occurred_at=now,
            )
        )

        return bookshelf

    # ========================================================================
    # Business Methods - Name Management
    # ========================================================================

    def rename(self, new_name: str) -> None:
        """Rename the Bookshelf"""
        new_bookshelf_name = BookshelfName(value=new_name)

        if self.name.value == new_bookshelf_name.value:
            return

        old_name = self.name.value
        self.name = new_bookshelf_name
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BookshelfRenamed(
                bookshelf_id=self.id,
                old_name=old_name,
                new_name=new_name,
                occurred_at=self.updated_at,
            )
        )

    # ========================================================================
    # Business Methods - Status Management (Core)
    # ========================================================================

    def change_status(self, new_status: BookshelfStatus) -> None:
        """Change Bookshelf status (不变性约束：Basement 不能被删除)"""
        if self.status == new_status:
            return

        if self.type == BookshelfType.BASEMENT and new_status == BookshelfStatus.DELETED:
            raise ValueError("Cannot delete Basement Bookshelf")

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BookshelfStatusChanged(
                bookshelf_id=self.id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """Mark Bookshelf as deleted (软删除)"""
        self.change_status(BookshelfStatus.DELETED)
        now = datetime.now(timezone.utc)

        self.emit(
            BookshelfDeleted(
                bookshelf_id=self.id,
                library_id=self.library_id,
                occurred_at=now,
            )
        )

    # ========================================================================
    # Basement-specific Methods
    # ========================================================================

    @property
    def is_basement(self) -> bool:
        """检查是否为 Basement（回收站）"""
        return self.type == BookshelfType.BASEMENT

    def mark_as_basement(self) -> None:
        """标记为 Basement（仅系统调用，在创建时使用）"""
        if self.type != BookshelfType.NORMAL:
            raise ValueError("Cannot convert non-normal shelf to basement")
        self.type = BookshelfType.BASEMENT
        self.is_hidden = True
        self.updated_at = datetime.now(timezone.utc)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def __repr__(self) -> str:
        return f"<Bookshelf(id={self.id}, library_id={self.library_id}, name={self.name.value}, status={self.status})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bookshelf):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
