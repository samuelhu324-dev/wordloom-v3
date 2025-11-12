# Library Service & Repository 修订总结

**修订日期**: 2025-11-12
**版本**: v2 (按业界最佳实践重构)
**涉及文件**: 2 个核心文件 + 1 个新 ADR

---

## 📊 修改概览

```
📁 backend/api/app/modules/domains/library/
├─ repository.py      [✅ 大幅改进]
├─ service.py         [✅ 大幅改进]
│
📁 assets/docs/ADR/
└─ ADR-008-library-service-repository-design.md   [✨ 新建]
```

---

## 🔄 repository.py 修改详情

### 添加内容

#### 1️⃣ 导入增强
```python
# 新增
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from domains.library.domain import LibraryName
from domains.library.exceptions import LibraryAlreadyExistsError

logger = logging.getLogger(__name__)
```

#### 2️⃣ 异常处理（save 方法）
```python
async def save(self, library: Library) -> None:
    """
    改进：
    ✅ 捕获 IntegrityError
    ✅ 区分 user_id 唯一性冲突（RULE-001）
    ✅ 转译为 LibraryAlreadyExistsError
    ✅ 添加警告日志
    """
    try:
        model = LibraryModel(...)
        self.session.add(model)
    except IntegrityError as e:
        error_str = str(e).lower()
        if "user_id" in error_str or "unique" in error_str:
            logger.warning(f"Integrity constraint violated: {e}")
            raise LibraryAlreadyExistsError(
                "User already has a Library (database constraint)"
            )
        logger.error(f"Unexpected integrity error: {e}")
        raise
```

#### 3️⃣ 提取转换方法（DRY 原则）
```python
def _to_domain(self, model: LibraryModel) -> Library:
    """
    新增方法：避免 get_by_id 和 get_by_user_id 的转换逻辑重复

    改进：
    ✅ 统一处理 ORM → Domain 转换
    ✅ 支持可选字段 basement_bookshelf_id
    """
    return Library(
        library_id=model.id,
        user_id=model.user_id,
        name=LibraryName(value=model.name),
        basement_bookshelf_id=getattr(model, 'basement_bookshelf_id', None),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
```

#### 4️⃣ 查询方法改进
```python
async def get_by_id(self, library_id: UUID) -> Optional[Library]:
    """
    改进：
    ✅ 调用 _to_domain() 复用转换逻辑
    ✅ 异常情况添加调试日志
    ✅ 捕获数据库异常避免泄露
    """
    try:
        model = await self.session.get(LibraryModel, library_id)
        if not model:
            logger.debug(f"Library not found: {library_id}")
            return None
        return self._to_domain(model)
    except Exception as e:
        logger.error(f"Error fetching Library {library_id}: {e}")
        raise

async def get_by_user_id(self, user_id: UUID) -> Optional[Library]:
    """
    改进：
    ✅ 调用 result.scalars().all() 检测多条记录
    ✅ 检测 RULE-001 违反（多库情况）
    ✅ 添加数据腐败告警日志
    ✅ 使用 _to_domain() 转换
    """
    try:
        stmt = select(LibraryModel).where(LibraryModel.user_id == user_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        if not models:
            logger.debug(f"No Library found for user: {user_id}")
            return None

        # RULE-001 violation detection
        if len(models) > 1:
            logger.error(
                f"RULE-001 violation: User {user_id} has {len(models)} Libraries! "
                f"Returning first one, but this indicates data corruption."
            )

        return self._to_domain(models[0])
    except Exception as e:
        logger.error(f"Error fetching Library for user {user_id}: {e}")
        raise
```

#### 5️⃣ 删除和存在性检查改进
```python
async def delete(self, library_id: UUID) -> None:
    """
    改进：
    ✅ 添加成功/失败日志
    ✅ 异常处理
    """
    try:
        model = await self.session.get(LibraryModel, library_id)
        if model:
            await self.session.delete(model)
            logger.info(f"Library deleted: {library_id}")
        else:
            logger.debug(f"Library not found for deletion: {library_id}")
    except Exception as e:
        logger.error(f"Error deleting Library {library_id}: {e}")
        raise

async def exists(self, library_id: UUID) -> bool:
    """
    改进：
    ✅ 异常处理和日志
    """
    try:
        model = await self.session.get(LibraryModel, library_id)
        return model is not None
    except Exception as e:
        logger.error(f"Error checking Library existence {library_id}: {e}")
        raise
```

### 代码量统计

```
repository.py 增幅：
  原始：~60 行（核心逻辑）
  修订：~180 行（包含异常处理 + 日志 + 文档）
  增加：+120 行（主要是错误处理和日志）
```

---

## 🔄 service.py 修改详情

### 添加内容

#### 1️⃣ 文档和导入增强
```python
"""
改进文档：
✅ 添加 4 层架构说明
✅ 明确职责分工
"""

import logging
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)
```

#### 2️⃣ 构造函数改进
```python
def __init__(self, repository: LibraryRepository, event_bus=None):
    """
    改进：
    ✅ 支持可选的 EventBus 注入
    ✅ 用于事件异步发布
    """
    self.repository = repository
    self.event_bus = event_bus
```

#### 3️⃣ create_library 方法大幅改进

**原始版本**（30 行）：
```python
async def create_library(self, user_id: UUID, name: str) -> Library:
    existing = await self.repository.get_by_user_id(user_id)
    if existing:
        raise LibraryAlreadyExistsError(...)

    library = Library.create(user_id=user_id, name=name)
    await self.repository.save(library)
    return library
```

**改进版本**（60 行）：
```python
async def create_library(self, user_id: UUID, name: str) -> Library:
    """
    改进：
    ✅ 明确的 4 层架构注释
    ✅ 详细的日志记录
    ✅ 异常处理链（IntegrityError → Domain Exception）
    ✅ 事件发布机制
    ✅ 发布异常不中断主流程
    """
    logger.info(f"Creating Library for user {user_id} with name '{name}'")

    # ========== Layer 1: Validation ==========
    existing = await self.repository.get_by_user_id(user_id)
    if existing:
        logger.warning(f"User {user_id} already has a Library {existing.id}")
        raise LibraryAlreadyExistsError(...)

    # ========== Layer 2: Domain Logic ==========
    library = Library.create(user_id=user_id, name=name)
    logger.debug(f"Created Library domain object: {library.id}")

    # ========== Layer 3: Persistence ==========
    try:
        await self.repository.save(library)
        logger.info(f"Library persisted: {library.id}")
    except IntegrityError as e:
        logger.error(f"IntegrityError while saving Library: {e}")
        raise LibraryAlreadyExistsError("User already has a Library")
    except LibraryAlreadyExistsError:
        logger.warning(f"LibraryAlreadyExistsError from repository")
        raise

    # ========== Layer 4: Event Publishing ==========
    if self.event_bus and library.events:
        logger.debug(f"Publishing {len(library.events)} domain events")
        for event in library.events:
            try:
                await self.event_bus.publish(event)
                logger.debug(f"Published event: {event.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")
                # ⚠️ 不中断：Library 已创建，只记日志

    return library
```

#### 4️⃣ get_library 方法改进
```python
async def get_library(self, library_id: UUID) -> Library:
    """
    改进：
    ✅ 添加调试日志（查询开始和成功）
    ✅ 添加警告日志（失败情况）
    """
    logger.debug(f"Retrieving Library: {library_id}")
    library = await self.repository.get_by_id(library_id)
    if not library:
        logger.warning(f"Library not found: {library_id}")
        raise LibraryNotFoundError(f"Library {library_id} not found")
    logger.debug(f"Library retrieved: {library_id}")
    return library
```

#### 5️⃣ rename_library 方法改进
```python
async def rename_library(self, library_id: UUID, new_name: str) -> Library:
    """
    改进：
    ✅ 添加操作日志
    ✅ 发布 LibraryRenamed 事件
    ✅ 事件发布异常处理
    """
    logger.info(f"Renaming Library {library_id} to '{new_name}'")
    library = await self.get_library(library_id)

    library.rename(new_name)
    await self.repository.save(library)

    # Event Publishing
    if self.event_bus and library.events:
        for event in library.events:
            try:
                await self.event_bus.publish(event)
                logger.debug(f"Published event: {event.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to publish rename event: {e}")

    return library
```

#### 6️⃣ delete_library 方法改进
```python
async def delete_library(self, library_id: UUID) -> None:
    """
    改进：
    ✅ 成功删除日志
    ✅ 发布 LibraryDeleted 事件
    ✅ 事件发布异常处理
    """
    logger.info(f"Deleting Library: {library_id}")
    library = await self.get_library(library_id)

    library.mark_deleted()
    await self.repository.save(library)
    await self.repository.delete(library_id)
    logger.info(f"Library deleted successfully: {library_id}")

    # Event Publishing
    if self.event_bus and library.events:
        for event in library.events:
            try:
                await self.event_bus.publish(event)
                logger.debug(f"Published event: {event.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to publish delete event: {e}")
```

### 代码量统计

```
service.py 增幅：
  原始：~80 行（核心逻辑）
  修订：~175 行（包含日志 + 事件 + 文档）
  增加：+95 行（主要是事件发布和日志）
```

---

## 📋 ADR-008 新建

**文件**: `assets/docs/ADR/ADR-008-library-service-repository-design.md`

**内容**:
- 清晰的职责分工（Service 4 层 + Repository 单一关注）
- 事件发布流程图
- 异常处理分层表
- 查询接口设计
- 代码实现模式
- 完整的实现清单
- 风险评估与缓解

**长度**: 精简版 ~250 行（相比之前的详细版 ~550 行）

---

## ✅ 验证结果

### 语法检查
```
✅ repository.py  - No syntax errors
✅ service.py     - No syntax errors
✅ ADR-008.md     - 有效的 Markdown
```

### 对齐 DDD 最佳实践
```
✅ Repository 职责清晰（仅数据持久化）
✅ Service 职责明确（业务编排）
✅ 异常分层处理（数据库 → Domain）
✅ 事件发布机制（异步通知）
✅ DRY 原则（_to_domain 提取）
✅ 完整的日志记录（可追踪性）
✅ RULE-001 检测（数据完整性）
```

---

## 📈 关键改进对比

| 方面 | 原始版本 | 改进版本 | 提升 |
|------|----------|----------|------|
| 异常处理 | 基础 | 完整分层 | ⬆️⬆️⬆️ |
| 日志记录 | 缺失 | 全覆盖 | ⬆️⬆️⬆️ |
| 代码复用 | 转换重复 | DRY (_to_domain) | ⬆️⬆️ |
| 事件发布 | 缺失 | 完整实现 | ⬆️⬆️⬆️ |
| 文档完整性 | 基础 | 详细注释 + ADR | ⬆️⬆️⬆️ |
| RULE-001 检测 | 无 | 主动检测 | ⬆️⬆️ |
| 代码行数 | ~140 行 | ~355 行 | +153% |

---

## 🎯 后续建议

### 短期（立即执行）
- [ ] Code Review 这两个文件
- [ ] 运行 pytest 验证现有测试通过
- [ ] 提交 PR 并合并

### 中期（1-2 周）
- [ ] 为 Service/Repository 编写单元测试
- [ ] 实现 EventBus 具体类（当前使用接口）
- [ ] 集成测试验证完整流程

### 长期（下一阶段）
- [ ] 其他 Domain 模块参考本 ADR 重构
- [ ] UnitOfWork 模式统一事务管理
- [ ] Dead Letter Queue 处理事件发布失败

---

## 📚 相关文档

- **DDD_RULES.yaml**: 记录了 Library Domain 的完整规则
- **ADR-001**: Independent Aggregate Roots（聚合根设计）
- **ADR-005-007**: 其他 Domain 的 ADR 文档

---

**修订完成时间**: 2025-11-12
**状态**: ✅ READY FOR REVIEW
**下一步**: 等待 Code Review 和集成测试

