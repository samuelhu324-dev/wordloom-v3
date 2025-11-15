"""
Search Application Input Ports - UseCase Interfaces

Defines the contract for search use cases.
Request/Response DTOs are imported from schemas.py (application layer DTOs).
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.search.application.schemas import ExecuteSearchRequest, ExecuteSearchResponse


class ExecuteSearchUseCase(ABC):
    """Execute Search UseCase - Port (Input Adapter)

    Orchestrates search across all entities.
    Application layer: depends on SearchPort (output port).

    DTO 注解通过 TYPE_CHECKING 引入，避免循环导入�?    运行时从 schemas 模块导入�?    """

    @abstractmethod
    async def execute(self, request: "ExecuteSearchRequest") -> "ExecuteSearchResponse":
        """Execute search operation

        Args:
            request: Search parameters (keyword, type, filters, pagination)
            - text: 搜索关键�?            - type: 实体类型过滤 (None = 全局搜索)
            - book_id: 书籍范围限制
            - limit: 分页大小
            - offset: 分页偏移

        Returns:
            ExecuteSearchResponse with hits and total count

        Raises:
            InvalidQueryError: Invalid search parameters
            SearchIndexError: Search engine failure
        """
        pass


__all__ = [
    "ExecuteSearchUseCase",
]
