📋 最终建议（Action Items）

🎯 短期（立即执行）
优先级	项目	文件	修改
🔴 P0	添加 Event Publishing	service.py	在 create_library() 后添加事件发布
🔴 P0	改进错误处理	repository.py	捕获 IntegrityError，转译为 Domain Exception
🟡 P1	提取转换逻辑	repository.py	创建 _to_domain() 方法（DRY 原则）
🟡 P1	添加日志	service.py	关键操作处添加日志（调试和审计）
🟡 P1	单元测试	tests/	编写 Domain 层测试（覆盖 RULE-001 等）

🎯 中期（1-2 周）
优先级	项目	文件	说明
🟢 P2	UnitOfWork 模式	core/	实现跨 Repository 的事务管理
🟢 P2	集成测试	tests/	Service + Repository + DB 的端到端测试
🟢 P2	API Router	routers/	连接 HTTP → Service → Domain
🟢 P2	事件总线	infra/	异步事件发布和处理

🎯 长期（架构完善）
优先级	项目	说明
⚪ P3	CQS Repository	将查询和命令分离（性能优化）
⚪ P3	缓存层	Redis 缓存常用查询（一个用户一个Library）
⚪ P3	分页支持	Repository 添加 list_by_user_id(user_id, page, limit)


“查/存/删是 repo 的本真功能吗？”
是。Repository 的职责就是数据访问：

查询（get/list/search）
保存/新增/删除（save/add/delete）
参与 UoW 事务协调

业务规则（权限、状态流转、不变式）放 Service/Domain，不要塞进 Repo。

Service 不写 SQL/不拿 Session；只编排业务与规则校验。
Repository 写 SQL/ORM；返回 Domain 实体；不做业务判断；不随意 commit。
UoW 控制事务；一次业务 = 一次提交。
API 只收发 DTO；异常经 Service 翻译成领域异常再映射 HTTP。
谨防懒加载 & N+1：API 层不要直接拿 ORM；需要的数据在 Repo 一次性查好。

 行业成熟实践指导

🏆 Best Practice 1: Service 中的"先检查，后执行"模式
```python
class LibraryService:
    """
    业界标准：Service = 业务编排器

    模式：
    1. 检查前置条件（业务规则验证）
    2. 调用 Domain 方法执行核心逻辑
    3. 调用 Repository 持久化
    4. 发布事件通知其他模块
    """

    async def create_library(self, user_id: UUID, name: str) -> Library:
        """
        标准的 Service 方法模板

        ┌─────────────────────────────────────┐
        │  Layer 1: Validation (业务检查)      │
        │  - Check pre-conditions              │
        │  - Verify business rules            │
        └─────────────────────────────────────┘
                        ↓
        ┌─────────────────────────────────────┐
        │  Layer 2: Domain Logic (核心逻辑)    │
        │  - Call Domain factory/method       │
        │  - Domain emits events              │
        └─────────────────────────────────────┘
                        ↓
        ┌─────────────────────────────────────┐
        │  Layer 3: Persistence (持久化)       │
        │  - Call Repository.save()           │
        │  - Handle constraints violations    │
        └─────────────────────────────────────┘
                        ↓
        ┌─────────────────────────────────────┐
        │  Layer 4: Event Publishing (事件发布) │
        │  - Publish collected events         │
        │  - Async listeners process them     │
        └─────────────────────────────────────┘
        """

        # ========== Layer 1: Validation ==========
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not name or not name.strip():
            raise ValueError("name cannot be empty")

        # 业务规则：一个用户只能有一个 Library（RULE-001）
        existing = await self.repository.get_by_user_id(user_id)
        if existing:
            raise LibraryAlreadyExistsError(
                f"User {user_id} already has a Library"
            )

        # ========== Layer 2: Domain Logic ==========
        library = Library.create(user_id=user_id, name=name)
        # 此时 library.events 包含：
        # - LibraryCreated
        # - BasementCreated

        # ========== Layer 3: Persistence ==========
        try:
            await self.repository.save(library)
            # 如果有 UnitOfWork，应在这里或后续 commit
        except IntegrityError as e:
            # Repository 可能抛出约束冲突，Service 需要处理
            if "user_id" in str(e).lower():
                raise LibraryAlreadyExistsError("User already has a Library")
            raise

        # ========== Layer 4: Event Publishing ==========
        if self.event_bus:
            for event in library.events:
                await self.event_bus.publish(event)
                # 例如：LibraryCreated 事件可能触发：
                # - 发送欢迎邮件
                # - 初始化用户偏好设置
                # - 记录审计日志

        return library
```

🏆 Best Practice 2: Repository 中的"接口隔离"原则
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

# ❌ 坏的做法：所有方法都在一个接口
class BadLibraryRepository(ABC):
    @abstractmethod
    async def save(self): pass

    @abstractmethod
    async def update(self): pass

    @abstractmethod
    async def delete(self): pass

    # ← 逐渐膨胀，最后变成 God Object


# ✅ 好的做法：遵循 ISP（接口隔离原则）
class LibraryRepository(ABC):
    """Repository should have focused responsibilities"""

    @abstractmethod
    async def save(self, library: Library) -> None:
        """Persist or update a Library"""
        pass

    @abstractmethod
    async def get_by_id(self, library_id: UUID) -> Optional[Library]:
        """Retrieve by primary key"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
        """Retrieve by business key（业务键查询）"""
        pass

    @abstractmethod
    async def delete(self, library_id: UUID) -> None:
        """Mark as deleted or physically delete"""
        pass

    @abstractmethod
    async def exists(self, library_id: UUID) -> bool:
        """Fast existence check (often optimized with COUNT)"""
        pass


# 🎯 业界做法：更激进的分离（CQS - Command Query Segregation）
class LibraryCommandRepository(ABC):
    """Command Repository: 只负责写操作"""

    @abstractmethod
    async def save(self, library: Library) -> None: pass

    @abstractmethod
    async def delete(self, library_id: UUID) -> None: pass


class LibraryQueryRepository(ABC):
    """Query Repository: 只负责读操作（可以优化成 View/Redis）"""

    @abstractmethod
    async def get_by_id(self, library_id: UUID) -> Optional[Library]: pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[Library]: pass

    @abstractmethod
    async def exists(self, library_id: UUID) -> bool: pass
```

🏆 Best Practice 3: 事务管理的"UnitOfWork"模式
```python
# 业界标准：事务应该在 Service 层或更上层管理

# ❌ 错误做法：在 Repository 里 commit
class BadLibraryRepository:
    async def save(self, library: Library) -> None:
        model = LibraryModel(...)
        self.session.add(model)
        await self.session.commit()  # ← ❌ 不对！Repository 不应该 commit


# ✅ 正确做法 1：UnitOfWork 模式（推荐）
class UnitOfWork:
    """
    UnitOfWork 是事务的协调者

    优点：
    - 一个操作可能涉及多个 Repository
    - 要么全部成功，要么全部失败
    - 集中管理事务生命周期
    """

    def __init__(self, session):
        self.session = session
        self.library_repository = LibraryRepositoryImpl(session)
        self.bookshelf_repository = BookshelfRepositoryImpl(session)

    async def __aenter__(self):
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()


# 在 Service 中使用
class LibraryService:
    def __init__(self, unit_of_work_factory):
        self.uow_factory = unit_of_work_factory

    async def create_library(self, user_id: UUID, name: str) -> Library:
        library = Library.create(user_id, name)

        # ✅ 事务包装
        async with self.uow_factory() as uow:
            await uow.library_repository.save(library)
            # 如果抛异常，自动 rollback
            # 如果成功，自动 commit

        # commit 后再发布事件（确保数据已持久化）
        if self.event_bus:
            for event in library.events:
                await self.event_bus.publish(event)

        return library


# ✅ 正确做法 2：装饰器模式（简化版）
from functools import wraps

def transactional(session):
    """装饰器：自动处理事务"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
        return wrapper
    return decorator

class LibraryService:
    @transactional(session)
    async def create_library(self, user_id: UUID, name: str) -> Library:
        library = Library.create(user_id, name)
        await self.repository.save(library)
        return library
```

🏆 Best Practice 4: 错误分层处理
```python
# ===== 层级 1: Domain Exceptions (纯业务逻辑错误) =====
# exceptions.py

class LibraryException(Exception):
    """Base exception for Library domain"""
    pass

class LibraryAlreadyExistsError(LibraryException):
    """Business rule violation: One Library per user"""
    pass

class LibraryNotFoundError(LibraryException):
    """Aggregate root not found"""
    pass


# ===== 层级 2: Service Layer (业务流程错误) =====
# service.py

class LibraryService:
    async def create_library(self, user_id: UUID, name: str) -> Library:
        # 业务规则检查 → 抛出 Domain Exception
        existing = await self.repository.get_by_user_id(user_id)
        if existing:
            raise LibraryAlreadyExistsError("RULE-001 violated")

        try:
            library = Library.create(user_id, name)
            await self.repository.save(library)
        except IntegrityError as e:
            # Repository 层的错误 → Service 转译为 Domain Exception
            raise LibraryAlreadyExistsError("Database constraint violation")


# ===== 层级 3: API Router (HTTP 响应) =====
# router.py

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/libraries")
async def create_library(user_id: UUID, name: str, service: LibraryService):
    try:
        library = await service.create_library(user_id, name)
        return {"id": library.id, "name": library.name.value}

    except LibraryAlreadyExistsError as e:
        # Domain Exception → HTTP 400
        raise HTTPException(
            status_code=400,
            detail="User already has a Library"
        )

    except LibraryNotFoundError as e:
        # Domain Exception → HTTP 404
        raise HTTPException(
            status_code=404,
            detail="Library not found"
        )

    except Exception as e:
        # 意外异常 → HTTP 500
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

🏆 Best Practice 5: 测试分层
```python
# ===== 单元测试：Domain 层 =====
# tests/test_domain.py

import pytest
from domains.library.domain import Library, LibraryName

def test_library_creation():
    """Domain: Library.create() should emit LibraryCreated event"""
    library = Library.create(user_id=uuid4(), name="My Library")

    assert len(library.events) == 2  # LibraryCreated + BasementCreated
    assert library.name.value == "My Library"
    assert isinstance(library.events[0], LibraryCreated)


def test_library_name_validation():
    """Domain: LibraryName should reject empty strings"""
    with pytest.raises(ValueError):
        LibraryName(value="")

    with pytest.raises(ValueError):
        LibraryName(value="   ")  # 只有空格


# ===== 集成测试：Service + Repository =====
# tests/test_service.py

@pytest.mark.asyncio
async def test_create_library_service(session):
    """Service: create_library() should enforce RULE-001"""
    service = LibraryService(
        repository=LibraryRepositoryImpl(session)
    )

    user_id = uuid4()

    # 第一次创建应该成功
    lib1 = await service.create_library(user_id, "Library 1")
    assert lib1.id is not None

    # 第二次创建应该失败（RULE-001）
    with pytest.raises(LibraryAlreadyExistsError):
        await service.create_library(user_id, "Library 2")


@pytest.mark.asyncio
async def test_create_library_repository_constraint(session):
    """Repository: Should detect and handle integrity constraint"""
    repo = LibraryRepositoryImpl(session)

    user_id = uuid4()
    lib1 = Library.create(user_id, "Library 1")
    await repo.save(lib1)

    # 数据库级约束应该阻止插入重复的 user_id
    lib2 = Library.create(user_id, "Library 2")  # ← 不同的 library_id，相同的 user_id

    with pytest.raises(IntegrityError):
        await repo.save(lib2)
```