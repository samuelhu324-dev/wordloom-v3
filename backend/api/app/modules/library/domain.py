"""
Library Domain Model

Library 是用户的唯一数据容器，所有 Bookshelves、Books、Blocks 的顶层聚合根。
"""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from pydantic import Field, validator

from backend.api.app.shared.base import AggregateRoot, DomainEvent


# ============================================
# Domain Events
# ============================================

class LibraryCreated(DomainEvent):
    """Library 被创建"""
    user_id: UUID
    library_name: str


class LibraryUpdated(DomainEvent):
    """Library 被更新"""
    user_id: UUID
    updated_fields: dict


# ============================================
# Aggregate Root: Library
# ============================================

class Library(AggregateRoot):
    """
    Aggregate Root: Library

    不变量（Invariants）:
    - RULE-001: 每个用户只能有一个 Library
    - RULE-002: Library 必须关联到有效的 User
    - RULE-003: Library 的名称不能为空
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 缓存字段（计算属性）
    bookshelf_count: int = 0
    total_books: int = 0
    total_blocks: int = 0

    @validator('name')
    def name_not_empty(cls, v):
        """验证 name 不能全为空格"""
        if v.strip() == "":
            raise ValueError("Library name cannot be empty or whitespace only")
        return v.strip()

    # ============================================
    # Domain Logic
    # ============================================

    @classmethod
    def create(cls, user_id: UUID, name: str) -> 'Library':
        """
        创建新的 Library

        Args:
            user_id: 用户 ID（RULE-002）
            name: Library 名称（RULE-003）

        Returns:
            新的 Library 实例

        Raises:
            ValueError: 如果参数无效
        """
        library = cls(user_id=user_id, name=name)

        # 触发 Domain Event
        library.events = [
            LibraryCreated(
                aggregate_id=library.id,
                user_id=user_id,
                library_name=name
            )
        ]

        return library

    def update_info(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """
        更新 Library 信息

        Args:
            name: 新的名称（可选）
            description: 新的描述（可选）
        """
        updated_fields = {}

        if name is not None and name != self.name:
            self.name = name
            updated_fields['name'] = name

        if description is not None and description != self.description:
            self.description = description
            updated_fields['description'] = description

        if updated_fields:
            self.updated_at = datetime.now()
            self.events = [
                LibraryUpdated(
                    aggregate_id=self.id,
                    user_id=self.user_id,
                    updated_fields=updated_fields
                )
            ]

    # ============================================
    # 查询方法（不改变状态）
    # ============================================

    def is_empty(self) -> bool:
        """检查 Library 是否为空"""
        return self.bookshelf_count == 0 and self.total_books == 0 and self.total_blocks == 0

    def get_summary(self) -> dict:
        """获取 Library 摘要"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "bookshelf_count": self.bookshelf_count,
            "total_books": self.total_books,
            "total_blocks": self.total_blocks,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================
# Domain Exceptions
# ============================================

class LibraryException(Exception):
    """Library Domain 的基类异常"""
    pass


class LibraryNotFoundError(LibraryException):
    """Library 不存在"""
    def __init__(self, library_id: UUID):
        self.library_id = library_id
        super().__init__(f"Library {library_id} not found")


class DuplicateLibraryError(LibraryException):
    """用户已有 Library（违反 RULE-001）"""
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        super().__init__(f"User {user_id} already has a Library")


class InvalidLibraryError(LibraryException):
    """Library 数据无效"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid Library: {reason}")