"""
Bookshelf Description - Value Object

Purpose:
- Encapsulates BookshelfDescription validation logic
- Optional field for bookshelf metadata
- Ensures immutability and type safety

Invariants:
- Description must be ≤ 1000 characters (if present)
- Can be None (optional)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from api.app.shared.base import ValueObject


@dataclass(frozen=True)
class BookshelfDescription(ValueObject):
    """
    BookshelfDescription Value Object

    Invariant: 描述文本长度必须 ≤ 1000 字符（可选字段）

    Design:
    - Immutable (frozen=True)
    - Optional (can be None)
    - Comparable by value
    - Hashable
    """

    value: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate description on creation"""
        if self.value is not None:
            # Trim whitespace
            trimmed = self.value.strip() if self.value else None

            if trimmed == "":
                # Empty string treated as None
                object.__setattr__(self, "value", None)
                return

            if len(trimmed) > 1000:
                raise ValueError(
                    f"Bookshelf description must not exceed 1000 characters (got {len(trimmed)})"
                )

            # Normalize: store trimmed value
            object.__setattr__(self, "value", trimmed)

    def __eq__(self, other: object) -> bool:
        """Compare by value"""
        if not isinstance(other, BookshelfDescription):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash by value"""
        return hash(self.value)

    def __str__(self) -> str:
        """String representation"""
        return self.value or ""

    def __repr__(self) -> str:
        """Developer representation"""
        return f"BookshelfDescription({self.value!r})"

    def is_empty(self) -> bool:
        """Check if description is empty or None"""
        return self.value is None or self.value == ""

    def contains(self, substring: str, case_insensitive: bool = False) -> bool:
        """
        Check if description contains substring

        Args:
            substring: String to search for
            case_insensitive: If True, case-insensitive comparison

        Returns:
            True if substring found in description, False if description is empty
        """
        if self.value is None:
            return False

        if case_insensitive:
            return substring.lower() in self.value.lower()
        return substring in self.value
