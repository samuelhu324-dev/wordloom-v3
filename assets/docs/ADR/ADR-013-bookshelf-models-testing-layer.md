# ADR-013: Bookshelf Models & Testing Layer 架构设计

**状态**: ACCEPTED
**日期**: 2025-11-12
**涉及模块**: Bookshelf Domain (Infrastructure Layer & Testing Layer)
**优先级**: P1 (Models Constraints & Round-Trip Testing)
**关联 ADR**: ADR-009 (Service & Repository), ADR-012 (Library Models Pattern), ADR-001 (Independent Aggregates)

---

## 问题陈述

Bookshelf 模块在 infrastructure 和 testing 层存在关键缺陷：

### 核心问题

1. **RULE-006 约束缺失**: 缺少 `UNIQUE(library_id, name)` 约束
   - 数据库允许同一 Library 下重复名称
   - 应用层检查与 DB 约束不一致（belt-and-suspenders 原则破裂）

2. **RULE-010 支持不完整**: 缺少 `is_basement` 字段
   - 无法标记 Basement bookshelf
   - get_basement_by_library_id() 查询无法实现

3. **ORM 映射方法缺失**: 无 `to_dict()` / `from_dict()`
   - Round-trip 验证无法进行
   - API 响应序列化不规范

4. **测试层不成熟**: conftest.py 缺少关键能力
   - 无 ORM factory（bookshelf_model_factory）
   - Mock Repository 不验证 RULE-006 约束
   - 缺少 Basement 查询支持

5. **约束验证边界情况**: 缺少集成测试覆盖
   - IntegrityError 处理未验证
   - 重名冲突场景无测试
   - Basement 隐藏性未验证

### 架构影响

这些缺陷导致：
- 🔴 数据完整性风险（重复名称可能产生）
- 🔴 功能实现风险（Basement 模式无法支撑）
- 🟡 测试覆盖不足（往返验证缺失）
- 🟡 代码可维护性下降（没有统一的序列化模式）

---

## 架构决策

### 1️⃣ ORM 映射策略强化（Infrastructure Layer）

#### BookshelfModel 数据库表设计（完整版）

```sql
CREATE TABLE bookshelves (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  library_id UUID NOT NULL,                    -- RULE-005: FK
  name VARCHAR(255) NOT NULL,                  -- RULE-006: 名称
  is_basement BOOLEAN DEFAULT FALSE NOT NULL,  -- RULE-010: 标记
  is_pinned BOOLEAN DEFAULT FALSE,             -- 辅助
  is_favorite BOOLEAN DEFAULT FALSE,           -- 辅助
  status VARCHAR(50) DEFAULT 'active',         -- active/archived/deleted
  description TEXT,                            -- 可选元数据
  book_count INTEGER DEFAULT 0,                -- 缓存计数
  created_at TIMESTAMP WITH TIME ZONE,         -- 创建时间
  updated_at TIMESTAMP WITH TIME ZONE,         -- 更新时间

  CONSTRAINT fk_library_id
    FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE,

  CONSTRAINT unique_name_per_library
    UNIQUE (library_id, name),                 -- ✅ RULE-006

  CONSTRAINT check_basement_properties
    CHECK (
      (is_basement = true AND status = 'active') OR
      (is_basement = false)
    )                                          -- Basement 始终活跃
);

CREATE INDEX idx_library_id ON bookshelves(library_id);
CREATE INDEX idx_is_basement ON bookshelves(is_basement)
  WHERE is_basement = true;                    -- RULE-010 查询优化
CREATE INDEX idx_status ON bookshelves(status);
```

#### 字段映射对照表

| ORM 字段 | SQL 类型 | Domain 字段 | Domain 类型 | 约束 | 用途 |
|---------|---------|-----------|-----------|------|------|
| `id` | UUID | `id` | UUID | PK, 非空 | 聚合根标识 |
| `library_id` | UUID | `library_id` | UUID | FK, 非空, 索引 | RULE-005: 属于 Library |
| `name` | VARCHAR(255) | `name` | BookshelfName VO | 非空, UNIQUE with lib_id | RULE-006: 唯一名称 |
| `is_basement` | Boolean | `is_basement` | bool | 非空, 索引, 检查约束 | RULE-010: Basement 标记 |
| `is_pinned` | Boolean | `is_pinned` | bool | 非空, 默认 False | 辅助特性 |
| `is_favorite` | Boolean | `is_favorite` | bool | 非空, 默认 False | 辅助特性 |
| `status` | VARCHAR(50) | `status` | BookshelfStatus | 非空, 索引 | active/archived/deleted |
| `description` | Text | `description` | str | 可空 | 可选元数据 |
| `book_count` | Integer | `book_count` | int | 非空, 默认 0 | 查询优化缓存 |
| `created_at` | DateTime+TZ | `created_at` | DateTime | 非空, UTC | 创建审计 |
| `updated_at` | DateTime+TZ | `updated_at` | DateTime | 非空, UTC | 更新审计 |

#### Round-Trip 验证检清单（增强）

```python
✅ UUID 恒等性: BookshelfModel.id == Bookshelf.id
✅ 库关联: BookshelfModel.library_id == Bookshelf.library_id (RULE-005)
✅ 名称对齐: BookshelfModel.name == BookshelfName(Bookshelf.name).value
✅ Basement 标记: BookshelfModel.is_basement == Bookshelf.is_basement (RULE-010)
✅ 辅助属性: is_pinned, is_favorite, status 同步
✅ 时间戳精度: abs(t_model - t_domain) < 1 秒，UTC 正确
✅ 约束验证: UNIQUE(library_id, name) 生效
✅ 约束验证: Basement 不可被改变为其他状态
✅ 数据完整性: 所有字段无丢失、无截断
```

### 2️⃣ 增强的测试分层策略（Testing Layer）

#### Fixtures 分类与职责（Bookshelf 特化）

```python
# 1️⃣ 常量 Fixtures
@pytest.fixture
def sample_library_id():
    """固定的 Library ID"""
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

@pytest.fixture
def sample_bookshelf_name():
    """固定的 Bookshelf 名称"""
    return "Test Bookshelf"

# 2️⃣ 工厂 Fixtures（特化 for Bookshelf）
@pytest.fixture
def bookshelf_domain_factory(sample_library_id):
    """
    生成 Domain Bookshelf 对象

    支持所有 11 字段的自定义
    """
    def _create(
        library_id=sample_library_id,
        name="Default Bookshelf",
        is_basement=False,
        is_pinned=False,
        is_favorite=False,
        status="active",
        description="",
        book_count=0,
        created_at=None,
        updated_at=None,
    ):
        return Bookshelf(
            id=uuid4(),
            library_id=library_id,
            name=BookshelfName(name),
            is_basement=is_basement,
            is_pinned=is_pinned,
            is_favorite=is_favorite,
            status=BookshelfStatus(status),
            description=description,
            book_count=book_count,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )
    return _create

@pytest.fixture
def bookshelf_model_factory(sample_library_id):
    """
    生成 ORM BookshelfModel 对象

    支持所有 11 字段的自定义，包括 is_basement（关键）
    """
    def _create(
        library_id=sample_library_id,
        name="Default Bookshelf",
        is_basement=False,            # ✅ RULE-010
        is_pinned=False,
        is_favorite=False,
        status="active",
        description="",
        book_count=0,
        created_at=None,
        updated_at=None,
    ):
        now = datetime.now(timezone.utc)
        return BookshelfModel(
            id=uuid4(),
            library_id=library_id,
            name=name,
            is_basement=is_basement,
            is_pinned=is_pinned,
            is_favorite=is_favorite,
            status=status,
            description=description,
            book_count=book_count,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create

# 3️⃣ Mock Repository（RULE-006 验证）
@pytest.fixture
async def mock_bookshelf_repository(bookshelf_domain_factory):
    """
    内存 Mock Repository，支持 RULE-006/010 验证

    关键能力：
    - 检查 UNIQUE(library_id, name) 约束
    - 支持 get_basement_by_library_id()
    """
    class MockBookshelfRepository:
        def __init__(self):
            self.store: Dict[UUID, Bookshelf] = {}

        async def save(self, bookshelf: Bookshelf) -> None:
            # ✅ RULE-006 验证: 同库内名称唯一
            for existing in self.store.values():
                if (existing.library_id == bookshelf.library_id and
                    existing.name == bookshelf.name and
                    existing.id != bookshelf.id):
                    raise BookshelfAlreadyExistsError(
                        f"Bookshelf '{bookshelf.name}' already exists in library"
                    )
            self.store[bookshelf.id] = bookshelf

        async def get_by_id(self, bookshelf_id: UUID) -> Optional[Bookshelf]:
            return self.store.get(bookshelf_id)

        async def get_by_library_id(self, library_id: UUID) -> List[Bookshelf]:
            return [b for b in self.store.values()
                    if b.library_id == library_id]

        async def get_basement_by_library_id(
            self, library_id: UUID
        ) -> Optional[Bookshelf]:
            # ✅ RULE-010 查询
            for b in self.store.values():
                if b.library_id == library_id and b.is_basement:
                    return b
            return None

        async def exists_by_name(
            self, library_id: UUID, name: str
        ) -> bool:
            return any(b.library_id == library_id and b.name.value == name
                      for b in self.store.values())

        async def delete(self, bookshelf_id: UUID) -> None:
            self.store.pop(bookshelf_id, None)

    return MockBookshelfRepository()

# 4️⃣ Service Fixture（使用 Mock）
@pytest.fixture
async def bookshelf_service(mock_bookshelf_repository):
    """BookshelfService with mock repository"""
    return BookshelfService(repository=mock_bookshelf_repository)

# 5️⃣ 数据库 Fixtures（集成测试）
# 复用 Library 的 db_engine, db_session...

@pytest.fixture
async def bookshelf_repository_impl(db_session):
    """真实 BookshelfRepositoryImpl（使用真实 DB）"""
    return BookshelfRepositoryImpl(session=db_session)

@pytest.fixture
async def bookshelf_service_with_db(bookshelf_repository_impl):
    """BookshelfService with real database"""
    return BookshelfService(repository=bookshelf_repository_impl)
```

#### Round-Trip Assertion Helpers（Bookshelf 特化）

```python
async def assert_bookshelf_round_trip(bookshelf, repository):
    """
    验证 Domain → ORM → Domain 往返

    特化点：
    - 验证 RULE-006 约束
    - 验证 RULE-010 is_basement 字段
    """
    await repository.save(bookshelf)
    loaded = await repository.get_by_id(bookshelf.id)

    assert loaded is not None
    assert loaded.id == bookshelf.id
    assert loaded.library_id == bookshelf.library_id
    assert str(loaded.name) == str(bookshelf.name)
    assert loaded.is_basement == bookshelf.is_basement  # ✅ RULE-010
    assert loaded.is_pinned == bookshelf.is_pinned
    assert loaded.is_favorite == bookshelf.is_favorite
    # 时间戳允许 1 秒误差
    assert abs(loaded.created_at.timestamp() -
               bookshelf.created_at.timestamp()) < 1

    return loaded

async def assert_rule_006_duplicate_name(library_id, name, repository):
    """
    验证 RULE-006：同库内名称唯一

    应该抛出 BookshelfAlreadyExistsError
    """
    bookshelf1 = Bookshelf.create(library_id, BookshelfName(name))
    await repository.save(bookshelf1)

    # 第二次保存相同名称应该失败
    bookshelf2 = Bookshelf.create(library_id, BookshelfName(name))
    with pytest.raises(BookshelfAlreadyExistsError):
        await repository.save(bookshelf2)

async def assert_rule_010_basement_query(library_id, repository):
    """
    验证 RULE-010：Basement 查询

    确保 get_basement_by_library_id() 返回正确的 Basement
    """
    basement = await repository.get_basement_by_library_id(library_id)

    if basement is not None:
        assert basement.library_id == library_id
        assert basement.is_basement is True
        assert basement.status == BookshelfStatus.ACTIVE

async def assert_bookshelf_unique_per_library(library_id, repository):
    """
    验证同一 Library 下不能有重复名称
    """
    bookshelves = await repository.get_by_library_id(library_id)

    # 检查名称唯一性
    names = [b.name.value for b in bookshelves]
    assert len(names) == len(set(names)), "Duplicate names detected!"

async def assert_basement_immutable(library_id, repository):
    """
    验证 Basement 不能被删除或重命名
    """
    basement = await repository.get_basement_by_library_id(library_id)

    assert basement is not None
    assert basement.is_basement is True

    # 尝试改变状态应该失败（在 Service 层）
    # 这需要 Service 层的保护
```

### 3️⃣ 测试模式与用例（Bookshelf 特化）

#### 模式 1: RULE-006 约束验证

```python
@pytest.mark.asyncio
async def test_rule_006_unique_name_in_library(
    bookshelf_service,
    sample_library_id,
):
    """
    验证 RULE-006: 同一 Library 下名称唯一

    Test Scenario:
    1. 创建第一个 Bookshelf "Reading"
    2. 尝试创建第二个同名 "Reading"
    3. 期望收到 BookshelfAlreadyExistsError
    """
    # 第一次创建成功
    bookshelf1 = await bookshelf_service.create_bookshelf(
        sample_library_id, "Reading"
    )
    assert bookshelf1.name.value == "Reading"

    # 第二次创建应该失败
    with pytest.raises(BookshelfAlreadyExistsError):
        await bookshelf_service.create_bookshelf(
            sample_library_id, "Reading"
        )

@pytest.mark.asyncio
async def test_rule_006_allows_same_name_different_library(
    bookshelf_service,
    library_service,
):
    """
    验证 RULE-006 作用域：限制在同一 Library 内

    不同 Library 可以有相同名称的 Bookshelf
    """
    lib1 = await library_service.create_library(uuid4(), "Library 1")
    lib2 = await library_service.create_library(uuid4(), "Library 2")

    # 两个库都可以创建同名 Bookshelf
    shelf1 = await bookshelf_service.create_bookshelf(lib1.id, "Reading")
    shelf2 = await bookshelf_service.create_bookshelf(lib2.id, "Reading")

    assert shelf1.library_id != shelf2.library_id
    assert shelf1.name.value == shelf2.name.value
```

#### 模式 2: RULE-010 Basement 验证

```python
@pytest.mark.asyncio
async def test_rule_010_basement_auto_create(
    bookshelf_repository_impl,
    sample_library_id,
):
    """
    验证 RULE-010: Library 创建时自动生成 Basement

    这应该由 Library Service 触发，
    但在这里验证 Repository 能否正确查询
    """
    # 假设 Basement 已由 Library Service 创建
    basement = Bookshelf.create_basement(sample_library_id)
    await bookshelf_repository_impl.save(basement)

    # 验证能够查询到
    loaded = await bookshelf_repository_impl.get_basement_by_library_id(
        sample_library_id
    )
    assert loaded is not None
    assert loaded.is_basement is True

@pytest.mark.asyncio
async def test_rule_010_basement_hidden_flag(
    bookshelf_model_factory,
    db_session,
):
    """
    验证 RULE-010: Basement 有 is_basement=True 标记

    使用 bookshelf_model_factory 创建带 is_basement 的对象
    """
    basement_model = bookshelf_model_factory(
        name="Basement",
        is_basement=True,
    )
    db_session.add(basement_model)
    await db_session.commit()

    # 查询验证
    result = await db_session.execute(
        select(BookshelfModel).where(BookshelfModel.is_basement == True)
    )
    basements = result.scalars().all()

    assert len(basements) >= 1
    assert any(b.name == "Basement" for b in basements)
```

#### 模式 3: Round-Trip 完整验证

```python
@pytest.mark.asyncio
async def test_bookshelf_round_trip_complete(
    bookshelf_domain_factory,
    bookshelf_repository_impl,
):
    """
    完整 Round-Trip 验证：Domain → ORM → Domain

    确保：
    - 所有 11 字段正确持久化
    - UUID 恒等性
    - RULE-006/010 字段完整
    """
    original = bookshelf_domain_factory(
        name="My Collection",
        is_basement=False,
        is_pinned=True,
        is_favorite=False,
    )

    # 保存
    await bookshelf_repository_impl.save(original)

    # 加载 + 验证
    loaded = await assert_bookshelf_round_trip(
        original,
        bookshelf_repository_impl
    )

    # 详细断言
    assert loaded.name.value == "My Collection"
    assert loaded.is_basement is False
    assert loaded.is_pinned is True
    assert loaded.is_favorite is False
```

### 4️⃣ ORM 映射方法（to_dict / from_dict）

#### BookshelfModel 完整实现

```python
class BookshelfModel(Base):
    __tablename__ = "bookshelves"

    id = Column(UUID, primary_key=True, default=uuid4)
    library_id = Column(UUID, ForeignKey("libraries.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_basement = Column(Boolean, default=False, nullable=False, index=True)
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)
    description = Column(Text)
    book_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('library_id', 'name', name='unique_name_per_library'),
    )

    def __repr__(self) -> str:
        """调试表示"""
        return (
            f"BookshelfModel(id={self.id}, library_id={self.library_id}, "
            f"name={self.name!r}, is_basement={self.is_basement})"
        )

    def to_dict(self) -> dict:
        """
        序列化到字典（11 字段全量）

        用途：
        - REST API 响应
        - 测试序列化验证
        - 数据导出
        """
        return {
            "id": str(self.id),
            "library_id": str(self.library_id),
            "name": self.name,
            "is_basement": self.is_basement,           # ✅ RULE-010
            "is_pinned": self.is_pinned,
            "is_favorite": self.is_favorite,
            "status": self.status,
            "description": self.description,
            "book_count": self.book_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "BookshelfModel":
        """
        从字典反序列化

        用途：
        - 数据迁移
        - 测试数据导入
        - API 请求处理
        """
        return BookshelfModel(
            id=UUID(data.get("id")) if data.get("id") else None,
            library_id=UUID(data.get("library_id")),
            name=data.get("name"),
            is_basement=data.get("is_basement", False),
            is_pinned=data.get("is_pinned", False),
            is_favorite=data.get("is_favorite", False),
            status=data.get("status", "active"),
            description=data.get("description"),
            book_count=data.get("book_count", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
```

---

## 实现清单

✅ **必须完成**（本 ADR 关键）：

| 项目 | 文件 | 内容 | 优先级 |
|------|------|------|--------|
| UNIQUE 约束 | `models.py` | `UniqueConstraint('library_id', 'name')` | 🔴 P0 |
| is_basement 字段 | `models.py` | Boolean 字段 + 索引 | 🔴 P0 |
| Round-Trip 方法 | `models.py` | `to_dict()`, `from_dict()` (11 字段) | 🔴 P0 |
| Model factory | `conftest.py` | `bookshelf_model_factory` | 🔴 P0 |
| Mock with RULE-006 | `conftest.py` | `mock_bookshelf_repository` 验证约束 | 🟡 P1 |
| RULE-010 support | `conftest.py` | `get_basement_by_library_id()` | 🟡 P1 |
| Round-Trip helper | `conftest.py` | `assert_bookshelf_round_trip()` | 🟡 P1 |
| 常量 Fixtures | `conftest.py` | `sample_library_id`, `sample_bookshelf_name` | 🟢 P2 |

🔮 **后续优化**（超出本 ADR 范围）：

- [ ] 批量约束检查优化
- [ ] PostgreSQL 特定约束（CHECK 语句）
- [ ] 缓存 Basement 查询结果
- [ ] 性能基准测试（UNIQUE 约束开销）
- [ ] 数据迁移脚本（添加 is_basement 到现有数据）

---

## 关键设计决策

### 1️⃣ 数据库约束强化（UNIQUE）

**决策**：使用 SQLAlchemy `UniqueConstraint` 强制 UNIQUE(library_id, name)

**原因**：
- ✅ 数据完整性保障（DB 级别）
- ✅ 并发冲突检测（多进程安全）
- ✅ 文档明确（约束在 ORM 中可见）

**对标**：
- PostgreSQL UNIQUE 约束最佳实践
- 与 ADR-012 (Library RULE-001) 一致

### 2️⃣ Basement 标记字段（is_basement）

**决策**：添加 Boolean 字段 `is_basement` 而非用特殊名称

**原因**：
- ✅ 清晰的查询条件：`WHERE is_basement = true`
- ✅ 索引高效：`CREATE INDEX idx_is_basement WHERE is_basement = true`
- ✅ 灵活性：支持多 Basement（极少见，但可扩展）

**权衡**：
- ⚠️ 增加 ORM 字段数（可接受，11 字段仍在合理范围）
- ✅ 相比复杂的查询逻辑，字段更直观

### 3️⃣ 序列化方法（to_dict / from_dict）

**决策**：全 11 字段序列化，支持完整 round-trip

**原因**：
- ✅ 测试完整性验证
- ✅ API 响应一致
- ✅ 迁移脚本兼容性

**对标**：
- 与 ADR-012 (Library) 一致
- 符合 RESTful 最佳实践

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| UNIQUE 约束导致并发冲突 | 应用层 L1 检查 + 异常转译 |
| is_basement 业务逻辑复杂化 | 在 Service 层集中管理，Repository 只查询 |
| 时间戳精度丢失 | 允许 1 秒误差、UTC 时区确保 |
| Mock Repository 与真实 DB 不同步 | 集成测试验证，CI/CD 用真实 DB |
| Basement 隐藏性未强制 | Service 层保护（不允许重命名/删除） |

---

## 对标业界最佳实践

✅ 唯一性约束（UNIQUE constraint）- 数据完整性
✅ Repository Pattern with exception translation
✅ Round-Trip Testing - ORM 映射验证
✅ Factory Pattern - 测试数据生成
✅ Soft Delete Pattern - 审计可追溯性
✅ Clean Code - 命名清晰，职责分离

---

## 相关 ADR

- **ADR-009**: Bookshelf Service & Repository Design（服务层）
- **ADR-012**: Library Models & Testing Layer（参考模式）
- **ADR-001**: Independent Aggregate Roots（聚合根设计）
- **ADR-002**: Basement Pattern（软删除）

---

## 后续工作

### 本 ADR 完成后

1. ✅ 修复 models.py（UNIQUE + is_basement + 序列化）
2. ✅ 优化 conftest.py（factories + Mock + helpers）
3. 📊 编写集成测试 tests/test_bookshelf_models.py
4. 📊 编写 round-trip 测试 tests/test_bookshelf_round_trip.py
5. 📊 编写约束测试 tests/test_bookshelf_constraints.py
6. 测试覆盖率目标：>= 90%

### Book & Block 应用

应用相同改进模式：
- ADR-014-book-models-testing-layer.md
- ADR-015-block-models-testing-layer.md

---

## 版本历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2025-11-12 | Architecture Team | 初版发布（基于 Bookshelf 改进） |

---

**批准者**: TBD
**有效期**: 长期（直到代码证明需要调整）

