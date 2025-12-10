"""Helpers for Book maturity state changes and derivations."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from ...domain import Book, BookMaturity
from ...domain.services import BookMaturityScoreInput

MATURITY_SEQUENCE: List[BookMaturity] = [
    BookMaturity.SEED,
    BookMaturity.GROWING,
    BookMaturity.STABLE,
    BookMaturity.LEGACY,
]


def normalize_maturity(value) -> BookMaturity:
    """Return BookMaturity enum regardless of str/enum input."""
    if isinstance(value, BookMaturity):
        return value

    candidate = getattr(value, "value", value)
    normalized = str(candidate)
    if normalized.startswith("BookMaturity."):
        normalized = normalized.split(".", 1)[1]
    return BookMaturity(normalized.lower())


def derive_maturity_from_score(score: int) -> BookMaturity:
    """Map numeric score to maturity bucket (Seed/Growing/Stable)."""
    score = int(score or 0)
    if score < 30:
        return BookMaturity.SEED
    if score < 60:
        return BookMaturity.GROWING
    if score < 90:
        return BookMaturity.STABLE
    return BookMaturity.LEGACY


def transition_book_maturity(book: Book, target: BookMaturity) -> tuple[BookMaturity, BookMaturity]:
    """Transition book.maturity to target using sequential state machine."""
    current = normalize_maturity(getattr(book, "maturity", BookMaturity.SEED))
    target = normalize_maturity(target)
    if current == target:
        return current, target

    path = _build_transition_path(current, target)
    for step in path[1:]:
        book.change_maturity(step)
    return current, target


def _build_transition_path(current: BookMaturity, target: BookMaturity) -> List[BookMaturity]:
    if current == target:
        return [current]

    current_index = MATURITY_SEQUENCE.index(current)
    target_index = MATURITY_SEQUENCE.index(target)

    if current_index < target_index:
        return MATURITY_SEQUENCE[current_index : target_index + 1]

    descending = MATURITY_SEQUENCE[target_index : current_index + 1]
    return list(reversed(descending))


def build_score_input(
    book: Book,
    *,
    tag_count: Optional[int] = None,
    block_type_count: Optional[int] = None,
    block_count: Optional[int] = None,
    open_todo_count: Optional[int] = None,
    operations_bonus: Optional[int] = None,
    cover_icon: Optional[str] = None,
    visit_count_90d: Optional[int] = None,
    last_content_edit_at: Optional[datetime] = None,
) -> BookMaturityScoreInput:
    """Construct score input with graceful fallbacks to book snapshots."""

    def _first_available(*values: Optional[int]) -> int:
        for value in values:
            if value is None:
                continue
            return int(value)
        return 0

    return BookMaturityScoreInput(
        book=book,
        tag_count=_first_available(tag_count, getattr(book, "tag_count_snapshot", None)),
        block_type_count=_first_available(block_type_count, getattr(book, "block_type_count", None)),
        block_count=_first_available(block_count, getattr(book, "block_count", None)),
        open_todo_count=_first_available(open_todo_count, getattr(book, "open_todo_snapshot", None)),
        lucide_cover_icon=cover_icon or getattr(book, "cover_icon", None),
        operations_bonus=_first_available(operations_bonus, getattr(book, "operations_bonus", None)),
        visit_count_90d=_first_available(visit_count_90d, getattr(book, "visit_count_90d", None)),
        last_content_edit_at=last_content_edit_at or getattr(book, "last_content_edit_at", getattr(book, "updated_at", None)),
    )
