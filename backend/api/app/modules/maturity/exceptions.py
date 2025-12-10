"""Custom exceptions for the maturity module."""
from __future__ import annotations

from uuid import UUID


class BookMaturitySourceNotFound(Exception):
    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"Book #{book_id} not found for maturity pipeline")
        self.book_id = book_id


class MaturitySnapshotNotFound(Exception):
    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"No maturity snapshots for book #{book_id}")
        self.book_id = book_id
