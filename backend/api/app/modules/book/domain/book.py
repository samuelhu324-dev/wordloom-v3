"""
Book Aggregate Root

Core business logic for content containers with Blocks.

Purpose:
- Represents content container under a Bookshelf
- Manages Block references (ordered list via block_count)
- Manages state: status, maturity lifecycle, is_pinned, due_at, etc.
- Does NOT manage: preview_image (→ Media), usage_count (→ Chronicle)

Architecture:
- Pure domain layer with zero infrastructure dependencies
- Emits DomainEvents on state changes
- Uses Repository pattern for persistence abstraction

Invariants:
- Book associated to Bookshelf through bookshelf_id FK (not embedded object)
- Book associated to Library through library_id FK (for permission checks)
- Title must exist and be ≤ 255 characters
- Summary optional, ≤ 1000 characters
- Status must be DRAFT | PUBLISHED | ARCHIVED | DELETED
- Maturity must be SEED | GROWING | STABLE | LEGACY
- soft_deleted_at marks Books in Basement view
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import List, Optional
from uuid import UUID, uuid4

from api.app.shared.base import AggregateRoot, DomainEvent
from .book_title import BookTitle
from .book_summary import BookSummary
from .exceptions import InvalidBookMaturityTransitionError, InvalidBookDataError
from .events import (
    BookStatus,
    BookMaturity,
    BookCreated,
    BookRenamed,
    BookStatusChanged,
    BookMaturityChanged,
    BookDeleted,
    BlocksUpdated,
    BookMovedToBookshelf,
    BookMovedToBasement,
    BookRestoredFromBasement,
)


ALLOWED_MATURITY_TRANSITIONS = {
    BookMaturity.SEED: {BookMaturity.GROWING},
    BookMaturity.GROWING: {BookMaturity.SEED, BookMaturity.STABLE},
    BookMaturity.STABLE: {BookMaturity.GROWING, BookMaturity.LEGACY},
    BookMaturity.LEGACY: {BookMaturity.GROWING, BookMaturity.STABLE},
}

COVER_ICON_PATTERN = re.compile(r"^[a-z0-9\-]+$")
MAX_COVER_ICON_LENGTH = 64


class Book(AggregateRoot):
    """
    Book Aggregate Root (独立聚合根)

    Design Decision: Independent aggregate
    - Does NOT directly contain Block objects (Blocks associated via book_id FK)
    - Uses block_count field for counting, not collection holding
    - Service layer responsible for Book transfers and deletions

    Business Rules:
    - Created with title and bookshelf_id
    - Can transfer to other Bookshelf (BookMovedToBookshelf event, RULE-011)
    - Deletion = transfer to Basement (BookMovedToBasement event, RULE-012)
    - Can restore from Basement (BookRestoredFromBasement event, RULE-013)
    """

    def __init__(
        self,
        book_id: UUID,
        bookshelf_id: UUID,
        library_id: UUID,
        title: BookTitle,
        summary: BookSummary = None,
        cover_icon: Optional[str] = None,
        cover_media_id: Optional[UUID] = None,
        is_pinned: bool = False,
        due_at: Optional[datetime] = None,
        status: BookStatus = BookStatus.DRAFT,
        maturity: BookMaturity = BookMaturity.SEED,
        block_count: int = 0,
        block_type_count: int = 0,
        tag_count_snapshot: int = 0,
        open_todo_snapshot: int = 0,
        operations_bonus: int = 0,
        maturity_score: int = 0,
        legacy_flag: bool = False,
        manual_maturity_override: bool = False,
        manual_maturity_reason: Optional[str] = None,
        last_visited_at: Optional[datetime] = None,
        visit_count_90d: int = 0,
        last_content_edit_at: Optional[datetime] = None,
        soft_deleted_at: Optional[datetime] = None,
        previous_bookshelf_id: Optional[UUID] = None,
        moved_to_basement_at: Optional[datetime] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        super().__init__()
        self.id = book_id
        self.bookshelf_id = bookshelf_id
        self.library_id = library_id  # ← Redundant FK (for permission checks)
        self.title = title
        self.summary = summary or BookSummary()
        self.cover_icon = self._normalize_cover_icon(cover_icon)
        self.cover_media_id = cover_media_id
        self.is_pinned = is_pinned
        self.due_at = due_at
        self.status = status
        self.maturity = maturity
        self.block_count = block_count
        self.block_type_count = block_type_count or 0
        self.tag_count_snapshot = tag_count_snapshot or 0
        self.open_todo_snapshot = open_todo_snapshot or 0
        self.operations_bonus = operations_bonus or 0
        self.maturity_score = maturity_score or 0
        self.legacy_flag = bool(legacy_flag)
        self.manual_maturity_override = bool(manual_maturity_override)
        self.manual_maturity_reason = manual_maturity_reason
        self.last_visited_at = last_visited_at
        self.visit_count_90d = visit_count_90d or 0
        self.soft_deleted_at = soft_deleted_at  # ← Marks if in Basement
        self.previous_bookshelf_id = previous_bookshelf_id
        self.moved_to_basement_at = moved_to_basement_at
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.last_content_edit_at = (
            last_content_edit_at
            or getattr(self, "last_content_edit_at", None)
            or self.updated_at
        )
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
        cover_icon: Optional[str] = None,
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
            cover_icon=cover_icon,
            status=BookStatus.DRAFT,
            maturity=BookMaturity.SEED,
            created_at=now,
            updated_at=now,
            last_content_edit_at=now,
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
        self._mark_content_edit()

        self.emit(
            BookRenamed(
                book_id=self.id,
                old_title=old_title,
                new_title=new_title,
                occurred_at=self.updated_at,
            )
        )

    # Compatibility alias for legacy callers
    def update_title(self, new_title: str) -> None:
        """Alias for rename to preserve legacy API usage"""
        self.rename(new_title)

    def update_summary(self, new_summary: Optional[str]) -> None:
        """Update the Book summary value object"""
        summary_vo = BookSummary(value=new_summary)
        if self.summary == summary_vo:
            return

        self.summary = summary_vo
        self.updated_at = datetime.now(timezone.utc)
        self._mark_content_edit()

    # Backward compatible alias (description historically used)
    def update_description(self, new_description: Optional[str]) -> None:
        """Alias for update_summary for backwards compatibility"""
        self.update_summary(new_description)

    def update_cover_icon(self, new_cover_icon: Optional[str]) -> None:
        """Set or clear the Lucide cover icon name"""
        normalized = self._normalize_cover_icon(new_cover_icon)
        if self.cover_icon == normalized:
            return

        self.cover_icon = normalized
        self.updated_at = datetime.now(timezone.utc)
        self._mark_content_edit()

    def set_cover_media(self, media_id: Optional[UUID]) -> None:
        """Assign or clear uploaded cover media (stable-only)."""
        if media_id is None:
            if self.cover_media_id is None:
                return
            self.cover_media_id = None
            self.updated_at = datetime.now(timezone.utc)
            self._mark_content_edit()
            return

        if not self._can_use_cover_media():
            raise InvalidBookDataError("只有 Stable 阶段的书籍才能设置封面图")

        if self.cover_media_id == media_id:
            return

        self.cover_media_id = media_id
        self.updated_at = datetime.now(timezone.utc)
        self._mark_content_edit()

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

    def change_maturity(self, new_maturity: BookMaturity) -> None:
        """Change Book maturity lifecycle"""
        if isinstance(new_maturity, str):
            new_maturity = BookMaturity(new_maturity)
        if self.maturity == new_maturity:
            return

        self._assert_maturity_transition(new_maturity)
        old_maturity = self.maturity
        self.maturity = new_maturity
        self.updated_at = datetime.now(timezone.utc)
        self._auto_revoke_cover_media()

        self.emit(
            BookMaturityChanged(
                book_id=self.id,
                old_maturity=old_maturity,
                new_maturity=new_maturity,
                occurred_at=self.updated_at,
            )
        )

    def mark_growing(self) -> None:
        """Advance Book to GROWING maturity"""
        self.change_maturity(BookMaturity.GROWING)

    def mark_stable(self) -> None:
        """Advance Book to STABLE maturity"""
        self.change_maturity(BookMaturity.STABLE)

    def mark_legacy(self) -> None:
        """Advance Book to LEGACY maturity"""
        self.change_maturity(BookMaturity.LEGACY)
        self.legacy_flag = True

    def set_pinned(self, pinned: bool) -> None:
        """Toggle Book pinned state while keeping updated timestamp."""
        normalized = bool(pinned)
        if self.is_pinned == normalized:
            return

        self.is_pinned = normalized
        self.updated_at = datetime.now(timezone.utc)

    def restore_from_legacy(self, target: BookMaturity = BookMaturity.STABLE) -> None:
        """Restore a legacy Book to an active maturity state"""
        if isinstance(target, str):
            target = BookMaturity(target)
        if self.maturity != BookMaturity.LEGACY:
            raise InvalidBookMaturityTransitionError(
                book_id=self.id,
                current=self.maturity.value if isinstance(self.maturity, BookMaturity) else str(self.maturity),
                target=target.value if isinstance(target, BookMaturity) else str(target),
            )
        self.change_maturity(target)
        self.legacy_flag = False
        self.manual_maturity_override = False

    def _assert_maturity_transition(self, target: BookMaturity) -> None:
        """Validate maturity state machine transitions"""
        current = self.maturity
        if isinstance(current, str):
            current_enum = BookMaturity(current)
            self.maturity = current_enum
        else:
            current_enum = current
        allowed = ALLOWED_MATURITY_TRANSITIONS.get(current_enum, set())
        if target not in allowed:
            raise InvalidBookMaturityTransitionError(
                book_id=self.id,
                current=current_enum.value if isinstance(current_enum, BookMaturity) else str(current_enum),
                target=target.value if isinstance(target, BookMaturity) else str(target),
            )

    def _mark_content_edit(self) -> None:
        """Keep last content edit timestamp in sync with updated_at."""
        self.last_content_edit_at = self.updated_at

    def _can_use_cover_media(self) -> bool:
        maturity = self.maturity
        if not isinstance(maturity, BookMaturity):
            maturity = BookMaturity(maturity)
        if maturity != BookMaturity.STABLE:
            return False
        if getattr(self, "legacy_flag", False):
            return False
        return True

    def _auto_revoke_cover_media(self) -> None:
        if self.cover_media_id is None:
            return
        if self._can_use_cover_media():
            return
        self.cover_media_id = None
        self._mark_content_edit()

    def mark_deleted(self, deleted_at: Optional[datetime] = None) -> None:
        """Mark Book as deleted (Basement hard delete guard)."""
        if not self.is_in_basement:
            raise InvalidBookDataError("Book must be in Basement before deletion")

        now = deleted_at or datetime.now(timezone.utc)
        self.change_status(BookStatus.DELETED)
        self.updated_at = now

        self.emit(
            BookDeleted(
                book_id=self.id,
                bookshelf_id=self.bookshelf_id,
                occurred_at=now,
            )
        )

    def move_to_bookshelf(self, new_bookshelf_id: UUID) -> None:
        """
        Transfer Book to new Bookshelf (真实转移，不是复制)

        Business Rules:
        1. Book must exist
        2. New Bookshelf must exist and be accessible
        3. Cannot transfer to current bookshelf
        4. Emits BookMovedToBookshelf event (RULE-011)

        Args:
            new_bookshelf_id: Target Bookshelf ID

        Raises:
            ValueError: If transfer is illegal
        """
        if self.bookshelf_id == new_bookshelf_id:
            raise ValueError("Book is already in the target bookshelf")

        # Actual transfer
        old_bookshelf_id = self.bookshelf_id
        self.bookshelf_id = new_bookshelf_id
        self.updated_at = datetime.now(timezone.utc)

        # Emit event
        self.emit(BookMovedToBookshelf(
            book_id=self.id,
            old_bookshelf_id=old_bookshelf_id,
            new_bookshelf_id=new_bookshelf_id,
            moved_at=self.updated_at,
        ))

    def move_to_basement(self, basement_bookshelf_id: UUID) -> None:
        """
        Transfer Book to Basement (deletion via soft delete, RULE-012)

        This is actually a move to Basement bookshelf with soft_deleted_at marked.

        Args:
            basement_bookshelf_id: Basement Bookshelf ID
        """
        if self.is_in_basement:
            raise InvalidBookDataError("Book is already in Basement")

        old_bookshelf_id = self.bookshelf_id
        now = datetime.now(timezone.utc)

        # Actual transfer
        self.previous_bookshelf_id = old_bookshelf_id
        self.bookshelf_id = basement_bookshelf_id
        self.soft_deleted_at = now  # ← Mark as in Basement
        self.moved_to_basement_at = now
        self.updated_at = now

        self.emit(BookMovedToBasement(
            book_id=self.id,
            old_bookshelf_id=old_bookshelf_id,
            basement_bookshelf_id=basement_bookshelf_id,
            deleted_at=now,
        ))

    def restore_from_basement(self, restore_to_bookshelf_id: Optional[UUID] = None) -> None:
        """
        Restore Book from Basement (RULE-013)

        Args:
            restore_to_bookshelf_id: Target Bookshelf ID for restoration
        """
        if self.soft_deleted_at is None:
            raise InvalidBookDataError("Book is not in Basement")

        target_bookshelf_id = restore_to_bookshelf_id or self.previous_bookshelf_id
        if target_bookshelf_id is None:
            raise InvalidBookDataError("No target bookshelf available for restoration")

        basement_id = self.bookshelf_id
        now = datetime.now(timezone.utc)

        # Transfer back
        self.bookshelf_id = target_bookshelf_id
        self.soft_deleted_at = None  # ← Clear Basement marker
        self.previous_bookshelf_id = None
        self.moved_to_basement_at = None
        self.updated_at = now

        self.emit(BookRestoredFromBasement(
            book_id=self.id,
            basement_bookshelf_id=basement_id,
            restored_to_bookshelf_id=target_bookshelf_id,
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

    @staticmethod
    def _normalize_cover_icon(value: Optional[str]) -> Optional[str]:
        """Validate cover icon input (Plan88 POLICY-BOOK-COVER-ICON-LUCIDE)."""
        if value is None:
            return None

        normalized = value.strip().lower()
        if not normalized:
            return None
        if len(normalized) > MAX_COVER_ICON_LENGTH:
            raise InvalidBookDataError(
                f"cover_icon exceeds {MAX_COVER_ICON_LENGTH} characters"
            )
        if not COVER_ICON_PATTERN.match(normalized):
            raise InvalidBookDataError(
                "cover_icon must contain lowercase letters, numbers, or hyphen"
            )
        return normalized
