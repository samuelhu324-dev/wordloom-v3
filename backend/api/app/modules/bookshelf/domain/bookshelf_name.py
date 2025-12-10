"""
Bookshelf Name - Value Object

Purpose:
- Encapsulates BookshelfName validation logic
- Ensures immutability and type safety
- Used by Bookshelf aggregate root

Invariants:
- Name must not be empty
- Name must be ≤ 255 characters
- Equals and hashable for use in collections
"""

from __future__ import annotations
from dataclasses import dataclass
from api.app.shared.base import ValueObject


@dataclass(frozen=True)
class BookshelfName(ValueObject):
    """
    BookshelfName Value Object

    Invariant (RULE-006): 书架名称长度必须 1-255 字符

    Design:
    - Immutable (frozen=True)
    - Comparable by value
    - Hashable
    """

    value: str

    def __post_init__(self) -> None:
        """Validate name on creation"""
        # Trim whitespace
        trimmed = self.value.strip() if self.value else ""

        # Use object.__setattr__ to set frozen dataclass field
        if not trimmed:
            raise ValueError("Bookshelf name cannot be empty")

        if len(trimmed) > 255:
            raise ValueError(
                f"Bookshelf name must not exceed 255 characters (got {len(trimmed)})"
            )

        # Normalize: store trimmed value
        object.__setattr__(self, "value", trimmed)

    def __eq__(self, other: object) -> bool:
        """Compare by value"""
        if not isinstance(other, BookshelfName):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash by value"""
        return hash(self.value)

    def __str__(self) -> str:
        """String representation"""
        return self.value

    def __repr__(self) -> str:
        """Developer representation"""
        return f"BookshelfName({self.value!r})"

    def contains(self, substring: str, case_insensitive: bool = False) -> bool:
        """
        Check if name contains substring

        Args:
            substring: String to search for
            case_insensitive: If True, case-insensitive comparison

        Returns:
            True if substring found in name
        """
        if case_insensitive:
            return substring.lower() in self.value.lower()
        return substring in self.value
