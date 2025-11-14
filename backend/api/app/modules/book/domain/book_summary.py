"""
BookSummary Value Object

Represents the summary of a Book with validation rules.
"""

from dataclasses import dataclass
from typing import Optional
from shared.base import ValueObject


@dataclass(frozen=True)
class BookSummary(ValueObject):
    """Value object for Book summary

    Invariants:
    - Optional (can be None)
    - Maximum 1000 characters if provided
    """
    value: Optional[str] = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("Book summary cannot exceed 1000 characters")

    def __str__(self) -> str:
        return self.value or ""
