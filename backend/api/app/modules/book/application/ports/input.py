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
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None


@dataclass
class ListBooksRequest:
    """列出 Book 的请求"""
    bookshelf_id: UUID
    skip: int = 0
    limit: int = 20


@dataclass
class GetBookRequest:
    """获取 Book 的请求"""
    book_id: UUID


@dataclass
class UpdateBookRequest:
    """更新 Book 的请求"""
    book_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None


@dataclass
class DeleteBookRequest:
    """删除 Book 的请求"""
    book_id: UUID


@dataclass
class RestoreBookRequest:
    """恢复 Book 的请求"""
    book_id: UUID


@dataclass
class ListDeletedBooksRequest:
    """列出已删除 Book 的请求"""
    skip: int = 0
    limit: int = 20


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class BookResponse:
    """Book 的响应 DTO"""
    id: UUID
    bookshelf_id: UUID
    title: str
    description: Optional[str]
    cover_image_url: Optional[str]
    block_count: int
    created_at: str
    updated_at: str
    soft_deleted_at: Optional[str]

    @classmethod
    def from_domain(cls, book) -> "BookResponse":
        """从域对象转换"""
        return cls(
            id=book.id,
            bookshelf_id=book.bookshelf_id,
            title=book.title,
            description=book.description,
            cover_image_url=book.cover_image_url,
            block_count=book.block_count or 0,
            created_at=book.created_at.isoformat() if book.created_at else None,
            updated_at=book.updated_at.isoformat() if book.updated_at else None,
            soft_deleted_at=book.soft_deleted_at.isoformat() if book.soft_deleted_at else None
        )


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
