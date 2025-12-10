# ADR-008: Library Service & Repository 架构设计

**状态**: ACCEPTED
**日期**: 2025-11-12
**涉及模块**: Library Domain (Service Layer & Repository Layer)
**优先级**: P0 (Core Implementation)

---

## 问题陈述

在 DDD 架构中，Service 层和 Repository 层的职责边界容易混淆，导致：
- 业务规则逻辑泄露到 Repository 层
- 数据库操作混入 Service 层
- 事件发布时机不清晰
- 错误处理分层不明确

需要建立清晰的设计原则，确保 Library 模块的 Service 和 Repository 层职责分明。

---

## 架构决策

### 1️⃣ 职责分工

#### Service 层（业务编排） - 4 层架构

```
Layer 1: Validation     ← 业务规则检查（RULE-001: 一用户一库）
          ↓
Layer 2: Domain Logic   ← 调用 Domain Factory / Methods，发出事件
          ↓
Layer 3: Persistence    ← 调用 Repository，捕获异常转译
          ↓
Layer 4: Event Pub      ← 收集事件，异步发布到 EventBus
```

#### Repository 层（持久化抽象） - 单一关注点

```
1. 构造 ORM Model
2. 执行数据库操作
3. 捕获约束冲突 → 转译为 Domain Exception
4. 提供业务查询接口（get_by_user_id 支持 RULE-001）
```

**关键规则**：
- Service ❌ 不直接使用 SQLAlchemy / ORM
- Repository ❌ 不包含业务逻辑
- 异常 ✅ Repository 负责转译为 Domain Exception

---

### 2️⃣ 事件发布流程

```
Timeline:
  Domain.create()
      ↓ (产生 events)
  Repository.save()
      ↓ (持久化到 DB)
  EventBus.publish()
      ↓ (异步通知其他 Domain)
  Listeners 处理（邮件、日志、权限初始化等）
```

**关键原则**：
- ✅ 先持久化，后发布（listeners 可以查询数据）
- ✅ 事件发布异常不中断流程（Library 已创建，只记日志）
- ✅ 异步发布避免阻塞

---

### 3️⃣ 异常处理分层

| Layer | 捕获 | 转译 | 抛出 |
|-------|------|------|------|
| Domain | - | - | ValueError |
| Repository | IntegrityError | ✓ | LibraryAlreadyExistsError |
| Service | Repository Exception | ✓ | Domain Exception |
| API Router | Domain Exception | ✓ | HTTP 4xx/5xx |

---

### 4️⃣ 查询接口

Repository 应提供的核心查询方法：

```python
class LibraryRepository(ABC):
    async def get_by_id(library_id) → Library          # 主键查询
    async def get_by_user_id(user_id) → Library        # 业务键查询（RULE-001）
    async def exists(library_id) → bool                 # 快速检查
    async def save(library) → None                      # 创建/更新
    async def delete(library_id) → None                 # 删除
```

**get_by_user_id 特殊性**：
- 最多返回 1 条（RULE-001）
- 多条记录 = 数据腐败告警

---

### 5️⃣ 代码实现模式

**Service 方法模板**：

```python
async def create_library(user_id: UUID, name: str) -> Library:
    # L1: Validation
    existing = await repo.get_by_user_id(user_id)
    if existing:
        raise LibraryAlreadyExistsError(...)

    # L2: Domain Logic
    library = Library.create(user_id, name)

    # L3: Persistence
    await repo.save(library)  # IntegrityError → LibraryAlreadyExistsError

    # L4: Event Publishing
    if event_bus and library.events:
        for event in library.events:
            try:
                await event_bus.publish(event)
            except Exception as e:
                logger.error(...)  # 不中断

    return library
```

**Repository _to_domain 提取**：

```python
def _to_domain(self, model: LibraryModel) -> Library:
    """DRY 原则：统一 ORM → Domain 转换"""
    return Library(
        library_id=model.id,
        user_id=model.user_id,
        name=LibraryName(value=model.name),
        basement_bookshelf_id=getattr(model, 'basement_bookshelf_id', None),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
```

---

## 实现清单

✅ **已完成**：

| 项目 | 文件 | 内容 |
|------|------|------|
| Repository 异常处理 | `repository.py` | `save()` 捕获 IntegrityError 转译 |
| Repository DRY | `repository.py` | `_to_domain()` 提取转换逻辑 |
| Repository 验证 | `repository.py` | `get_by_user_id()` 检测 RULE-001 违反 |
| Repository 日志 | `repository.py` | 所有方法 + 异常情况的日志 |
| Service EventBus | `service.py` | 构造函数支持注入 |
| Service 事件发布 | `service.py` | 所有方法都发布相应事件 |
| Service 日志记录 | `service.py` | 关键操作的日志 + 4 层注释 |
| Service 错误处理 | `service.py` | 捕获 IntegrityError 转译处理 |

🔮 **后续优化**（超出本 ADR 范围）：

- [ ] UnitOfWork 模式（多 Repository 事务）
- [ ] EventBus 实现（RabbitMQ / Kafka）
- [ ] Dead Letter Queue（发布失败重试）
- [ ] Redis 缓存（get_by_user_id 优化）

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 事件发布失败 | 数据已持久化，只记日志。未来用 DLQ |
| RULE-001 违反 | 数据库 UNIQUE 约束 + Repository 检测 |
| 并发写冲突 | IntegrityError 捕获处理 |
| EventBus 为 None | 检查后跳过，不发布 |

---

## 对标业界最佳实践

✅ 符合 DDD 标准
✅ 符合 Clean Architecture（依赖向内）
✅ 符合 ISP（接口隔离原则）
✅ 符合 CQS（查询/命令分离准备）

---

## 相关 ADR

- ADR-001: Independent Aggregate Roots
- ADR-005: Bookshelf Domain Simplification
- ADR-006: Book Domain Refinement
- ADR-007: Block Domain Implementation
