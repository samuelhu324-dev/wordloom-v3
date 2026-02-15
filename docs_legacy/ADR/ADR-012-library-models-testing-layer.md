# ADR-012: Library Models & Testing Layer 架构设计

**状态**: ACCEPTED
**日期**: 2025-11-12
**涉及模块**: Library Domain (Infrastructure Layer & Testing Layer)
**优先级**: P1 (Round-Trip Testing & Verification)
**关联 ADR**: ADR-008 (Service & Repository), ADR-001 (Independent Aggregates)

---

## 问题陈述

在 DDD 架构的 Library 模块中，infrastructure 和 testing 层的职责和测试验证容易含混：

- ORM Model 与 Domain Model 的映射验证不清晰
- 测试数据工厂（fixtures）与 Mock Repository 的分工不明确
- Round-trip 验证（Domain → DB → Domain）缺少统一的测试模式
- 数据库集成测试的依赖管理复杂
- 软删除、约束冲突、RULE-001 违反等边界情况缺少验证

需要建立清晰的 ORM 映射规范和全面的测试策略，确保 models.py 和 conftest.py 的职责明确。

---

## 架构决策

### 1️⃣ ORM 映射策略（Infrastructure Layer）

#### LibraryModel 数据库表设计

```
CREATE TABLE libraries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,          -- ← RULE-001: 一用户一库
  name VARCHAR(255) NOT NULL,             -- ← RULE-003: 名称约束
  created_at TIMESTAMP WITH TIME ZONE,    -- ← 时区感知
  updated_at TIMESTAMP WITH TIME ZONE,    -- ← 软更新时间戳
  UNIQUE(user_id)                         -- ← 强制 1:1 关系
);
CREATE INDEX idx_user_id ON libraries(user_id);
```

#### 字段映射对照表

| ORM 字段 | SQL 类型 | Domain 字段 | Domain 类型 | 验证规则 |
|---------|---------|-----------|-----------|--------|
| `id` | UUID | `library_id` | UUID | PK, 非空 |
| `user_id` | UUID | `user_id` | UUID | FK, 唯一, 非空 |
| `name` | VARCHAR(255) | `name` | LibraryName VO | 长度 1-255 |
| `created_at` | DateTime+TZ | `created_at` | DateTime | UTC+0 |
| `updated_at` | DateTime+TZ | `updated_at` | DateTime | UTC+0 |

#### Round-Trip 验证清单

```python
✅ UUID 恒等性: LibraryModel.id == Library.library_id
✅ 用户关联: LibraryModel.user_id == Library.user_id (RULE-001 基础)
✅ 名称对齐: LibraryModel.name == LibraryName(Library.name).value
✅ 时间戳精度: abs(t_model - t_domain) < 1 秒
✅ 时区正确性: created_at.tzinfo == UTC
✅ 数据完整性: 字段无丢失、无截断
```

### 2️⃣ 测试分层策略（Testing Layer）

```
Testing Pyramid:

                    ▲
                   ╱ ╲
                  ╱   ╲ E2E 端到端
                 ╱─────╲
                ╱       ╲
               ╱ 集成测试  ╲  (使用 db_session, real DB)
              ╱───────────╲
             ╱             ╲
            ╱ 单元测试       ╲ (使用 mock_repository, 内存)
           ╱───────────────╲
          ╱                 ╲
         ╱─────────────────── ╲

Unit Tests (70%) → Integration (25%) → E2E (5%)
```

#### Fixtures 分类与职责

```python
# 1️⃣ 常量 Fixtures（不变）
@pytest.fixture
def sample_user_id():
    """固定的用户 ID 用于测试"""
    return uuid4()

# 2️⃣ 工厂 Fixtures（快速创建测试对象）
@pytest.fixture
def library_domain_factory(sample_user_id):
    """
    生成 Domain 对象

    Usage:
        library = library_domain_factory(name="Custom")
    """
    def _create(name="Test", ...):
        return Library(...)
    return _create

@pytest.fixture
def library_model_factory(sample_user_id):
    """
    生成 ORM 对象

    Usage:
        model = library_model_factory(name="Custom")
    """
    def _create(name="Test", ...):
        return LibraryModel(...)
    return _create

# 3️⃣ Mock Fixtures（单元测试）
@pytest.fixture
async def mock_library_repository(library_domain_factory):
    """
    内存 Repository（不涉及数据库）

    Usage:
        async def test_create(library_service, mock_repository):
            await library_service.create_library(...)
    """
    class MockLibraryRepository:
        def __init__(self):
            self.store = {}
        async def save(self, library): ...
        async def get_by_id(self, id): ...
    return MockLibraryRepository()

# 4️⃣ 数据库 Fixtures（集成测试）
@pytest.fixture
async def db_engine():
    """
    创建测试用异步数据库引擎

    用于集成测试，每个测试独立
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """
    创建测试用异步数据库会话

    关键特性：
    - 每个测试独立会话
    - 测试后自动回滚（可选）
    - 支持并行执行
    """
    async_session = async_sessionmaker(db_engine, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest.fixture
async def library_repository_impl(db_session):
    """
    真实 LibraryRepositoryImpl（使用真实 DB）

    用于集成测试 round-trip
    """
    return LibraryRepositoryImpl(session=db_session)

@pytest.fixture
async def library_service_with_db(library_repository_impl):
    """
    LibraryService with real database

    用于端到端测试
    """
    return LibraryService(repository=library_repository_impl)
```

#### Round-Trip Assertion Helpers

```python
# 验证 Domain → DB → Domain 的往返正确性
async def assert_library_round_trip(library_domain, repository):
    """
    Step 1: 保存到数据库
    Step 2: 从数据库加载
    Step 3: 逐字段验证
    Step 4: 返回加载后的对象供进一步测试
    """
    await repository.save(library_domain)
    loaded = await repository.get_by_id(library_domain.id)

    assert loaded is not None
    assert loaded.id == library_domain.id
    assert loaded.user_id == library_domain.user_id
    assert str(loaded.name) == str(library_domain.name)
    # 时间戳允许 1 秒误差（数据库精度）
    assert abs(loaded.created_at.timestamp() -
               library_domain.created_at.timestamp()) < 1

    return loaded

# 验证 RULE-001：一用户一库
async def assert_user_library_unique(user_id, repository):
    """
    检测数据腐败：同一用户多个 Library
    """
    library = await repository.get_by_user_id(user_id)
    assert library is None or library.user_id == user_id

# 验证存在性和删除
async def assert_library_persisted(library_id, repository):
    loaded = await repository.get_by_id(library_id)
    assert loaded is not None
    return loaded

async def assert_library_deleted(library_id, repository):
    loaded = await repository.get_by_id(library_id)
    assert loaded is None
```

### 3️⃣ 测试模式与用例

#### 模式 1: 单元测试（Mock Repository）

```python
@pytest.mark.asyncio
async def test_create_library_unit(library_service, sample_user_id):
    """
    单元测试：Service 层逻辑验证

    特点：
    - 使用 Mock Repository（内存）
    - 不涉及数据库
    - 快速反馈
    """
    library = await library_service.create_library(sample_user_id, "My Library")

    assert library.id is not None
    assert library.user_id == sample_user_id
    assert str(library.name) == "My Library"
```

#### 模式 2: 集成测试（Real DB）

```python
@pytest.mark.asyncio
async def test_create_library_integration(
    library_repository_impl,
    sample_user_id
):
    """
    集成测试：Domain → DB → Domain 往返

    特点：
    - 使用真实 Repository + DB
    - 验证 ORM 映射正确性
    - 验证约束是否生效
    """
    library = Library.create(sample_user_id, "My Library")
    await library_repository_impl.save(library)

    # Round-trip 验证
    loaded = await assert_library_round_trip(library, library_repository_impl)
    assert loaded.id == library.id
```

#### 模式 3: Round-Trip 验证

```python
@pytest.mark.asyncio
async def test_library_round_trip(
    library_domain_factory,
    library_repository_impl
):
    """
    验证 ORM 映射的完整性

    确保：
    - 所有字段正确持久化
    - UUID 恒等性保持
    - 时间戳精度无损
    """
    library = library_domain_factory(name="Round Trip Test")

    # 保存 + 加载 + 验证
    loaded = await assert_library_round_trip(library, library_repository_impl)
    assert loaded.name.value == "Round Trip Test"
```

#### 模式 4: RULE-001 约束验证

```python
@pytest.mark.asyncio
async def test_rule_001_unique_per_user(
    library_service,
    library_repository_impl,
    sample_user_id
):
    """
    验证 RULE-001: 一用户一库

    确保：
    - 第一次创建成功
    - 第二次创建失败（IntegrityError → LibraryAlreadyExistsError）
    """
    # 第一次创建
    lib1 = await library_service.create_library(sample_user_id, "Library 1")
    assert lib1.user_id == sample_user_id

    # 第二次创建应该失败
    with pytest.raises(LibraryAlreadyExistsError):
        await library_service.create_library(sample_user_id, "Library 2")

    # 验证只有一个 Library
    await assert_user_library_unique(sample_user_id, library_repository_impl)
```

### 4️⃣ ORM 映射方法（to_dict / from_dict）

```python
class LibraryModel(Base):
    # ... 字段定义 ...

    def to_dict(self) -> dict:
        """
        序列化到字典

        用途：
        - 测试序列化
        - REST API 响应
        - 数据导出
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "LibraryModel":
        """
        从字典反序列化

        用途：
        - 测试数据导入
        - 数据迁移
        - API 请求处理
        """
        return LibraryModel(
            id=data.get("id"),
            user_id=data.get("user_id"),
            name=data.get("name"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
```

---

## 实现清单

✅ **已完成**：

| 项目 | 文件 | 内容 |
|------|------|------|
| LibraryModel 定义 | `models.py` | 完整 ORM 映射 + UNIQUE 约束 |
| Round-Trip 方法 | `models.py` | `to_dict()`, `from_dict()` |
| 常量 Fixtures | `conftest.py` | `sample_user_id`, `sample_library_id`, `sample_library_name` |
| 工厂 Fixtures | `conftest.py` | `library_domain_factory`, `library_model_factory`, `library_create_schema` |
| Mock Fixtures | `conftest.py` | `mock_library_repository`, `library_service` |
| 数据库 Fixtures | `conftest.py` | `db_engine`, `db_session` |
| Repository Fixtures | `conftest.py` | `library_repository_impl`, `library_service_with_db` |
| Round-Trip Helpers | `conftest.py` | `assert_library_round_trip()` |
| 约束验证 Helpers | `conftest.py` | `assert_user_library_unique()`, `assert_library_persisted()`, `assert_library_deleted()` |
| 事件验证 Helpers | `conftest.py` | `assert_library_created_event()`, `assert_library_renamed_event()` |

🔮 **后续优化**（超出本 ADR 范围）：

- [ ] PostgreSQL 特定优化（JSON 字段、JSONB）
- [ ] 并发测试（多用户同时创建 Library）
- [ ] 性能测试（批量操作基准）
- [ ] 缓存层测试（Redis 集成）
- [ ] 事件溯源测试（Event Store）

---

## 关键设计决策

### 1️⃣ 异步测试框架

**决策**：全异步 conftest（async fixtures + asyncio）

**原因**：
- ✅ 与 FastAPI async 一致
- ✅ 支持并行测试
- ✅ 真实环境模拟

**权衡**：
- ⚠️ 学习曲线陡（async/await）
- ✅ 早期学习，后期收益大

### 2️⃣ SQLite 内存 vs PostgreSQL

**决策**：开发用 SQLite 内存，CI/CD 用 PostgreSQL

**原因**：
- ✅ 本地开发快（<100ms）
- ✅ CI/CD 真实环境验证
- ✅ 降低本地资源消耗

**配置**：
```python
# 开发环境
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# CI/CD 环境
DATABASE_URL = os.getenv("TEST_DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost/wordloom_test")
```

### 3️⃣ Mock vs Real Repository

**决策**：单元测试用 Mock，集成测试用 Real

**使用场景**：
- ✅ Mock: Service 层逻辑测试（快）
- ✅ Real: Round-Trip 映射验证（准确）

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 时间戳精度丢失 | 允许 1 秒误差、使用 UTC 时区 |
| RULE-001 违反 | DB UNIQUE 约束 + 应用层检查 |
| Async 复杂性 | 详细文档 + fixtures 模板 |
| 测试隔离问题 | 每个测试独立 DB session + cleanup |
| 并发冲突 | IntegrityError 捕获 + 转译处理 |

---

## 对标业界最佳实践

✅ Hexagonal Architecture（端口-适配器）
✅ Repository Pattern（持久化抽象）
✅ Factory Pattern（测试数据生成）
✅ Test Pyramid（单元 → 集成 → E2E）
✅ DDD（不变量、值对象、聚合根）
✅ Clean Code（关注点分离、命名清晰）

---

## 相关 ADR

- **ADR-001**: Independent Aggregate Roots（聚合根独立性）
- **ADR-008**: Library Service & Repository Design（服务层和仓储层）
- **ADR-002**: Basement Pattern（软删除）
- **ADR-005**: Bookshelf Domain Simplification（相邻域参考）

---

## 后续工作

### 本 ADR 完成后

1. ✅ 编写 tests/test_library_models.py（ORM 映射测试）
2. ✅ 编写 tests/test_library_round_trip.py（往返验证）
3. ✅ 编写 tests/test_library_constraints.py（RULE-001 等约束）
4. 📊 测试覆盖率目标：>= 90%

### 相邻域参考

应用相同模式到 Bookshelf, Book, Block：
- ADR-009-bookshelf-models-testing-layer.md
- ADR-010-book-models-testing-layer.md
- ADR-011-block-models-testing-layer.md

---

## 版本历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2025-11-12 | Architecture Team | 初版发布 |

---

**批准者**: TBD
**有效期**: 长期（直到代码证明需要调整）
