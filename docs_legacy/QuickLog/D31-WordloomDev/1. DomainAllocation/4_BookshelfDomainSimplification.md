Domain 代码是否还有可转移/删减的内容？
📊 当前 domain.py 代码质量分析
现状：
├─ 代码行数: ~350 行 (接近警戒线 ⚠️)
├─ 权重: 45% (应该是 30-40%) ⚠️
├─ 事件数: 4 个 (✅ 合理，核心事件)
└─ 方法数: 10+ 个

分类分析：

✅ 必须保留在 Domain 的内容（110 行）
# 1. Enums（15 行）
class BookshelfType(str, Enum):
    NORMAL = "normal"
    BASEMENT = "basement"

class BookshelfStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

# 2. 核心 Events（80 行）
@dataclass
class BookshelfCreated(DomainEvent): ...
@dataclass
class BookshelfRenamed(DomainEvent): ...
@dataclass
class BookshelfStatusChanged(DomainEvent): ...
@dataclass
class BookshelfDeleted(DomainEvent): ...

# 3. Value Objects（40 行）
@dataclass(frozen=True)
class BookshelfName(ValueObject):
    def __post_init__(self):  # ← RULE-006 验证

@dataclass(frozen=True)
class BookshelfDescription(ValueObject): ...

✅ 应该保留的业务方法（80 行）
# 1. Factory Method（20 行）
@classmethod
def create(cls, library_id, name, description) -> Bookshelf:
    # ← RULE-004 体现

# 2. 名称管理（15 行）
def rename(self, new_name: str) -> None:
    # ← RULE-006 体现
    # ← BookshelfRenamed 事件

def set_description(self, description: Optional[str]) -> None:
    # 辅助方法（可保留）

# 3. 状态管理 - 核心业务（30 行）
def change_status(self, new_status: BookshelfStatus) -> None:
    # ← RULE-010 约束（Basement 不能删除）
    # ← BookshelfStatusChanged 事件

def mark_deleted(self) -> None:
    # ← BookshelfDeleted 事件

# 4. Basement 支持（10 行）
@property
def is_basement(self) -> bool: ...

def mark_as_basement(self) -> None: ...

# 5. 查询方法（15 行）
def can_accept_books(self) -> bool: ...
def is_active(self) -> bool: ...
def is_archived(self) -> bool: ...
def is_deleted(self) -> bool: ...

# 6. Dunder 方法（5 行）
def __repr__(self): ...
def __eq__(self, other): ...
def __hash__(self): ...

⚠️ 可以精简的内容（50 行）
# 1. set_description() - 可删除 (5 行)
def set_description(self, description: Optional[str]) -> None:
    self.description = BookshelfDescription(value=description)
    self.updated_at = datetime.utcnow()

# ❌ 为什么可删除？
#    - 没有对应的 DomainEvent
#    - 没有业务不变性检查
#    - 可在 Service 层直接操作 bookshelf.description
#    - 或者在 rename() 的同时支持

# 2. 过度的查询方法 (15 行)
def can_accept_books(self) -> bool: ...
def is_active(self) -> bool: ...
def is_archived(self) -> bool: ...
def is_deleted(self) -> bool: ...

# ❌ 为什么可精简？
#    - 这些是简单的 status 检查
#    - 可以在 Service 层或 Router 层做
#    - 如 if bookshelf.status == BookshelfStatus.ACTIVE

# 3. 冗余的初始化参数 (20 行)
def __init__(
    self,
    bookshelf_id: UUID,
    library_id: UUID,
    name: BookshelfName,
    description: BookshelfDescription = None,  # ← 可简化
    bookshelf_type: BookshelfType = BookshelfType.NORMAL,  # ← 可简化
    is_hidden: bool = False,  # ← 可简化
    is_pinned: bool = False,  # ← 已移到 Service
    pinned_at: Optional[datetime] = None,  # ← 已移到 Service
    is_favorite: bool = False,  # ← 已移到 Service
    status: BookshelfStatus = BookshelfStatus.ACTIVE,  # ← 可简化
    book_count: int = 0,  # ← 可删除（可从数据库查询）
    created_at: datetime = None,  # ← 可简化
    updated_at: datetime = None,  # ← 可简化
):

🎯 精简建议（从 350 行 → ~280 行）
# ============================================================================
# 精简版 Bookshelf Domain（~280 行）
# ============================================================================

# filepath: d:\Project\Wordloom\backend\api\app\modules\domains\bookshelf\domain.py

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from shared.base import AggregateRoot, DomainEvent, ValueObject


# ============================================================================
# Enums
# ============================================================================

class BookshelfType(str, Enum):
    NORMAL = "normal"
    BASEMENT = "basement"


class BookshelfStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================================================
# Domain Events (核心事件，保留)
# ============================================================================

@dataclass
class BookshelfCreated(DomainEvent):
    bookshelf_id: UUID
    library_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfRenamed(DomainEvent):
    bookshelf_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfStatusChanged(DomainEvent):
    """Emitted when Bookshelf status changes (active/archived/deleted)"""
    bookshelf_id: UUID
    old_status: BookshelfStatus
    new_status: BookshelfStatus
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


@dataclass
class BookshelfDeleted(DomainEvent):
    bookshelf_id: UUID
    library_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def aggregate_id(self) -> UUID:
        return self.bookshelf_id


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class BookshelfName(ValueObject):
    """Value object for Bookshelf name (RULE-006)"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Bookshelf name cannot be empty")
        if len(self.value) > 255:
            raise ValueError("Bookshelf name cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class BookshelfDescription(ValueObject):
    """Value object for Bookshelf description"""
    value: Optional[str] = None

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError("Bookshelf description cannot exceed 1000 characters")

    def __str__(self) -> str:
        return self.value or ""


# ============================================================================
# Aggregate Root
# ============================================================================

class Bookshelf(AggregateRoot):
    """
    Bookshelf Aggregate Root (独立聚合根)

    Invariants (from DDD_RULES):
    - RULE-004: 可无限创建
    - RULE-005: 必须属于一个 Library (via library_id FK)
    - RULE-006: 名称不能为空 (≤ 255 字符)
    - RULE-010: 每个 Library 有隐藏的 Basement

    Design Decision:
    - 独立聚合根：通过 FK 关联，不嵌套
    - 没有 Book 集合（Books 通过 bookshelf_id FK 关联）
    - 辅助功能 (pin/favorite) 已转移到 Service 层
    """

    def __init__(
        self,
        bookshelf_id: UUID,
        library_id: UUID,
        name: BookshelfName,
        description: BookshelfDescription = None,
        bookshelf_type: BookshelfType = BookshelfType.NORMAL,
        is_hidden: bool = False,
        status: BookshelfStatus = BookshelfStatus.ACTIVE,
        is_pinned: bool = False,  # ← 保留字段（Service 操作）
        pinned_at: Optional[datetime] = None,  # ← 保留字段（Service 操作）
        is_favorite: bool = False,  # ← 保留字段（Service 操作）
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = bookshelf_id
        self.library_id = library_id  # ← FK（RULE-005）
        self.name = name
        self.description = description or BookshelfDescription()
        self.type = bookshelf_type
        self.is_hidden = is_hidden
        self.status = status
        self.is_pinned = is_pinned  # ← Service 操作
        self.pinned_at = pinned_at  # ← Service 操作
        self.is_favorite = is_favorite  # ← Service 操作
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.events = []

    # ====================================================================
    # Factory Method
    # ====================================================================

    @classmethod
    def create(
        cls,
        library_id: UUID,
        name: str,
        description: Optional[str] = None,
    ) -> Bookshelf:
        """
        Factory method to create a new Bookshelf (RULE-004)

        Args:
            library_id: Parent Library ID (RULE-005)
            name: Bookshelf name (RULE-006: validated)
            description: Optional description

        Returns:
            New Bookshelf with BookshelfCreated event

        Raises:
            ValueError: If name or description invalid
        """
        bookshelf_id = uuid4()
        bookshelf_name = BookshelfName(value=name)  # ← RULE-006 验证
        bookshelf_desc = BookshelfDescription(value=description)
        now = datetime.utcnow()

        bookshelf = cls(
            bookshelf_id=bookshelf_id,
            library_id=library_id,  # ← RULE-005
            name=bookshelf_name,
            description=bookshelf_desc,
            status=BookshelfStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        bookshelf.emit(
            BookshelfCreated(
                bookshelf_id=bookshelf_id,
                library_id=library_id,
                name=name,
                occurred_at=now,
            )
        )

        return bookshelf

    # ====================================================================
    # Business Methods - Name Management
    # ====================================================================

    def rename(self, new_name: str) -> None:
        """Rename the Bookshelf (RULE-006: validated)"""
        new_bookshelf_name = BookshelfName(value=new_name)

        if self.name.value == new_bookshelf_name.value:
            return

        old_name = self.name.value
        self.name = new_bookshelf_name
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfRenamed(
                bookshelf_id=self.id,
                old_name=old_name,
                new_name=new_name,
                occurred_at=self.updated_at,
            )
        )

    # ====================================================================
    # Business Methods - Status Management (核心业务)
    # ====================================================================

    def change_status(self, new_status: BookshelfStatus) -> None:
        """
        Change Bookshelf status

        Constraint: Basement cannot be deleted (RULE-010)
        """
        if self.status == new_status:
            return

        # RULE-010: Basement 不能被删除
        if self.type == BookshelfType.BASEMENT and new_status == BookshelfStatus.DELETED:
            raise ValueError("Cannot delete Basement Bookshelf")

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self.emit(
            BookshelfStatusChanged(
                bookshelf_id=self.id,
                old_status=old_status,
                new_status=new_status,
                occurred_at=self.updated_at,
            )
        )

    def mark_deleted(self) -> None:
        """Mark Bookshelf as deleted"""
        self.change_status(BookshelfStatus.DELETED)

        self.emit(
            BookshelfDeleted(
                bookshelf_id=self.id,
                library_id=self.library_id,
                occurred_at=self.updated_at,
            )
        )

    # ====================================================================
    # Basement Support
    # ====================================================================

    @property
    def is_basement(self) -> bool:
        """Check if this is the Basement Bookshelf (RULE-010)"""
        return self.type == BookshelfType.BASEMENT

    def mark_as_basement(self) -> None:
        """Mark as Basement (系统调用，在创建时使用)"""
        if self.type != BookshelfType.NORMAL:
            raise ValueError("Cannot convert non-normal shelf to basement")
        self.type = BookshelfType.BASEMENT
        self.is_hidden = True
        self.updated_at = datetime.utcnow()

    # ====================================================================
    # Utility Methods
    # ====================================================================

    def __repr__(self) -> str:
        return f"<Bookshelf(id={self.id}, name={self.name.value}, status={self.status})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bookshelf):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

📊 精简对比
现状 domain.py:
├─ Enums: 15 行
├─ Events: 80 行
├─ Value Objects: 40 行
├─ __init__: 25 行
├─ create(): 25 行
├─ rename(): 15 行
├─ set_description(): 5 行 ← 删除
├─ change_status(): 20 行
├─ mark_deleted(): 10 行
├─ Basement 方法: 15 行
├─ 查询方法: 25 行 ← 精简
├─ __repr__/__eq__/__hash__: 10 行
└─ 总计: ~350 行

精简后 domain.py:
├─ Enums: 15 行
├─ Events: 80 行
├─ Value Objects: 40 行
├─ __init__: 18 行 ← 精简
├─ create(): 25 行
├─ rename(): 15 行
├─ change_status(): 20 行
├─ mark_deleted(): 10 行
├─ Basement 方法: 15 行
├─ __repr__/__eq__/__hash__: 10 行
└─ 总计: ~280 行 (-20%)

删除的部分 (70 行):
❌ set_description() (5 行)
❌ can_accept_books(), is_active(), is_archived(), is_deleted() (15 行)
❌ 简化 __init__ 参数 (10 行)
❌ 移除文档注释中的冗余解释 (40 行)

