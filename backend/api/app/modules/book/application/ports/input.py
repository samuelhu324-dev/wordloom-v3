"""
Book Input Ports - UseCase Interfaces

定义所有 Book UseCase 的接口契约，供 Router 调用。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from ..models.maturity import BookMaturityMutationResult


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
    cover_icon: Optional[str] = None
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class ListBooksRequest:
    """列出 Book 的请求"""
    bookshelf_id: Optional[UUID] = None
    library_id: Optional[UUID] = None
    include_deleted: bool = False
    skip: int = 0
    limit: int = 20
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class GetBookRequest:
    """获取 Book 的请求"""
    book_id: UUID
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class UpdateBookRequest:
    """更新 Book 的请求"""
    book_id: Optional[UUID] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    maturity: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None
    due_at: Optional[str] = None
    tag_ids: Optional[List[UUID]] = None
    cover_icon: Optional[str] = None
    cover_icon_provided: bool = False
    cover_media_id: Optional[UUID] = None
    cover_media_id_provided: bool = False
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class DeleteBookRequest:
    """删除 Book 的请求（RULE-012: Soft-delete to Basement）

    Args:
        book_id: Book ID to delete
        basement_bookshelf_id: Target bookshelf in Basement (typically derived from current bookshelf)
    """
    book_id: UUID
    basement_bookshelf_id: UUID
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class RestoreBookRequest:
    """恢复 Book 的请求（RULE-013: Restore from Basement）

    Args:
        book_id: Book ID to restore
        target_bookshelf_id: Target bookshelf to restore book to (must be in same library)
    """
    book_id: UUID
    target_bookshelf_id: UUID
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class ListDeletedBooksRequest:
    """列出已删除 Book 的请求"""
    bookshelf_id: Optional[UUID] = None
    library_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 20
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class MoveBookRequest:
    """转移 Book 的请求（RULE-011）"""
    book_id: UUID
    target_bookshelf_id: UUID
    reason: Optional[str] = None
    actor_user_id: Optional[UUID] = None
    enforce_owner_check: bool = True


@dataclass
class RecalculateBookMaturityRequest:
    """自动触发成熟度重算的请求"""

    book_id: UUID
    tag_count: Optional[int] = None
    block_type_count: Optional[int] = None
    block_count: Optional[int] = None
    open_todo_count: Optional[int] = None
    operations_bonus: Optional[int] = None
    cover_icon: Optional[str] = None
    trigger: str = "recalculate"
    actor_id: Optional[UUID] = None


@dataclass
class UpdateBookMaturityRequest:
    """手动调整 Book 成熟度的请求"""

    book_id: UUID
    target_maturity: str
    override_reason: Optional[str] = None
    force: bool = False
    trigger: str = "manual_override"
    actor_id: Optional[UUID] = None
    open_todo_count: Optional[int] = None
    maturity_score: Optional[int] = None
    tag_count: Optional[int] = None
    block_type_count: Optional[int] = None
    block_count: Optional[int] = None
    operations_bonus: Optional[int] = None
    cover_icon: Optional[str] = None
    visit_count_90d: Optional[int] = None
    last_content_edit_at: Optional[datetime] = None
    last_visited_at: Optional[datetime] = None
    is_pinned: Optional[bool] = None


# ============================================================================
# Output DTOs (Response Models) - Unified to Pydantic schemas
# ============================================================================

# 统一：使用 schemas.py 中的 Pydantic 模型，避免 dataclass 与 Pydantic 双轨造成的序列化分裂。
# ListBooks 用例采用 BookPaginatedResponse；单 Book 用例采用 BookDetailResponse。

from api.app.modules.book.schemas import (
    BookDetailResponse as BookResponse,
    BookPaginatedResponse as BookListPaginatedResponse,
    # Backward compatibility alias: legacy name BookListResponse still imported by other modules
    BookPaginatedResponse as BookListResponse,
)


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
    """列出 Book 的 UseCase 接口 (统一返回分页 Pydantic 模型)"""

    @abstractmethod
    async def execute(self, request: ListBooksRequest) -> BookListPaginatedResponse:
        """执行列出 Book (返回 BookPaginatedResponse)"""
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


class RecalculateBookMaturityUseCase(ABC):
    """自动重算成熟度的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: RecalculateBookMaturityRequest) -> BookMaturityMutationResult:
        """执行成熟度得分重算"""
        pass


class UpdateBookMaturityUseCase(ABC):
    """手动覆盖成熟度的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UpdateBookMaturityRequest) -> BookMaturityMutationResult:
        """执行成熟度覆盖或 Legacy 切换"""
        pass
