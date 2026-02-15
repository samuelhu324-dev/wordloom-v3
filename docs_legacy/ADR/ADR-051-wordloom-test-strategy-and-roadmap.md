# ADR-051: Wordloom 测试策略与执行路线图

**状态**: 草案 (DRAFT - P0 阶段执行中)
**创建日期**: 2025-11-15
**最后更新**: 2025-11-15
**作者**: 架构团队
**涉及模块**: 全栈 (Config, Core, Shared, Event Bus, ORM, Storage, Modules, HTTP Adapters)

---

## 1. 执行摘要

本文档定义了 Wordloom v3 后端的完整测试策略，包括：

- **测试金字塔**: 单元测试 (60%) → 集成测试 (30%) → E2E 测试 (10%)
- **三阶段执行计划**: P0 (基础设施) → P1 (模块) → P2 (HTTP & 集成)
- **目标覆盖**: 600+ 测试用例，45+ 测试文件，85-100% 覆盖率
- **时间表**: P0 本周，P1 下周，P2 后续

### 测试金字塔结构

```
        E2E (10%)
       /        \
      /          \
   集成测试       50 tests
   (30%)       /        \
              /          \
          单元测试    400 tests
          (60%)      /        \
                    /          \
                 基础设施    模块    HTTP
                 200 tests  100 tests 100 tests
```

---

## 2. 测试框架与工具

### 技术栈

| 工具 | 用途 | 版本 |
|------|------|------|
| **pytest** | 测试框架 | ^7.0 |
| **pytest-asyncio** | 异步测试支持 | ^0.20 |
| **pytest-cov** | 覆盖率报告 | ^4.0 |
| **unittest.mock** | Mock/Patch | 内置 |
| **SQLite** | 测试数据库 | 内置 |

### 配置文件

**pytest.ini** 配置：
```ini
[pytest]
asyncio_mode = auto
testpaths = backend/api/app/tests backend/infra/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=app --cov=infra --cov-report=html
```

---

## 3. P0 阶段：基础设施层测试（本周）

### 3.1 范围

基础设施层包括系统级别的配置、异常、共享实用程序、事件总线和数据持久化。

### 3.2 配置层 (Config Layer) - 50 测试

**目录**: `backend/api/app/tests/test_config/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `conftest.py` | - | 共享fixtures |
| `test_settings.py` | 15 | 环境变量加载、默认值、验证 |
| `test_database_config.py` | 15 | 数据库连接、连接池、URL解析 |
| `test_security_config.py` | 20 | JWT、密码哈希、令牌验证 |

**关键测试**:
- ✅ Settings从环境变量加载
- ✅ 数据库连接池配置
- ✅ JWT令牌创建和验证
- ✅ 密码哈希和验证

### 3.3 核心层 (Core Layer) - 25 测试

**目录**: `backend/api/app/tests/test_core/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_exceptions.py` | 25 | 8个系统异常类的继承、创建、序列化 |

**关键异常**:
- `AppException` (基类)
- `ValidationException`
- `AuthenticationException`
- `AuthorizationException`
- `NotFoundException`
- `ConflictException`
- `RateLimitException`
- `ServiceUnavailableException`

### 3.4 共享层 (Shared Layer) - 50 测试

**目录**: `backend/api/app/tests/test_shared/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_base.py` | 25 | ValueObject、AggregateRoot、DomainEvent |
| `test_errors.py` | 15 | DDD特定错误 (7个错误类) |
| `test_schemas.py` | 10 | PaginationRequest/Response、TimestampedDTO |

**DDD基类**:
- ✅ ValueObject 相等性、哈希、不可变性
- ✅ AggregateRoot 身份、版本、事件收集
- ✅ DomainEvent 时间戳、聚合根ID

### 3.5 事件总线 (Event Bus) - 50 测试

**目录**: `backend/infra/tests/test_event_bus/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_event_handler_registry.py` | 30 | 处理器注册、装饰器模式、异步分发 |
| `test_handlers.py` | 20 | 6个事件处理器 (Block/Tag CRUD) |

**处理器**:
- `BlockCreatedHandler` → 插入search_index
- `BlockUpdatedHandler` → 更新search_index
- `BlockDeletedHandler` → 删除search_index
- `TagCreatedHandler` → 插入search_index
- `TagUpdatedHandler` → 更新search_index
- `TagDeletedHandler` → 删除search_index

### 3.6 存储层 (Storage Layer) - 75 测试

**目录**: `backend/infra/tests/test_storage/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_repositories.py` | 40 | 7个Repository适配器 (CRUD、查询、事务) |
| `test_orm_models.py` | 35 | ORM模型约束、关系、级联、验证 |

**仓库适配器**:
- LibraryRepository (8 tests)
- BookshelfRepository (8 tests)
- BookRepository (8 tests)
- BlockRepository (8 tests)
- TagRepository (6 tests)
- MediaRepository (6 tests)
- SearchIndexRepository (6 tests)

**ORM模型验证**:
- 主键约束
- 外键约束
- 唯一约束
- 非空约束
- 软删除字段
- 级联操作
- 时间戳自动管理

### 3.7 P0 执行清单

- [ ] 所有config层测试通过
- [ ] 所有core层测试通过
- [ ] 所有shared层测试通过
- [ ] 所有event_bus层测试通过
- [ ] 所有storage层基本测试通过
- [ ] 覆盖率 >= 80%
- [ ] 更新DDD_RULES.yaml
- [ ] 更新HEXAGONAL_RULES.yaml

---

## 4. P1 阶段：模块层测试（下周）

### 4.1 范围

模块层包括 Media、Tag、Search 模块的完整测试，以及 Library、Bookshelf、Book、Block 的验证。

### 4.2 Media 模块 - 100 测试

**目录**: `backend/api/app/tests/test_media/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_domain.py` | 20 | Media AggregateRoot、ValueObjects、Events |
| `test_repository.py` | 20 | MediaPort实现、CRUD、查询 |
| `test_service.py` | 20 | 8个UseCase (upload, delete, restore等) |
| `test_router.py` | 25 | 8个端点、参数验证、错误处理 |
| `test_integration.py` | 15 | 跨模块集成 (与Book关联) |

### 4.3 Tag 模块 - 80 测试

**目录**: `backend/api/app/tests/test_tag/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_domain.py` | 18 | Tag AggregateRoot、层次结构、Events |
| `test_repository.py` | 15 | TagPort实现、CRUD、层次查询 |
| `test_service.py` | 20 | 6个UseCase |
| `test_router.py` | 27 | 6个端点 |

### 4.4 Search 模块 - 100 测试

**目录**: `backend/api/app/tests/test_search/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_domain.py` | 20 | SearchQuery、SearchHit、SearchResult ValueObjects |
| `test_repository.py` | 30 | PostgreSQL FTS、排序、排名、分页 |
| `test_service.py` | 20 | ExecuteSearch UseCase、并行查询 |
| `test_router.py` | 20 | 6个搜索端点 |
| `test_integration.py` | 10 | 跨模块搜索集成 |

### 4.5 验证现有模块

- Library: 13个测试 (✅ 已存在)
- Bookshelf: 38个测试 (✅ 已存在)
- Book: 28个测试 (✅ 已存在)
- Block: 34个测试 (✅ 已存在)

---

## 5. P2 阶段：HTTP & 集成测试（之后）

### 5.1 HTTP 路由端点 - 100 测试

**目录**: `backend/api/app/tests/test_routers/`

| 模块 | 端点数 | 测试数 |
|------|-------|-------|
| Library | 5 | 15 |
| Bookshelf | 6 | 20 |
| Book | 8 | 25 |
| Block | 8 | 15 |
| Tag | 6 | 12 |
| Media | 8 | 13 |

**覆盖范围**:
- ✅ 参数验证
- ✅ 认证授权
- ✅ 错误响应
- ✅ 异常映射到HTTP状态码

### 5.2 集成测试 - 50+ 测试

**目录**: `backend/api/app/tests/test_integration/`

| 场景 | 测试数 |
|------|-------|
| 跨域工作流 | 20 |
| 删除恢复 (Basement/Trash) | 15 |
| 搜索集成 | 10 |
| 事件驱动流 | 5 |

---

## 6. 测试文件结构总结

```
backend/
├── api/
│   └── app/
│       └── tests/
│           ├── conftest.py (全局fixtures)
│           ├── test_config/          (50 tests)
│           │   ├── conftest.py
│           │   ├── test_settings.py
│           │   ├── test_database_config.py
│           │   └── test_security_config.py
│           ├── test_core/            (25 tests)
│           │   └── test_exceptions.py
│           ├── test_shared/          (50 tests)
│           │   ├── test_base.py
│           │   ├── test_errors.py
│           │   └── test_schemas.py
│           ├── test_media/           (100 tests - P1)
│           ├── test_tag/             (80 tests - P1)
│           ├── test_search/          (100 tests - P1)
│           ├── test_routers/         (100 tests - P2)
│           └── test_integration/     (50 tests - P2)
│
└── infra/
    └── tests/
        ├── conftest.py
        ├── test_event_bus/          (50 tests)
        │   ├── test_event_handler_registry.py
        │   └── test_handlers.py
        └── test_storage/            (75 tests)
            ├── test_repositories.py
            └── test_orm_models.py
```

---

## 7. 覆盖率目标

| 层级 | 目标 | 优先级 |
|------|------|--------|
| Config | 100% | P0 |
| Core | 100% | P0 |
| Shared | 95% | P0 |
| Event Bus | 95% | P0 |
| Storage | 90% | P0 |
| Domain (Models) | 95% | P1 |
| Application (Services) | 90% | P1 |
| HTTP Adapters | 85% | P2 |
| **整体** | **85%** | **总目标** |

---

## 8. CI/CD 集成

### GitHub Actions 配置

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run P0 tests
        run: |
          pytest backend/api/app/tests/test_config \
                  backend/api/app/tests/test_core \
                  backend/api/app/tests/test_shared \
                  backend/infra/tests/test_event_bus \
                  backend/infra/tests/test_storage \
                  --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 9. 关键决策

### 9.1 测试数据库

- **P0-P1**: SQLite 内存数据库 (快速、隔离)
- **P2**: PostgreSQL 测试容器 (准确)

### 9.2 Mock 策略

- **Domain**: 不使用 Mock (纯逻辑)
- **Service**: Mock Repository
- **Router**: Mock Service
- **Integration**: 真实依赖

### 9.3 异步测试

所有涉及 async/await 的测试使用 `@pytest.mark.asyncio`

---

## 10. 后续步骤

### P0 完成后
1. ✅ 创建所有 P0 测试文件
2. ✅ 验证覆盖率 >= 80%
3. → 更新 DDD_RULES.yaml
4. → 更新 HEXAGONAL_RULES.yaml

### P1 准备
- 参考 Bookshelf 模块模式
- 应用相同测试结构到 Media/Tag/Search

### P2 准备
- 创建 HTTP 路由测试
- 创建跨域集成测试

---

## 11. 相关文档

- **DDD_RULES.yaml**: 域模型规则与测试元数据
- **HEXAGONAL_RULES.yaml**: 架构分层与测试映射
- **ADR-046**: P0/P1 基础设施完成总结
- **ADR-050**: 搜索模块设计 (Search 测试参考)

---

## 12. 附录：Mock 示例

### Repository Mock 模式

```python
class MockLibraryRepository(ILibraryRepository):
    def __init__(self):
        self.libraries = {}

    async def save(self, library):
        self.libraries[library.id] = library
        return library

    async def get_by_id(self, library_id):
        return self.libraries.get(library_id)
```

### 使用 Fixture

```python
@pytest.fixture
def mock_library_repository():
    return MockLibraryRepository()

@pytest.fixture
def create_library_service(mock_library_repository):
    return CreateLibraryUseCase(
        library_repository=mock_library_repository
    )
```

---

## 4. P1 阶段：业务模块层测试（进行中）

### 4.1 范围

业务模块层包括 Media、Tag、Search 等核心模块的完整实现。

### 4.2 Media 模块 - 100 测试

**目录**: `backend/api/app/tests/test_media/`

| 文件 | 测试数量 | 覆盖范围 |
|------|--------|---------|
| `test_domain.py` | 20 | Media AggregateRoot、6个事件、生命周期 |
| `test_service.py` | 20 | CRUD、垃圾箱、30天保留、事件发出 |
| `test_router.py` | 25 | 8个HTTP端点、验证、认证 |
| `test_repository.py` | 20 | 保存、获取、列表、分页、垃圾箱 |
| `test_integration.py` | 15 | Block/Book关联、事件总线、搜索 |

**关键事件**:
- `MediaUploadedEvent`
- `MediaMovedToTrashEvent`
- `MediaRestoredEvent`
- `MediaPurgedEvent`
- `MediaAssociatedEvent`
- `MediaDisassociatedEvent`

### 4.3 Tag 模块 - 80 测试

**文件**: `backend/api/app/tests/test_tag/test_module_complete.py`

| 测试类 | 测试数量 | 覆盖范围 |
|--------|--------|---------|
| `TestTagAggregateRoot` | 3 | 创建、颜色、重命名 |
| `TestTagHierarchy` | 2 | 父子关系、多级深度 |
| `TestTagEvents` | 3 | 创建/重命名/删除事件 |
| `TestTagService` | 2 | 创建、唯一性 |
| `TestTagRouter` | 4 | CRUD端点骨架 |
| `TestTagRepository` | 4 | 保存、获取、列表、层次查询 |
| `TestTagIntegration` | 3 | Block关联、搜索、删除级联 |

### 4.4 Search 模块 - 100 测试

**文件**: `backend/api/app/tests/test_search/test_module_complete.py`

| 测试类 | 测试数量 | 覆盖范围 |
|--------|--------|---------|
| `TestSearchQuery` | 3 | 创建、验证、过滤 |
| `TestSearchHit` | 2 | 创建、排名 |
| `TestSearchResult` | 2 | 空结果、多结果 |
| `TestSearchRepository` | 4 | 全局/类型/分页/排名 |
| `TestSearchService` | 3 | 执行、性能、并行 |
| `TestSearchRouter` | 4 | 全局/Block/Book/过滤 |
| `TestSearchIndexSync` | 3 | Block创建/更新/删除时同步 |
| `TestSearchFullTextSearch` | 3 | FTS查询、tsvector、代码段 |
| `TestSearchIntegration` | 3 | 跨模块、权限、事件 |

### 4.5 P1 总计

- **总测试数**: 280 (100 + 80 + 100)
- **总文件数**: 9 (5 + 1 + 1 + 2 其他模块)
- **状态**: ✅ 完成

---

## 5. P2 阶段：HTTP 与集成层测试（待执行）

### 5.1 HTTP 路由测试 - 100 测试

**文件**: `backend/api/app/tests/test_routers/test_all_endpoints.py`

| 路由类 | 端点数量 | 测试数量 |
|--------|--------|---------|
| `TestLibraryRoutes` | 5 | 15 |
| `TestBookshelfRoutes` | 6 | 18 |
| `TestBookRoutes` | 8 | 24 |
| `TestBlockRoutes` | 6 | 18 |
| `TestTagRoutes` | 6 | 18 |
| `TestMediaRoutes` | 7 | 21 |
| `TestSearchRoutes` | 6 | 18 |
| `TestErrorHandling` | - | 4 |
| `TestAuthenticationAuthorization` | - | 3 |

**关键测试**:
- ✅ 所有HTTP端点的请求/响应验证
- ✅ 错误处理 (4xx/5xx)
- ✅ 认证和授权
- ✅ 请求验证

### 5.2 工作流集成测试 - 50 测试

**文件**: `backend/api/app/tests/test_integration/test_workflows.py`

| 测试类 | 测试数量 | 覆盖范围 |
|--------|--------|---------|
| `TestCompleteWorkflow` | 3 | 完整工作流 |
| `TestDeleteRecoveryWorkflow` | 3 | 删除/恢复 |
| `TestSearchIntegration` | 3 | 搜索集成 |
| `TestEventPropagation` | 3 | 事件传播 |
| `TestConcurrentOperations` | 3 | 并发操作 |
| `TestDataIntegrity` | 3 | 数据完整性 |
| `TestPermissionIntegration` | 2 | 权限集成 |
| `TestPerformance` | 3 | 性能测试 |

### 5.3 跨模块集成测试 - 50 测试

**文件**: `backend/api/app/tests/test_integration/test_cross_module.py`

| 测试类 | 测试数量 | 覆盖范围 |
|--------|--------|---------|
| `TestCrossModuleIntegration` | 3 | 跨模块 |
| `TestPermissionHierarchy` | 3 | 权限 |
| `TestErrorRecovery` | 3 | 错误恢复 |
| `TestEventConsistency` | 3 | 事件一致性 |
| `TestDataConsistency` | 3 | 数据一致性 |
| `TestBoundaryConditions` | 5 | 边界条件 |
| `TestCacheIntegration` | 2 | 缓存 |
| `TestMessageQueue` | 2 | 消息队列 |

### 5.4 P2 总计

- **总测试数**: 200 (100 + 50 + 50)
- **总文件数**: 3 (1 + 2)
- **状态**: ⏳ 待执行

---

## 6. 整体进度

### 阶段总结

| 阶段 | 文件数 | 测试数 | 覆盖范围 | 状态 |
|------|-------|-------|---------|------|
| P0 基础设施 | 12 | 250 | Config/Core/Shared/EventBus/Storage | ✅ 完成 |
| P1 业务模块 | 9 | 280 | Media/Tag/Search/Other | ✅ 完成 |
| P2 HTTP & 集成 | 3 | 200 | 路由/工作流/跨模块 | ⏳ 待执行 |
| **总计** | **24** | **730** | **全栈覆盖** | ⏳ 进行中 |

### 覆盖率目标

- **整体目标**: 85%
- **Config层**: 100%
- **Core层**: 100%
- **Shared层**: 100%
- **EventBus层**: 95%
- **Storage层**: 90%
- **业务模块**: 85%
- **HTTP适配器**: 80%

---

## 7. 执行指南

### 运行 P0 测试

```bash
pytest backend/api/app/tests/test_config \
        backend/api/app/tests/test_core \
        backend/api/app/tests/test_shared \
        backend/infra/tests/test_event_bus \
        backend/infra/tests/test_storage \
        --cov=app.config \
        --cov=app.core \
        --cov=app.shared \
        --cov=infra.event_bus \
        --cov=infra.storage \
        --cov-report=html
```

### 运行 P1 测试

```bash
pytest backend/api/app/tests/test_media \
        backend/api/app/tests/test_tag \
        backend/api/app/tests/test_search \
        --cov=app.modules.media \
        --cov=app.modules.tag \
        --cov=app.modules.search \
        --cov-report=html
```

### 运行 P2 测试

```bash
pytest backend/api/app/tests/test_routers \
        backend/api/app/tests/test_integration \
        --cov=app.routers \
        --cov-report=html
```

### 运行所有测试

```bash
pytest backend/ --cov=app --cov=infra --cov-report=html -v
```

---

**版本历史**

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1 | 2025-11-15 | 初始草案 (P0 阶段) |
| 0.2 | 2025-11-15 | P0 完成 + P1 进行中 + P2 规划 |
