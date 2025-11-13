"""
Block Input Ports - UseCase Interfaces

定义所有 Block UseCase 的接口契约，供 Router 调用。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class CreateBlockRequest:
    """创建 Block 的请求"""
    book_id: UUID
    block_type: str  # TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    position_after_id: Optional[UUID] = None


@dataclass
class ListBlocksRequest:
    """列出 Block 的请求"""
    book_id: UUID
    skip: int = 0
    limit: int = 100


@dataclass
class GetBlockRequest:
    """获取 Block 的请求"""
    block_id: UUID


@dataclass
class UpdateBlockRequest:
    """更新 Block 的请求"""
    block_id: UUID
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReorderBlocksRequest:
    """重新排序 Block 的请求"""
    block_id: UUID
    position_after_id: Optional[UUID] = None
    position_before_id: Optional[UUID] = None


@dataclass
class DeleteBlockRequest:
    """删除 Block 的请求"""
    block_id: UUID


@dataclass
class RestoreBlockRequest:
    """恢复 Block 的请求"""
    block_id: UUID


@dataclass
class ListDeletedBlocksRequest:
    """列出已删除 Block 的请求"""
    skip: int = 0
    limit: int = 100


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class BlockResponse:
    """Block 的响应 DTO"""
    id: UUID
    book_id: UUID
    block_type: str
    content: Optional[str]
    metadata: Optional[Dict[str, Any]]
    order: str  # Fractional index
    created_at: str
    updated_at: str
    soft_deleted_at: Optional[str]

    @classmethod
    def from_domain(cls, block) -> "BlockResponse":
        """从域对象转换"""
        return cls(
            id=block.id,
            book_id=block.book_id,
            block_type=block.block_type.value if hasattr(block.block_type, 'value') else str(block.block_type),
            content=block.content,
            metadata=block.metadata,
            order=str(block.order),
            created_at=block.created_at.isoformat() if block.created_at else None,
            updated_at=block.updated_at.isoformat() if block.updated_at else None,
            soft_deleted_at=block.soft_deleted_at.isoformat() if block.soft_deleted_at else None
        )


@dataclass
class BlockListResponse:
    """Block 列表响应 DTO"""
    items: List[BlockResponse]
    total: int


# ============================================================================
# UseCase Interfaces (Input Ports)
# ============================================================================

class CreateBlockUseCase(ABC):
    """创建 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: CreateBlockRequest) -> BlockResponse:
        """执行创建 Block"""
        pass


class ListBlocksUseCase(ABC):
    """列出 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ListBlocksRequest) -> BlockListResponse:
        """执行列出 Block"""
        pass


class GetBlockUseCase(ABC):
    """获取 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetBlockRequest) -> BlockResponse:
        """执行获取 Block"""
        pass


class UpdateBlockUseCase(ABC):
    """更新 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UpdateBlockRequest) -> BlockResponse:
        """执行更新 Block"""
        pass


class ReorderBlocksUseCase(ABC):
    """重新排序 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ReorderBlocksRequest) -> BlockResponse:
        """执行重新排序 Block"""
        pass


class DeleteBlockUseCase(ABC):
    """删除 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DeleteBlockRequest) -> None:
        """执行删除 Block"""
        pass


class RestoreBlockUseCase(ABC):
    """恢复 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: RestoreBlockRequest) -> BlockResponse:
        """执行恢复 Block"""
        pass


class ListDeletedBlocksUseCase(ABC):
    """列出已删除 Block 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ListDeletedBlocksRequest) -> BlockListResponse:
        """执行列出已删除 Block"""
        pass
