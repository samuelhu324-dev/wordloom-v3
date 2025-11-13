"""
Library Input Ports - UseCase Interfaces

定义所有 Library UseCase 的接口契约，供 Router 调用。
"""

from abc import ABC, abstractmethod
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class GetUserLibraryRequest:
    """获取用户 Library 的请求"""
    user_id: UUID


@dataclass
class DeleteLibraryRequest:
    """删除 Library 的请求"""
    library_id: UUID


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class LibraryResponse:
    """Library 的响应 DTO"""
    id: UUID
    user_id: UUID
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, library) -> "LibraryResponse":
        """从域对象转换"""
        return cls(
            id=library.id,
            user_id=library.user_id,
            created_at=library.created_at.isoformat() if library.created_at else None,
            updated_at=library.updated_at.isoformat() if library.updated_at else None
        )


# ============================================================================
# UseCase Interfaces (Input Ports)
# ============================================================================

class GetUserLibraryUseCase(ABC):
    """获取用户 Library 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetUserLibraryRequest) -> LibraryResponse:
        """执行获取用户 Library"""
        pass


class DeleteLibraryUseCase(ABC):
    """删除 Library 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DeleteLibraryRequest) -> None:
        """执行删除 Library"""
        pass
