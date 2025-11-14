"""
Book Input Ports - UseCase Interfaces

定义所有 Book UseCase 的接口契约，供 Router 调用。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class CreateBookRequest:
    """创建 Book 的请求"""
    bookshelf_id: UUID
    library_id: UUID
    title: str
    summary: Optional[str] = None


@dataclass
class ListBooksRequest:
    """列出 Book 的请求"""
    bookshelf_id: Optional[UUID] = None
    library_id: Optional[UUID] = None
    include_deleted: bool = False
    skip: int = 0
    limit: int = 20


@dataclass
class GetBookRequest:
    """获取 Book 的请求"""
    book_id: UUID


@dataclass
class UpdateBookRequest:
    """更新 Book 的请求"""
    book_id: Optional[UUID] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None
    due_at: Optional[str] = None


@dataclass
class DeleteBookRequest:
    """删除 Book 的请求（RULE-012: Soft-delete to Basement）

    Args:
        book_id: Book ID to delete
        basement_bookshelf_id: Target bookshelf in Basement (typically derived from current bookshelf)
    """
    book_id: UUID
    basement_bookshelf_id: UUID


@dataclass
class RestoreBookRequest:
    """恢复 Book 的请求（RULE-013: Restore from Basement）

    Args:
        book_id: Book ID to restore
        target_bookshelf_id: Target bookshelf to restore book to (must be in same library)
    """
    book_id: UUID
    target_bookshelf_id: UUID


@dataclass
class ListDeletedBooksRequest:
    """列出已删除 Book 的请求"""
    bookshelf_id: Optional[UUID] = None
    library_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 20


@dataclass
class MoveBookRequest:
    """转移 Book 的请求（RULE-011）"""
    book_id: UUID
    target_bookshelf_id: UUID
    reason: Optional[str] = None


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class BookResponse:
    """Book 的响应 DTO"""
    id: UUID
    bookshelf_id: UUID
    library_id: UUID
    title: str
    summary: Optional[str]
    status: str
    block_count: int
    is_pinned: bool
    due_at: Optional[str]
    created_at: str
    updated_at: str
    soft_deleted_at: Optional[str]

    @classmethod
    def from_domain(cls, book) -> "BookResponse":
        """从域对象转换"""
        return cls(
            id=book.id,
            bookshelf_id=book.bookshelf_id,
            library_id=book.library_id,
            title=book.title.value if hasattr(book.title, 'value') else book.title,
            summary=book.summary.value if hasattr(book.summary, 'value') else book.summary,
            status=book.status.value if hasattr(book.status, 'value') else book.status,
            block_count=book.block_count or 0,
            is_pinned=book.is_pinned,
            due_at=book.due_at.isoformat() if book.due_at else None,
            created_at=book.created_at.isoformat() if book.created_at else None,
            updated_at=book.updated_at.isoformat() if book.updated_at else None,
            soft_deleted_at=book.soft_deleted_at.isoformat() if book.soft_deleted_at else None
        )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "bookshelf_id": str(self.bookshelf_id),
            "library_id": str(self.library_id),
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "block_count": self.block_count,
            "is_pinned": self.is_pinned,
            "due_at": self.due_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "soft_deleted_at": self.soft_deleted_at,
        }


@dataclass
class BookListResponse:
    """Book 列表响应 DTO"""
    items: List[BookResponse]
    total: int


# ============================================================================
# UseCase Interfaces (Input Ports)
# ============================================================================

class CreateBookUseCase(ABC):
    """创建 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: CreateBookRequest) -> BookResponse:
        """执行创建 Book"""
        pass


class ListBooksUseCase(ABC):
    """列出 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ListBooksRequest) -> BookListResponse:
        """执行列出 Book"""
        pass


class GetBookUseCase(ABC):
    """获取 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetBookRequest) -> BookResponse:
        """执行获取 Book"""
        pass


class UpdateBookUseCase(ABC):
    """更新 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UpdateBookRequest) -> BookResponse:
        """执行更新 Book"""
        pass


class DeleteBookUseCase(ABC):
    """删除 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DeleteBookRequest) -> None:
        """执行删除 Book"""
        pass


class RestoreBookUseCase(ABC):
    """恢复 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: RestoreBookRequest) -> BookResponse:
        """执行恢复 Book"""
        pass


class ListDeletedBooksUseCase(ABC):
    """列出已删除 Book 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ListDeletedBooksRequest) -> BookListResponse:
        """执行列出已删除 Book"""
        pass


class MoveBookUseCase(ABC):
    """转移 Book 的 UseCase 接口（RULE-011）"""

    @abstractmethod
    async def execute(self, request: MoveBookRequest) -> BookResponse:
        """执行转移 Book 到另一个 Bookshelf"""
        pass
