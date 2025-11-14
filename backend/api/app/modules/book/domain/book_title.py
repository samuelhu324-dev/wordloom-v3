"""
BookTitle Value Object

Represents the title of a Book with validation rules.
"""

from dataclasses import dataclass
from shared.base import ValueObject


@dataclass(frozen=True)
class BookTitle(ValueObject):
    """Value object for Book title

    Invariants:
    - Cannot be empty or whitespace
    - Maximum 255 characters
    """
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Book title cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Book title cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value
