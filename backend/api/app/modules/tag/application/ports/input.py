"""
Tag Input Ports - UseCase Interfaces

定义所有 Tag UseCase 的接口契约，供 Router 调用。

UseCase 接口设计原则:
1. 一个接口对应一个 UseCase
2. 方法名为 execute()
3. 参数使用 DTO 类（Input Request）
4. 返回值使用 DTO 类（Output Response）
5. 异常通过 Exception 抛出
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from ...domain import Tag, EntityType


# ============================================================================
# Input DTOs (Request Models)
# ============================================================================

@dataclass
class CreateTagRequest:
    """创建顶级 Tag 的请求"""
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CreateSubtagRequest:
    """创建 Sub-tag 的请求"""
    parent_tag_id: UUID
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None


@dataclass
class UpdateTagRequest:
    """更新 Tag 的请求"""
    tag_id: UUID
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    parent_tag_id: Optional[UUID] = None
    parent_tag_provided: bool = False


@dataclass
class DeleteTagRequest:
    """删除 Tag 的请求"""
    tag_id: UUID


@dataclass
class RestoreTagRequest:
    """恢复 Tag 的请求"""
    tag_id: UUID


@dataclass
class AssociateTagRequest:
    """关联 Tag 到 Entity 的请求"""
    tag_id: UUID
    entity_type: EntityType
    entity_id: UUID


@dataclass
class DisassociateTagRequest:
    """移除 Tag 与 Entity 关联的请求"""
    tag_id: UUID
    entity_type: EntityType
    entity_id: UUID


@dataclass
class SearchTagsRequest:
    """搜索 Tag 的请求"""
    keyword: str
    limit: int = 20
    order: str = "name_asc"


@dataclass
class GetMostUsedTagsRequest:
    """获取最常用 Tag 的请求"""
    limit: int = 30


@dataclass
class ListTagsRequest:
    """分页列出 Tag 的请求"""
    page: int = 1
    size: int = 50
    include_deleted: bool = False
    only_top_level: bool = True
    order_by: str = "name_asc"


# ============================================================================
# Output DTOs (Response Models)
# ============================================================================

@dataclass
class TagResponse:
    """Tag 的响应 DTO"""
    id: UUID
    name: str
    color: str
    icon: Optional[str]
    description: Optional[str]
    level: int  # 0=top, 1=sub, 2=sub-sub
    parent_tag_id: Optional[UUID]
    usage_count: int
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]

    @classmethod
    def from_domain(cls, tag: Tag) -> "TagResponse":
        """从域对象转换"""
        return cls(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            icon=tag.icon,
            description=tag.description,
            level=tag.level,
            parent_tag_id=tag.parent_tag_id,
            usage_count=tag.usage_count,
            created_at=tag.created_at.isoformat() if tag.created_at else None,
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None,
            deleted_at=tag.deleted_at.isoformat() if tag.deleted_at else None
        )


@dataclass
class ListTagsResult:
    """分页列出 Tag 的响应"""
    items: List[TagResponse]
    total: int
    page: int
    size: int

    @property
    def has_more(self) -> bool:
        return self.page * self.size < self.total


# ============================================================================
# UseCase Interfaces (Input Ports)
# ============================================================================

class CreateTagUseCase(ABC):
    """创建顶级 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: CreateTagRequest) -> TagResponse:
        """执行创建 Tag"""
        pass


class CreateSubtagUseCase(ABC):
    """创建 Sub-tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: CreateSubtagRequest) -> TagResponse:
        """执行创建 Sub-tag"""
        pass


class UpdateTagUseCase(ABC):
    """更新 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: UpdateTagRequest) -> TagResponse:
        """执行更新 Tag"""
        pass


class DeleteTagUseCase(ABC):
    """删除 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DeleteTagRequest) -> None:
        """执行删除 Tag"""
        pass


class RestoreTagUseCase(ABC):
    """恢复 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: RestoreTagRequest) -> TagResponse:
        """执行恢复 Tag"""
        pass


class AssociateTagUseCase(ABC):
    """关联 Tag 到 Entity 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: AssociateTagRequest) -> None:
        """执行关联 Tag"""
        pass


class DisassociateTagUseCase(ABC):
    """移除 Tag 与 Entity 关联的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: DisassociateTagRequest) -> None:
        """执行移除关联"""
        pass


class SearchTagsUseCase(ABC):
    """搜索 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: SearchTagsRequest) -> List[TagResponse]:
        """执行搜索 Tag"""
        pass


class GetMostUsedTagsUseCase(ABC):
    """获取最常用 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: GetMostUsedTagsRequest) -> List[TagResponse]:
        """执行获取最常用 Tag"""
        pass


class ListTagsUseCase(ABC):
    """分页列出 Tag 的 UseCase 接口"""

    @abstractmethod
    async def execute(self, request: ListTagsRequest) -> ListTagsResult:
        """执行分页列出 Tag"""
        pass
