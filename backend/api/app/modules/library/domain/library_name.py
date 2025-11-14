"""
Library Name Value Object

Responsibility:
- Encapsulate name validation logic
- Enforce invariant RULE-003: name must be 1-255 characters, non-empty
- Immutable (frozen dataclass)

Cross-Reference:
- DDD_RULES.yaml: RULE-003
- HEXAGONAL_RULES.yaml: Value Objects section
"""

from dataclasses import dataclass
from typing import Optional

from shared.base import ValueObject


@dataclass(frozen=True)
class LibraryName(ValueObject):
    """
    Value Object representing a Library's name

    Invariants (RULE-003):
    - Non-empty after stripping whitespace
    - Maximum 255 characters
    - Immutable (frozen)
    - Comparable by value (dataclass equality)
    """

    value: str

    def __post_init__(self) -> None:
        """
        Validate name on construction (Fail Fast pattern)

        Raises:
            ValueError: If validation fails
            - Empty or whitespace-only string
            - Exceeds 255 characters
        """
        # Strip whitespace from input for comparison
        stripped_value = self.value.strip() if isinstance(self.value, str) else ""

        # 检查非空
        if not stripped_value:
            raise ValueError(
                "Library name cannot be empty or whitespace-only"
            )

        # 检查长度（使用原始值的长度，但验证逻辑基于 stripped）
        if len(self.value) > 255:
            raise ValueError(
                "Library name cannot exceed 255 characters. "
                f"Provided: {len(self.value)} characters"
            )

        # 使用 __dict__ 更新来绕过 frozen dataclass 限制（仅在 __post_init__ 中）
        # 将值 strip 后存储
        object.__setattr__(self, 'value', stripped_value)

    def __str__(self) -> str:
        """String representation of the name"""
        return self.value

    def __repr__(self) -> str:
        """Debug representation"""
        return f"LibraryName(value='{self.value}')"

    # ============================================================================
    # Value Object Methods
    # ============================================================================

    def equals(self, other: object) -> bool:
        """
        Compare two LibraryName objects by value

        Note: Dataclass equality is already value-based, but this method
        is kept for explicit Value Object pattern documentation.
        """
        if not isinstance(other, LibraryName):
            return False
        return self.value == other.value

    def is_empty(self) -> bool:
        """Check if name is empty or whitespace-only"""
        return not self.value or not self.value.strip()

    def length(self) -> int:
        """Get name length"""
        return len(self.value)

    def truncate(self, max_length: int) -> "LibraryName":
        """
        Create a new LibraryName with truncated value

        Args:
            max_length: Maximum length

        Returns:
            New LibraryName instance (if truncation is needed and valid)

        Raises:
            ValueError: If truncated value is invalid
        """
        if len(self.value) <= max_length:
            return self

        truncated = self.value[:max_length].strip()
        return LibraryName(value=truncated)