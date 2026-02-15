# ADR-014: Book Models & Testing Layer 架构设计

**状态**: ACCEPTED
**日期**: 2025-11-12
**涉及模块**: Book Domain (Infrastructure Layer & Testing Layer)
**优先级**: P1 (RULE-011/012 Permission & Soft Delete Verification)
**关联 ADR**: ADR-010 (Service & Repository), ADR-013 (Bookshelf Models Pattern), ADR-001 (Independent Aggregates)

---

## 问题陈述

Book 模块在 infrastructure 和 testing 层存在关键缺陷，无法支持 RULE-011 和 RULE-012 的完整验证：

### 核心问题

1. **RULE-011 权限检查缺失**: 缺少 `library_id` 冗余 FK
   - 无法验证跨 Bookshelf 转移时的库权限
   - 应用层检查与 DB 约束分离

2. **RULE-012 软删除不完整**: 缺少 `soft_deleted_at` 字段
   - 无法标记 Basement 中的 Books
   - Repository 查询无法过滤已删除的 Books

3. **ORM 映射方法缺失**: 无 `to_dict()` / `from_dict()`
   - Round-trip 验证无法进行
   - 序列化不规范

4. **测试层不成熟**: conftest.py 缺少关键能力
   - 无 ORM factory（book_model_factory）
   - Mock Repository 不验证 RULE-011/012 约束
   - 缺少 Basement 查询支持

5. **权限检查边界情况**: 缺少集成测试覆盖
   - 跨库转移应被拒绝但无测试
   - Basement 过滤验证缺失
   - 恢复操作验证缺失

### 架构影响

这些缺陷导致：
- 🔴 数据完整性风险（权限检查失效）
- 🔴 功能实现风险（Basement 模式无法支撑）
- 🟡 测试覆盖不足（往返验证缺失）
- 🟡 代码可维护性下降（没有统一的序列化模式）

---

## 架构决策

### 1️⃣ ORM 映射策略强化（Infrastructure Layer）

#### BookModel 数据库表设计（完整版）

```sql
CREATE TABLE books (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bookshelf_id UUID NOT NULL,                       -- RULE-009: FK to parent
  library_id UUID NOT NULL,                         -- RULE-011: 冗余 FK for permission
  title VARCHAR(255) NOT NULL,                      -- 书名
  summary TEXT,                                     -- 摘要
  is_pinned BOOLEAN DEFAULT FALSE,                  -- 辅助
  due_at TIMESTAMP WITH TIME ZONE,                  -- 可选
  status VARCHAR(50) DEFAULT 'draft',               -- draft/active/archived
  block_count INTEGER DEFAULT 0,                    -- 缓存计数
  soft_deleted_at TIMESTAMP WITH TIME ZONE,         -- RULE-012: 软删除标记
  created_at TIMESTAMP WITH TIME ZONE,              -- 创建时间
  updated_at TIMESTAMP WITH TIME ZONE,              -- 更新时间

  CONSTRAINT fk_bookshelf_id
    FOREIGN KEY (bookshelf_id) REFERENCES bookshelves(id) ON DELETE CASCADE,

  CONSTRAINT fk_library_id
    FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE
);

CREATE INDEX idx_bookshelf_id ON books(bookshelf_id);
CREATE INDEX idx_library_id ON books(library_id);              -- RULE-011 权限检查
CREATE INDEX idx_soft_deleted_at ON books(soft_deleted_at)
  WHERE soft_deleted_at IS NULL;                              -- RULE-012 过滤
```

#### 字段映射对照表

| ORM 字段 | SQL 类型 | Domain 字段 | Domain 类型 | 约束 | 用途 |
|---------|---------|-----------|-----------|------|------|
| `id` | UUID | `id` | UUID | PK, 非空 | 聚合根标识 |
| `bookshelf_id` | UUID | `bookshelf_id` | UUID | FK, 非空, 索引 | RULE-009: 属于 Bookshelf |
| `library_id` | UUID | `library_id` | UUID | FK, 非空, 索引 | RULE-011: 权限检查 |
| `title` | VARCHAR(255) | `title` | BookTitle VO | 非空 | 书籍名称 |
| `summary` | Text | `summary` | BookSummary VO | 可空 | 可选摘要 |
| `is_pinned` | Boolean | `is_pinned` | bool | 非空, 默认 False | 辅助特性 |
| `due_at` | DateTime+TZ | `due_at` | DateTime | 可空 | 截止日期 |
| `status` | VARCHAR(50) | `status` | BookStatus | 非空 | draft/active/archived |
| `block_count` | Integer | `block_count` | int | 非空, 默认 0 | 查询优化缓存 |
| `soft_deleted_at` | DateTime+TZ | `soft_deleted_at` | DateTime | 可空, 索引 | RULE-012: 软删除标记 |
| `created_at` | DateTime+TZ | `created_at` | DateTime | 非空, UTC | 创建审计 |
| `updated_at` | DateTime+TZ | `updated_at` | DateTime | 非空, UTC | 更新审计 |

#### Round-Trip 验证检清单（增强）

```python
✅ UUID 恒等性: BookModel.id == Book.id
✅ Bookshelf 关联: BookModel.bookshelf_id == Book.bookshelf_id (RULE-009)
✅ 库权限: BookModel.library_id == Book.library_id (RULE-011)
✅ 书名对齐: BookModel.title == BookTitle(Book.title).value
✅ 软删除标记: BookModel.soft_deleted_at == Book.soft_deleted_at (RULE-012)
✅ 辅助属性: is_pinned, due_at, status 同步
✅ 时间戳精度: abs(t_model - t_domain) < 1 秒，UTC 正确
✅ 数据完整性: 所有字段无丢失、无截断
```

### 2️⃣ 增强的测试分层策略（Testing Layer）

#### Fixtures 分类与职责（Book 特化）

```python
# 1️⃣ 常量 Fixtures
@pytest.fixture
def sample_library_id():
    """固定的 Library ID"""
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

@pytest.fixture
def sample_bookshelf_id():
    """固定的 Bookshelf ID"""
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

@pytest.fixture
def sample_book_title():
    """固定的 Book 标题"""
    return "Test Book"

# 2️⃣ 工厂 Fixtures（特化 for Book）
@pytest.fixture
def book_domain_factory(sample_library_id, sample_bookshelf_id):
    """
    生成 Domain Book 对象

    支持所有 11 字段的自定义，包括 soft_deleted_at（RULE-012）
    """
    def _create(
        book_id=None,
        bookshelf_id=None,
        library_id=None,
        title="Test Book",
        summary=None,
        status="draft",
        is_pinned=False,
        due_at=None,
        block_count=0,
        soft_deleted_at=None,  # ✅ RULE-012
        created_at=None,
        updated_at=None,
    ):
        return Book(
            id=book_id or uuid4(),
            bookshelf_id=bookshelf_id or sample_bookshelf_id,
            library_id=library_id or sample_library_id,  # ✅ RULE-011
            title=BookTitle(title),
            summary=BookSummary(summary) if summary else None,
            status=BookStatus(status),
            is_pinned=is_pinned,
            due_at=due_at,
            block_count=block_count,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )
    return _create

@pytest.fixture
def book_model_factory(sample_library_id, sample_bookshelf_id):
    """
    生成 ORM BookModel 对象

    支持所有 12 字段的自定义（包括 library_id 和 soft_deleted_at）
    """
    def _create(
        book_id=None,
        bookshelf_id=None,
        library_id=None,
        title="Test Book",
        summary=None,
        status="draft",
        is_pinned=False,
        due_at=None,
        block_count=0,
        soft_deleted_at=None,  # ✅ RULE-012
        created_at=None,
        updated_at=None,
    ):
        now = datetime.now(timezone.utc)
        return BookModel(
            id=book_id or uuid4(),
            bookshelf_id=bookshelf_id or sample_bookshelf_id,
            library_id=library_id or sample_library_id,  # ✅ RULE-011
            title=title,
            summary=summary,
            status=status,
            is_pinned=is_pinned,
            due_at=due_at,
            block_count=block_count,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create

# 3️⃣ Mock Repository（RULE-011/012 验证）
@pytest.fixture
async def mock_book_repository(sample_library_id, sample_bookshelf_id):
    """
    内存 Mock Repository，支持 RULE-011 和 RULE-012 验证

    关键能力：
    - library_id 一致性检查（不同 Library 拒绝）
    - soft_deleted_at 过滤（活跃 Books 隐藏已删除）
    - get_deleted_books() 检索 Basement
    """
    class MockBookRepository:
        def __init__(self):
            self.store: Dict[UUID, Book] = {}
            self.bookshelves = {}  # 用于权限检查

        async def save(self, book: Book) -> None:
            # ✅ RULE-011: 权限检查（library_id 一致性）
            if book.bookshelf_id in self.bookshelves:
                bookshelf = self.bookshelves[book.bookshelf_id]
                if book.library_id != bookshelf.library_id:
                    raise PermissionError(
                        f"Book library_id {book.library_id} does not match "
                        f"Bookshelf library_id {bookshelf.library_id}"
                    )

            self.store[book.id] = book

        async def get_by_id(self, book_id: UUID) -> Optional[Book]:
            book = self.store.get(book_id)
            # ✅ RULE-012: 自动过滤软删除的 Book
            if book and book.soft_deleted_at is not None:
                return None
            return book

        async def get_by_bookshelf_id(self, bookshelf_id: UUID) -> List[Book]:
            # ✅ RULE-012: 仅返回未删除的 Books
            return [b for b in self.store.values()
                    if b.bookshelf_id == bookshelf_id and
                       b.soft_deleted_at is None]

        async def get_deleted_books(self, bookshelf_id: UUID) -> List[Book]:
            # ✅ RULE-013: 检索 Basement 中的 Books
            return [b for b in self.store.values()
                    if b.bookshelf_id == bookshelf_id and
                       b.soft_deleted_at is not None]

        async def delete(self, book_id: UUID) -> None:
            # 禁用硬删除，强制软删除模式
            raise NotImplementedError(
                "Use soft delete: set book.soft_deleted_at and call save()"
            )

    return MockBookRepository()

# 4️⃣ Service Fixture（使用 Mock）
@pytest.fixture
async def book_service(mock_book_repository):
    """BookService with mock repository"""
    return BookService(repository=mock_book_repository)
```

#### Round-Trip Assertion Helpers（Book 特化）

```python
async def assert_book_round_trip(book, repository):
    """
    验证 Domain → ORM → Domain 往返

    特化点：
    - 验证 RULE-011 library_id 字段
    - 验证 RULE-012 soft_deleted_at 字段
    """
    await repository.save(book)
    loaded = await repository.get_by_id(book.id)

    assert loaded is not None
    assert loaded.id == book.id
    assert loaded.bookshelf_id == book.bookshelf_id
    assert loaded.library_id == book.library_id      # ✅ RULE-011
    assert str(loaded.title) == str(book.title)
    assert loaded.is_pinned == book.is_pinned
    assert loaded.soft_deleted_at == book.soft_deleted_at  # ✅ RULE-012
    # 时间戳允许 1 秒误差
    assert abs(loaded.created_at.timestamp() -
               book.created_at.timestamp()) < 1

    return loaded

async def assert_rule_011_move_permission(
    book_id, source_shelf, target_shelf, repository
):
    """
    验证 RULE-011：Book 转移权限

    应该拒绝不同 Library 的转移
    """
    book = await repository.get_by_id(book_id)

    if target_shelf.library_id != book.library_id:
        # 不同 Library，应该失败
        with pytest.raises(PermissionError):
            book.bookshelf_id = target_shelf.id
            await repository.save(book)
    else:
        # 同 Library，应该成功
        book.bookshelf_id = target_shelf.id
        await repository.save(book)

        loaded = await repository.get_by_id(book.id)
        assert loaded.bookshelf_id == target_shelf.id

async def assert_rule_012_soft_delete(book_id, repository):
    """
    验证 RULE-012：Book 软删除

    确保：
    - 设置 soft_deleted_at 后不可见
    - 可通过 get_deleted_books() 检索
    """
    book = await repository.get_by_id(book_id)
    assert book is not None

    # 标记软删除
    book.soft_deleted_at = datetime.now(timezone.utc)
    await repository.save(book)

    # 不可见
    loaded = await repository.get_by_id(book_id)
    assert loaded is None

    # 可通过 deleted 查询检索
    deleted = await repository.get_deleted_books(book.bookshelf_id)
    assert book_id in [b.id for b in deleted]

async def assert_rule_013_restore(book_id, bookshelf_id, repository):
    """
    验证 RULE-013：Book 从 Basement 恢复

    清除 soft_deleted_at 后应该重新可见
    """
    # 确保 Book 在 Basement 中
    deleted = await repository.get_deleted_books(bookshelf_id)
    assert book_id in [b.id for b in deleted]

    # 恢复（清除 soft_deleted_at）
    book = [b for b in await repository.get_deleted_books(bookshelf_id)
            if b.id == book_id][0]
    book.soft_deleted_at = None
    await repository.save(book)

    # 应该重新可见
    loaded = await repository.get_by_id(book_id)
    assert loaded is not None
    assert loaded.soft_deleted_at is None
```

### 3️⃣ 测试模式与用例（Book 特化）

#### 模式 1: RULE-011 权限验证

```python
@pytest.mark.asyncio
async def test_rule_011_cross_library_transfer_blocked(
    book_service,
    sample_library_id,
    bookshelf_repo,
):
    """
    验证 RULE-011: 不同 Library 的转移被拒绝

    Test Scenario:
    1. 创建 Library A 和 B
    2. 在 Library A 中创建 Book
    3. 尝试转移到 Library B 的 Bookshelf
    4. 期望收到 PermissionError
    """
    lib_a = await library_service.create_library(uuid4(), "A")
    lib_b = await library_service.create_library(uuid4(), "B")

    shelf_a = await bookshelf_service.create_bookshelf(lib_a.id, "Shelf A")
    shelf_b = await bookshelf_service.create_bookshelf(lib_b.id, "Shelf B")

    book = await book_service.create_book(shelf_a.id, lib_a.id, "My Book")

    # 尝试转移到 Library B（应该失败）
    with pytest.raises(PermissionError):
        await book_service.move_to_bookshelf(book.id, shelf_b.id)

@pytest.mark.asyncio
async def test_rule_011_same_library_transfer_allowed(
    book_service,
    sample_library_id,
):
    """
    验证 RULE-011 作用域：同 Library 内转移允许
    """
    lib = await library_service.create_library(uuid4(), "My Library")
    shelf1 = await bookshelf_service.create_bookshelf(lib.id, "Shelf 1")
    shelf2 = await bookshelf_service.create_bookshelf(lib.id, "Shelf 2")

    book = await book_service.create_book(shelf1.id, lib.id, "My Book")

    # 转移到同库的另一个 Bookshelf（应该成功）
    moved = await book_service.move_to_bookshelf(book.id, shelf2.id)

    assert moved.bookshelf_id == shelf2.id
    assert moved.library_id == lib.id  # library_id 不变
```

#### 模式 2: RULE-012 软删除验证

```python
@pytest.mark.asyncio
async def test_rule_012_soft_delete_hides_book(
    book_service,
    book_repository_impl,
    sample_library_id,
):
    """
    验证 RULE-012: Book 软删除（移到 Basement）

    Test Scenario:
    1. 创建 Book
    2. 删除（转移到 Basement）
    3. 期望 get_by_id() 返回 None
    4. 期望 get_deleted_books() 能检索
    """
    lib = await library_service.create_library(uuid4(), "My Library")
    shelf = await bookshelf_service.create_bookshelf(lib.id, "My Shelf")
    basement = await bookshelf_service.get_basement_bookshelf(lib.id)

    book = await book_service.create_book(shelf.id, lib.id, "My Book")
    book_id = book.id

    # 删除（实际是转移到 Basement）
    await book_service.delete_book(book_id)

    # 不可见
    loaded = await book_repository_impl.get_by_id(book_id)
    assert loaded is None

    # 可通过 get_deleted_books 检索
    deleted = await book_repository_impl.get_deleted_books(basement.id)
    assert book_id in [b.id for b in deleted]

@pytest.mark.asyncio
async def test_rule_013_restore_from_basement(
    book_service,
    book_repository_impl,
    sample_library_id,
):
    """
    验证 RULE-013: Book 从 Basement 恢复

    Test Scenario:
    1. 创建 Book 并删除（到 Basement）
    2. 恢复到原 Bookshelf（或其他）
    3. 期望 get_by_id() 返回 Book
    4. 期望 soft_deleted_at 被清除
    """
    lib = await library_service.create_library(uuid4(), "My Library")
    shelf1 = await bookshelf_service.create_bookshelf(lib.id, "Shelf 1")
    shelf2 = await bookshelf_service.create_bookshelf(lib.id, "Shelf 2")

    book = await book_service.create_book(shelf1.id, lib.id, "My Book")
    book_id = book.id

    # 删除（到 Basement）
    await book_service.delete_book(book_id)
    assert await book_repository_impl.get_by_id(book_id) is None

    # 恢复到 Shelf 2
    restored = await book_service.restore_from_basement(book_id, shelf2.id)

    # 应该重新可见
    loaded = await book_repository_impl.get_by_id(book_id)
    assert loaded is not None
    assert loaded.bookshelf_id == shelf2.id
    assert loaded.soft_deleted_at is None
```

#### 模式 3: Round-Trip 完整验证

```python
@pytest.mark.asyncio
async def test_book_round_trip_complete(
    book_domain_factory,
    book_repository_impl,
):
    """
    完整 Round-Trip 验证：Domain → ORM → Domain

    确保：
    - 所有 12 字段正确持久化
    - UUID 恒等性
    - RULE-011/012 字段完整
    """
    original = book_domain_factory(
        title="My Book",
        is_pinned=True,
        status="active",
    )

    # 保存
    await book_repository_impl.save(original)

    # 加载 + 验证
    loaded = await assert_book_round_trip(original, book_repository_impl)

    # 详细断言
    assert loaded.title.value == "My Book"
    assert loaded.is_pinned is True
    assert loaded.library_id == original.library_id
```

### 4️⃣ ORM 映射方法（to_dict / from_dict）

#### BookModel 完整实现

```python
class BookModel(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bookshelf_id = Column(UUID(as_uuid=True), ForeignKey("bookshelves.id"), nullable=False, index=True)
    library_id = Column(UUID(as_uuid=True), ForeignKey("libraries.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    is_pinned = Column(Boolean, default=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="draft")
    block_count = Column(Integer, default=0)
    soft_deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"BookModel(id={self.id}, title={self.title!r}, "
            f"library_id={self.library_id}, soft_deleted_at={self.soft_deleted_at})"
        )

    def to_dict(self) -> dict:
        """
        序列化到字典（12 字段全量）

        用途：
        - REST API 响应
        - 测试序列化验证
        - 数据导出
        """
        return {
            "id": str(self.id),
            "bookshelf_id": str(self.bookshelf_id),
            "library_id": str(self.library_id),           # ✅ RULE-011
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "is_pinned": self.is_pinned,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "block_count": self.block_count,
            "soft_deleted_at": self.soft_deleted_at.isoformat() if self.soft_deleted_at else None,  # ✅ RULE-012
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "BookModel":
        """
        从字典反序列化

        用途：
        - 数据迁移
        - 测试数据导入
        - API 请求处理
        """
        return BookModel(
            id=UUID(data.get("id")) if data.get("id") else None,
            bookshelf_id=UUID(data.get("bookshelf_id")) if data.get("bookshelf_id") else None,
            library_id=UUID(data.get("library_id")) if data.get("library_id") else None,
            title=data.get("title"),
            summary=data.get("summary"),
            status=data.get("status", "draft"),
            is_pinned=data.get("is_pinned", False),
            due_at=data.get("due_at"),
            block_count=data.get("block_count", 0),
            soft_deleted_at=data.get("soft_deleted_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
```

---

## 实现清单

✅ **必须完成**（本 ADR 关键）：

| 项目 | 文件 | 内容 | 优先级 |
|------|------|------|--------|
| library_id 字段 | `models.py` | UUID FK (NOT NULL, indexed) | 🔴 P0 |
| soft_deleted_at 字段 | `models.py` | DateTime nullable, indexed | 🔴 P0 |
| Round-Trip 方法 | `models.py` | `to_dict()`, `from_dict()` (12 字段) | 🔴 P0 |
| Model factory | `conftest.py` | `book_model_factory` | 🔴 P0 |
| Mock with RULE-011 | `conftest.py` | `mock_book_repository` 权限验证 | 🔴 P0 |
| Mock with RULE-012 | `conftest.py` | `get_by_id` 过滤 + `get_deleted_books` | 🔴 P0 |
| Round-Trip helper | `conftest.py` | `assert_book_round_trip()` | 🟡 P1 |
| RULE-011 helper | `conftest.py` | `assert_rule_011_move_permission()` | 🟡 P1 |
| RULE-012 helper | `conftest.py` | `assert_rule_012_soft_delete()` | 🟡 P1 |
| 常量 Fixtures | `conftest.py` | `sample_library_id` 等 | 🟢 P2 |

🔮 **后续优化**（超出本 ADR 范围）：

- [ ] 批量软删除优化
- [ ] 恢复操作的事务性保证
- [ ] 性能基准测试（soft_deleted_at 索引效率）
- [ ] 数据迁移脚本（添加 library_id/soft_deleted_at 到现有 Books）

---

## 关键设计决策

### 1️⃣ 库权限冗余 FK（library_id）

**决策**：添加冗余 `library_id` FK 而非通过 Bookshelf JOIN 获取

**原因**：
- ✅ RULE-011 权限检查高效（不需要 JOIN）
- ✅ 数据完整性保障（DB 级外键约束）
- ✅ 级联删除安全（Library 删除时自动清理）
- ✅ 查询性能（直接过滤 library_id）

**权衡**：
- ⚠️ 多 FK 维护复杂（但数据库一致性机制可保证）
- ✅ 相比复杂 JOIN 查询，字段更直观

### 2️⃣ 软删除标记（soft_deleted_at）

**决策**：使用 DateTime 字段 `soft_deleted_at` 标记而非布尔 flag

**原因**：
- ✅ 保留删除时间信息（审计）
- ✅ 索引高效：`WHERE soft_deleted_at IS NULL`
- ✅ 恢复支持：清除字段即恢复
- ✅ 灵活性：支持时间范围查询

**对标**：
- PostgreSQL 最佳实践（时间戳软删除）
- 与 ADR-002 (Basement Pattern) 一致

### 3️⃣ 序列化方法（to_dict / from_dict）

**决策**：全 12 字段序列化，支持完整 round-trip（包括 library_id 和 soft_deleted_at）

**原因**：
- ✅ 权限检查完整验证
- ✅ 软删除状态可序列化
- ✅ API 响应一致性

**对标**：
- 与 ADR-013 (Bookshelf) 一致
- 符合 RESTful 最佳实践

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 冗余 FK 维护复杂 | DB 外键约束确保一致性；应用层检查验证 |
| 跨库转移逻辑复杂 | Service L1 集中管理；Mock 完整验证 |
| 时间戳精度丢失 | 允许 1 秒误差、UTC 时区确保 |
| soft_deleted_at 索引导致查询膨胀 | 使用 WHERE IS NULL 过滤条件精确；监控查询计划 |
| Mock Repository 与真实 DB 不同步 | 集成测试验证，CI/CD 用真实 DB |

---

## 对标业界最佳实践

✅ 外键约束强制数据完整性
✅ Repository Pattern with exception translation
✅ Round-Trip Testing - ORM 映射验证
✅ Factory Pattern - 测试数据生成
✅ Soft Delete Pattern - 审计可追踪性
✅ Clean Code - 命名清晰，职责分离
✅ Permission-aware ORM（冗余 FK 权限）

---

## 相关 ADR

- **ADR-010**: Book Service & Repository Design（服务层）
- **ADR-013**: Bookshelf Models & Testing Layer（参考模式）
- **ADR-014**: Book Models & Testing Layer（本 ADR）
- **ADR-001**: Independent Aggregate Roots（聚合根设计）
- **ADR-002**: Basement Pattern（软删除）

---

## 后续工作

### 本 ADR 完成后

1. ✅ 修复 models.py（library_id + soft_deleted_at + 序列化）
2. ✅ 优化 conftest.py（factories + Mock + helpers）
3. 📊 编写集成测试 tests/test_book_models.py
4. 📊 编写 round-trip 测试 tests/test_book_round_trip.py
5. 📊 编写权限测试 tests/test_book_permissions.py
6. 📊 编写软删除测试 tests/test_book_soft_delete.py
7. 测试覆盖率目标：>= 90%

### Block 应用

应用相同改进模式：
- ADR-015-block-models-testing-layer.md

---

## 版本历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2025-11-12 | Architecture Team | 初版发布（基于 Book 权限和软删除需求） |

---

**批准者**: TBD
**有效期**: 长期（直到代码证明需要调整）

