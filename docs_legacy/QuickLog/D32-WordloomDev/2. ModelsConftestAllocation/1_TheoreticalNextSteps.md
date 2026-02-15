
🏆 Phase 1: 补全 Core 4 Domains（你已做）

```python
✅ DONE:
├─ Library (D/S/R)
├─ Bookshelf (D/S/R)
├─ Book (D/S/R)
└─ Block (D/S/R)

❌ PENDING - 补完必要的支持文件:
├─ exceptions.py       ← 所有 Domain 异常
├─ models.py           ← ORM 验证
├─ __init__.py         ← 导出聚合根
└─ conftest.py         ← 测试 fixtures
```

🔧 Phase 2a: 处理"简单"模块（VO/ValueObject）

```python
优先级 P1（建议立即做）:

【Tag 模块】（如果是 Book-scoped VO）
├─ Decision: "全局标签" or "Book-scoped 标签"？
│  建议: 全局标签（更灵活，支持跨书共享）
├─ Domain: Tag 作为独立聚合根
│  ├─ Tag.create(name: str, description: str = None)
│  └─ Tag.invariants: name 唯一性、非空
├─ Service: TagService.create_tag(), list_tags(), delete_tag()
├─ Repository: TagRepository.get_by_name(), get_by_library_id()
└─ Work: ~2-3 天（D/S/R + tests）

【Media 模块】（作为 VO，简单做法）
├─ Decision: Value Object 还是 Aggregate？
│  建议: 初期作为 VO（嵌入 Block），后期升级为 Aggregate
├─ Domain: MediaReference VO
│  ├─ file_url: str
│  ├─ file_size: int
│  ├─ mime_type: str
│  └─ uploaded_at: datetime
├─ Service: 暂无（由 BlockService 处理）
├─ Repository: 暂无
└─ Work: ~1 天（作为 VO 嵌入）
```

🔌 Phase 2b: 处理"复杂"模块（需要基础设施）

```python
优先级 P2（后续做）:

【Search 模块】
├─ Role: Infrastructure-driven（搜索引擎）
├─ Not a Domain Model（是 Infrastructure 的一部分）
├─ No D/S/R needed（只有 Adapter）
└─ Work: 对接 Elasticsearch/Meilisearch

【Stats 模块】
├─ Role: Reporting/Analytics（独立 Context）
├─ May have D/S/R（或只是 Query Repository）
├─ CQRS 模式推荐
└─ Work: 异步更新 Stats 表

【Chronicle 模块】（时间追踪）
├─ Role: Event Sourcing + Audit Log
├─ May need D/S/R（或使用 Event Store）
├─ 依赖于 Domain Events
└─ Work: 消费所有 Domain Events

【Theme 模块】
├─ Role: UI Configuration（用户偏好）
├─ Simple D/S/R（ThemeService.apply_theme()）
├─ Low priority
└─ Work: ~1 天
```

完整的改造路线图（成熟方案）

```python
┌─────────────────────────────────────────────────────────────────┐
│          Wordloom DDD 架构完整改造路线图                          │
├─────────────────────────────────────────────────────────────────┤

【Week 1】✅ DONE
├─ Library (D/S/R) ✅
├─ Bookshelf (D/S/R) ✅
├─ Book (D/S/R) ✅
└─ Block (D/S/R) ✅

【Week 2】🔧 Core Infrastructure
├─ Task 1: 补全 exceptions.py（所有 Domain）
│  └─ 时间: 4 小时
│  └─ 产出: 统一异常层次结构
│
├─ Task 2: 完善 models.py（ORM 验证）
│  └─ 时间: 6 小时
│  └─ 产出: ORM ↔ Domain 映射确认
│
└─ Task 3: 完善 conftest.py（测试 fixtures）
   └─ 时间: 4 小时
   └─ 产出: 单元/集成测试框架

【Week 3-4】📦 Tag + Media (简单模块)
├─ Tag 模块改造（选项 A：全局标签）
│  ├─ domain.py: Tag 聚合根
│  ├─ service.py: TagService
│  ├─ repository.py: TagRepository
│  ├─ models.py: Tag ORM + BookTag 关联
│  ├─ schemas.py: TagResponse DTO
│  ├─ router.py: CRUD endpoints
│  └─ 时间: 3-4 天
│  └─ ADR: ADR-012-tag-domain-design.md
│
└─ Media 模块改造（选项 A：初期作为 VO）
   ├─ domain.py: MediaReference VO（嵌入 Block）
   ├─ 修改 Block: 添加 media_url, media_size 字段
   ├─ models.py: Block model 添加 media 字段
   ├─ service.py: BlockService 处理 media 上传
   ├─ router.py: Upload endpoint
   └─ 时间: 2-3 天
   └─ Note: 后期可升级为独立 Aggregate

【Week 5-6】🔌 Interface Layer (API)
├─ Task 1: Router 完善
│  └─ CRUD endpoints for all Aggregates
│  └─ 时间: 4-5 天
│
└─ Task 2: Schemas 完善
   └─ Request/Response DTO
   └─ 时间: 2-3 天
   └─ ADR: ADR-013-api-schema-design.md

【Week 7-8】📊 Analytics & Infrastructure
├─ Search 模块（Elasticsearch）
│  └─ 时间: 4-5 天
│
├─ Stats 模块（CQRS）
│  └─ 时间: 3-4 天
│
└─ Chronicle 模块（Event Sourcing）
   └─ 时间: 5-7 天

【Week 9+】🎯 Polish & Optimization
├─ Unit Tests (~80% 覆盖)
├─ Integration Tests
├─ Performance Tuning
├─ Documentation
└─ Code Review & Refactoring

总耗时: ~8-10 周
```
针对 Tag 和 Media 的具体建议

🏷️ Tag 模块方案对比

```python
┌─ 方案 A：全局标签（推荐）✅
│  ├─ 设计: Tag 是独立的 Aggregate Root
│  ├─ Book_Tag: Join Table（无业务逻辑）
│  ├─ 优点:
│  │  ✅ 标签可跨 Library/Bookshelf 共享
│  │  ✅ 标签有独立的生命周期
│  │  ✅ 支持标签管理（重命名、删除、合并）
│  │  ✅ 性能好（标签表小）
│  └─ 缺点: 需要处理孤立标签
│
├─ 方案 B：Book-scoped 标签
│  ├─ 设计: Tag 是 Book 内的 Value Object
│  ├─ 嵌入: Book.tags: List[Tag]
│  ├─ 优点:
│  │  ✅ 简单（无关联表）
│  │  ✅ ACID 保证（嵌入式）
│  │  ✅ 级联删除自动
│  └─ 缺点:
│     ❌ 无跨书共享
│     ❌ 无独立标签管理
│     ❌ Book 表膨胀
│
└─ 方案 C：混合（标签系统）
   ├─ 设计: User 可创建私有或公开标签
   ├─ Tag.scope: "PRIVATE" | "PUBLIC" | "SHARED"
   └─ 复杂度高，后期考虑
```

📸 Media 模块方案对比

```python
┌─ 方案 A：Media 作为 Value Object（推荐初期）✅
│  ├─ 设计: MediaReference VO 嵌入 Block
│  ├─ 字段: url, size, mime_type, uploaded_at
│  ├─ 优点:
│  │  ✅ 简单（无额外表）
│  │  ✅ 与 Block 生命周期一致
│  │  ✅ Block 删除时自动清理
│  └─ 缺点:
│     ❌ 无版本追踪
│     ❌ 无元数据管理
│     ❌ 后期升级复杂
│
├─ 方案 B：Media 作为独立 Aggregate（推荐长期）✅
│  ├─ 设计: Media 是独立的 Aggregate Root
│  ├─ 关系: Block.media_ids -> List[Media]
│  ├─ 优点:
│  │  ✅ 独立生命周期管理
│  │  ✅ 支持元数据、版本、权限
│  │  ✅ Block 可引用相同 Media
│  │  ✅ 灵活的删除策略
│  └─ 缺点: 复杂度高，需要额外 Service
│
└─ 方案 C：Media 作为 Infrastructure Service
   ├─ 设计: 不在 Domain 中，只有 Infrastructure Adapter
   └─ 适用: 简单的"上传 → 保存 → 返回 URL"流程
```

我的建议：分阶段

```python
【Phase 1】方案 A（现在）
├─ MediaReference VO（嵌入 Block）
├─ 简单的上传逻辑
└─ 工作量: 2-3 天

【Phase 2】方案 B（后期升级）
├─ Media Aggregate Root
├─ 元数据管理、版本追踪
├─ 数据迁移脚本
└─ 工作量: 5-7 天（升级成本）
```

DDD_RULES 与其他层的映射策略
```python
# 在 DDD_RULES 中新增部分，建立跨层映射

mapping_rules:
  domain_to_application:
    # 规则：如何从 Domain 映射到 Application DTO

    BookAggregate → BookResponse:
      mapping:
        - Book.id → id
        - Book.title.value → title
        - Book.summary.value → summary
        - Book.bookshelf_id → bookshelf_id
        - Book.library_id → library_id
        - Book.status.value → status
        - Book.is_pinned → is_pinned
        - Book.block_count → block_count
      validation_rules:
        - title 长度 3-255（来自 Domain BookTitle VO）
        - status 必须是 BookStatus 枚举值
        - bookshelf_id 必须存在（由 Service L1 验证）

    BookCreateRequest → Book.create():
      mapping:
        - title → BookTitle(value=title)
        - summary → BookSummary(value=summary) if summary else None
        - bookshelf_id → (passed to Domain)
      flow:
        - API 接收 BookCreateRequest
        - Service.create_book() 验证
        - Book.create() 构建 Domain
        - Repository.save() 持久化
        - Response 转换为 BookResponse

  domain_to_infrastructure:
    # 规则：如何从 Domain 映射到 ORM

    Book → BookModel:
      mapping:
        - Book.id → BookModel.id
        - Book.title.value → BookModel.title
        - Book.status.value → BookModel.status
      index_strategy:
        - 索引 bookshelf_id（频繁查询）
        - 索引 library_id（权限检查）
        - 复合索引 (bookshelf_id, soft_deleted_at)
      soft_delete_strategy:
        - BookModel.soft_deleted_at 标记删除
        - 查询默认过滤 soft_deleted_at IS NULL

exception_mapping:
  # Domain Exception → HTTP Response

  BookNotFoundError:
    status_code: 404
    message: "Book not found"

  PermissionError:
    status_code: 403
    message: "You don't have permission to access this Book"

  BookAlreadyExistsError:
    status_code: 409
    message: "Book with this title already exists"
```
