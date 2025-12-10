"""
Book Domain - Business logic for content containers with Blocks

Purpose:
- Represents content container under a Bookshelf
- Manages Block references (ordered list)
- Manages state: status, is_pinned, due_at, etc.
- Does NOT manage: preview_image (→ Media), usage_count (→ Chronicle)

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

class BookStatus(str, Enum):
    """Status of a Book"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================================================
# Domain Events
# ============================================================================

@dataclass
class BookCreated(DomainEvent):
    """Emitted when a new Book is created"""
    book_id: UUID
    bookshelf_id: UUID
    title: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookRenamed(DomainEvent):
    """Emitted when Book title is changed"""
    book_id: UUID
    old_title: str
    new_title: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookStatusChanged(DomainEvent):
    """Emitted when Book status changes"""
    book_id: UUID
    old_status: BookStatus
    new_status: BookStatus
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookDeleted(DomainEvent):
    """Emitted when Book is deleted"""
    book_id: UUID
    bookshelf_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BlocksUpdated(DomainEvent):
    """Emitted when Book's Blocks are updated"""
    book_id: UUID
    block_count: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookMovedToBookshelf(DomainEvent):
    """Emitted when Book is moved to a different Bookshelf"""
    book_id: UUID
    old_bookshelf_id: UUID
    new_bookshelf_id: UUID
    moved_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookMovedToBasement(DomainEvent):
    """Emitted when Book is moved to Basement (deleted)"""
    book_id: UUID
    old_bookshelf_id: UUID
    basement_bookshelf_id: UUID
    deleted_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


@dataclass
class BookRestoredFromBasement(DomainEvent):
    """Emitted when Book is restored from Basement"""
    book_id: UUID
    basement_bookshelf_id: UUID
    restored_to_bookshelf_id: UUID
    restored_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def aggregate_id(self) -> UUID:
        return self.book_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class BookTitle(ValueObject):
    """Value object for Book title"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Book title cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Book title cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BookSummary(ValueObject):
    """Value object for Book summary"""
    value: Optional[str] = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("Book summary cannot exceed 1000 characters")

    def __str__(self) -> str:
        return self.value or ""


# ============================================================================
# Aggregate Root
# ============================================================================

class Book(AggregateRoot):
    """
    Book Aggregate Root (独立聚合根)

    Invariants:
    - Book 通过 bookshelf_id FK 关联到 Bookshelf（不包含 Bookshelf 对象）
    - Book 通过 library_id FK 关联到 Library（用于权限检查）
    - Title 必须存在且 ≤ 255 字符
    - Summary 可选，≤ 1000 字符
    - Status 只能是 DRAFT / PUBLISHED / ARCHIVED / DELETED 之一
    - soft_deleted_at 用于标记 Basement 中的 Book

    Design Decision: 独立聚合根
    - 不直接包含 Block 对象（Block 通过 book_id FK 关联）
    - 通过 block_count 计数字段，而非持有集合
    - Service 层负责 Book 的转移和删除

    Business Rules:
    - 创建时带 title 和 bookshelf_id
    - 可转移到其他 Bookshelf（BookMovedToBookshelf 事件）
    - 删除时转移到 Basement（BookMovedToBasement 事件）
    - 可从 Basement 恢复（BookRestoredFromBasement 事件）
    """

    def __init__(
        self,
        book_id: UUID,
        bookshelf_id: UUID,
        library_id: UUID,
        title: BookTitle,
        summary: BookSummary = None,
        is_pinned: bool = False,
        due_at: Optional[datetime] = None,
        status: BookStatus = BookStatus.DRAFT,
        block_count: int = 0,
        soft_deleted_at: Optional[datetime] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = book_id
        self.bookshelf_id = bookshelf_id
        self.library_id = library_id  # ← 冗余 FK（用于权限检查）
        self.title = title
        self.summary = summary or BookSummary()
        self.is_pinned = is_pinned
        self.due_at = due_at
        self.status = status
        self.block_count = block_count
        self.soft_deleted_at = soft_deleted_at  # ← 标记是否在 Basement
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.events: List[DomainEvent] = []

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def create(
        cls,
        bookshelf_id: UUID,
        library_id: UUID,
        title: str,
        summary: Optional[str] = None,
    ) -> Book:
        """
        Factory method to create a new Book

        Args:
            bookshelf_id: ID of the parent Bookshelf
            library_id: ID of the parent Library (redundant FK for permission checks)
            title: Title of the Book
            summary: Optional summary

        Returns:
            New Book instance with BookCreated event

        Raises:
            ValueError: If title or summary invalid
        """
        book_id = uuid4()
        book_title = BookTitle(value=title)
        book_summary = BookSummary(value=summary)
        now = datetime.now(timezone.utc)

        book = cls(
            book_id=book_id,
            bookshelf_id=bookshelf_id,
            library_id=library_id,
            title=book_title,
            summary=book_summary,
            status=BookStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )

        book.emit(
            BookCreated(
                book_id=book_id,
                bookshelf_id=bookshelf_id,
                title=title,
                occurred_at=now,
            )
        )

        return book

    # ========================================================================
    # Business Methods
    # ========================================================================

    def rename(self, new_title: str) -> None:
        """Rename the Book"""
        new_book_title = BookTitle(value=new_title)

        if self.title.value == new_book_title.value:
            return

        old_title = self.title.value
        self.title = new_book_title
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BookRenamed(
                book_id=self.id,
                old_title=old_title,
                new_title=new_title,
                occurred_at=self.updated_at,
            )
        )

    def change_status(self, new_status: BookStatus) -> None:
        """Change Book status"""
        if self.status == new_status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BookStatusChanged(
                book_id=self.id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """Mark Book as deleted (soft delete)"""
        self.change_status(BookStatus.DELETED)
        now = datetime.now(timezone.utc)

        self.emit(
            BookDeleted(
                book_id=self.id,
                bookshelf_id=self.bookshelf_id,
                occurred_at=now,
            )
        )

    def move_to_bookshelf(self, new_bookshelf_id: UUID) -> None:
        """
        将 Book 转移到新的 Bookshelf（真实转移，不是复制）

        业务规则：
        1. Book 必须存在
        2. 新 Bookshelf 必须存在且可操作
        3. 不能转移到自己所在的 Bookshelf
        4. 发出 BookMovedToBookshelf 事件

        Args:
            new_bookshelf_id: 目标 Bookshelf 的 ID

        Raises:
            ValueError: 如果转移非法
        """
        if self.bookshelf_id == new_bookshelf_id:
            raise ValueError("Book is already in the target bookshelf")

        # 真实转移（一行代码）
        old_bookshelf_id = self.bookshelf_id
        self.bookshelf_id = new_bookshelf_id
        self.updated_at = datetime.now(timezone.utc)

        # 发出事件
        self.emit(BookMovedToBookshelf(
            book_id=self.id,
            old_bookshelf_id=old_bookshelf_id,
            new_bookshelf_id=new_bookshelf_id,
            moved_at=self.updated_at,
        ))

    def move_to_basement(self, basement_bookshelf_id: UUID) -> None:
        """
        将 Book 转移到 Basement（删除）

        这实际上是调用 move_to_bookshelf，但记录软删除时间

        Args:
            basement_bookshelf_id: Basement 的 Bookshelf ID
        """
        old_bookshelf_id = self.bookshelf_id
        now = datetime.now(timezone.utc)

        # 实际转移
        self.bookshelf_id = basement_bookshelf_id
        self.soft_deleted_at = now  # ← 标记为 Basement 中
        self.updated_at = now

        self.emit(BookMovedToBasement(
            book_id=self.id,
            old_bookshelf_id=old_bookshelf_id,
            basement_bookshelf_id=basement_bookshelf_id,
            deleted_at=now,
        ))

    def restore_from_basement(self, restore_to_bookshelf_id: UUID) -> None:
        """
        从 Basement 恢复 Book

        Args:
            restore_to_bookshelf_id: 恢复到的目标 Bookshelf ID
        """
        if self.soft_deleted_at is None:
            raise ValueError("Book is not in Basement")

        basement_id = self.bookshelf_id
        now = datetime.now(timezone.utc)

        # 转移回来
        self.bookshelf_id = restore_to_bookshelf_id
        self.soft_deleted_at = None  # ← 清除 Basement 标记
        self.updated_at = now

        self.emit(BookRestoredFromBasement(
            book_id=self.id,
            basement_bookshelf_id=basement_id,
            restored_to_bookshelf_id=restore_to_bookshelf_id,
            restored_at=now,
        ))

    def update_block_count(self, count: int) -> None:
        """Update block count (called when Blocks are modified)"""
        self.block_count = count
        self.updated_at = datetime.now(timezone.utc)

        self.emit(
            BlocksUpdated(
                book_id=self.id,
                block_count=count,
                occurred_at=self.updated_at,
            )
        )

    # ========================================================================
    # Query Methods (Simplified as Properties)
    # ========================================================================

    @property
    def is_draft(self) -> bool:
        """Check if Book is in draft status"""
        return self.status == BookStatus.DRAFT

    @property
    def is_published(self) -> bool:
        """Check if Book is published"""
        return self.status == BookStatus.PUBLISHED

    @property
    def is_archived(self) -> bool:
        """Check if Book is archived"""
        return self.status == BookStatus.ARCHIVED

    @property
    def is_deleted(self) -> bool:
        """Check if Book is deleted"""
        return self.status == BookStatus.DELETED

    @property
    def can_edit(self) -> bool:
        """Check if Book can be edited"""
        return self.status != BookStatus.DELETED

    @property
    def is_in_basement(self) -> bool:
        """检查是否在 Basement"""
        return self.soft_deleted_at is not None

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, bookshelf_id={self.bookshelf_id}, title={self.title.value})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
