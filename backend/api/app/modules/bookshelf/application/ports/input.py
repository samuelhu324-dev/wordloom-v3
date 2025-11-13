"""
Bookshelf Input Ports - UseCase Interfaces

定义所有 Bookshelf UseCase 的接口契约，供 Router 调用。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class CreateBookshelfRequest:
    """创建 Bookshelf 的请求"""
    library_id: UUID
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


@dataclass
class ListBookshelvesRequest:
    """列出 Bookshelf 的请求"""
    library_id: UUID


@dataclass
class GetBookshelfRequest:
    """获取 Bookshelf 的请求"""
    bookshelf_id: UUID


@dataclass
class UpdateBookshelfRequest:
    """更新 Bookshelf 的请求"""
    bookshelf_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


@dataclass
class DeleteBookshelfRequest:
    """删除 Bookshelf 的请求"""
    bookshelf_id: UUID


@dataclass
class GetBasementRequest:
    """获取 Basement Bookshelf 的请求"""
    library_id: UUID


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class BookshelfResponse:
    """Bookshelf 的响应 DTO"""
    id: UUID
    library_id: UUID
    name: str
    description: Optional[str]
    color: Optional[str]
    is_basement: bool
    book_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, bookshelf) -> "BookshelfResponse":
        """从域对象转换"""
        return cls(
            id=bookshelf.id,
            library_id=bookshelf.library_id,
            name=bookshelf.name,
            description=bookshelf.description,
            color=bookshelf.color,
            is_basement=bookshelf.is_basement,
            book_count=bookshelf.book_count or 0,
            created_at=bookshelf.created_at.isoformat() if bookshelf.created_at else None,
            updated_at=bookshelf.updated_at.isoformat() if bookshelf.updated_at else None
        )


# ============================================================================
# UseCase Interfaces (Input Ports)
# ============================================================================

class CreateBookshelfUseCase(ABC):
    """创建 Bookshelf 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: CreateBookshelfRequest) -> BookshelfResponse:
        """执行创建 Bookshelf"""
        pass


class ListBookshelvesUseCase(ABC):
    """列出 Bookshelf 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ListBookshelvesRequest) -> List[BookshelfResponse]:
        """执行列出 Bookshelf"""
        pass


class GetBookshelfUseCase(ABC):
    """获取 Bookshelf 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetBookshelfRequest) -> BookshelfResponse:
        """执行获取 Bookshelf"""
        pass


class UpdateBookshelfUseCase(ABC):
    """更新 Bookshelf 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UpdateBookshelfRequest) -> BookshelfResponse:
        """执行更新 Bookshelf"""
        pass


class DeleteBookshelfUseCase(ABC):
    """删除 Bookshelf 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DeleteBookshelfRequest) -> None:
        """执行删除 Bookshelf"""
        pass


class GetBasementUseCase(ABC):
    """获取 Basement Bookshelf 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetBasementRequest) -> BookshelfResponse:
        """执行获取 Basement Bookshelf"""
        pass
