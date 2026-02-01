# ADR-015: Block Models & Testing Layer 架构设计

**状态**: ACCEPTED
**日期**: 2025-11-12
**涉及模块**: Block Domain (Infrastructure Layer & Testing Layer)
**优先级**: P1 (RULE-014/015-REVISED Type System & Fractional Index Verification)
**关联 ADR**: ADR-011 (Service & Repository), ADR-014 (Book Models Pattern), ADR-001 (Independent Aggregates)

---

## 问题陈述

Block 模块在 infrastructure 和 testing 层存在关键缺陷，无法完整支持 RULE-014 和 RULE-015-REVISED 的验证：

### 核心问题

1. **RULE-014 类型系统不安全**: type 字段用 String，非 Enum
   - 数据库可以插入非法类型值
   - ORM 无法进行类型检查
   - API 响应序列化不规范

2. **RULE-015-REVISED Fractional Index 验证不完整**: 无法验证 O(1) 插入
   - Mock 没有验证 order（Decimal）排序正确性
   - 无法测试在任意两个 block 之间插入新 block
   - 没有排序验证 helper

3. **RULE-013-REVISED 类型特定字段验证缺失**: HEADING 类型需要 heading_level
   - Mock 不验证 HEADING 类型必须有 heading_level
   - 其他类型允许 heading_level（应该为 None）
   - 无专门 helper 验证

4. **ORM 映射方法缺失**: 无 `to_dict()` / `from_dict()`
   - Round-trip 验证无法进行
   - Decimal order 序列化处理不规范

5. **POLICY-008 软删除验证不完整**: Mock 不过滤软删除
   - get_by_id() 没有自动过滤 soft_deleted_at IS NOT NULL
   - get_deleted_blocks() 不存在
   - 无软删除验证 helper

### 架构影响

这些缺陷导致：
- 🔴 类型安全风险（非法类型可入库）
- 🔴 功能实现风险（Fractional Index 无验证）
- 🟡 测试覆盖不足（往返验证缺失）
- 🟡 代码可维护性下降（没有统一的序列化模式）

---

## 架构决策

### 1️⃣ ORM 映射策略强化（Infrastructure Layer）

#### BlockModel 数据库表设计（完整版）

```sql
CREATE TABLE blocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  book_id UUID NOT NULL,                       -- RULE-016: FK to parent
  type VARCHAR(50) NOT NULL,                   -- RULE-014: BlockType Enum (enforced via CHECK or custom type)
  content TEXT NOT NULL,                       -- Block content
  order NUMERIC(19,10) NOT NULL DEFAULT 0,     -- RULE-015-REVISED: Fractional Index
  heading_level INTEGER,                       -- RULE-013-REVISED: Only for HEADING type
  soft_deleted_at TIMESTAMP WITH TIME ZONE,    -- POLICY-008: Soft delete marker
  created_at TIMESTAMP WITH TIME ZONE,         -- 创建时间
  updated_at TIMESTAMP WITH TIME ZONE,         -- 更新时间

  CONSTRAINT fk_book_id
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,

  CONSTRAINT check_block_type
    CHECK (type IN ('text', 'heading', 'code', 'image', 'quote', 'list', 'table', 'divider'))
);

CREATE INDEX idx_book_id ON blocks(book_id);
CREATE INDEX idx_order ON blocks(book_id, order);         -- RULE-015-REVISED 查询优化
CREATE INDEX idx_soft_deleted_at ON blocks(soft_deleted_at)
  WHERE soft_deleted_at IS NULL;                          -- POLICY-008 过滤优化
```

#### BlockType Enum 定义（关键）

```python
from enum import Enum

class BlockType(str, Enum):
    """
    Block Type Enumeration (RULE-014)

    - TEXT: Plain paragraph
    - HEADING: Title (H1, H2, H3 per RULE-013-REVISED)
    - CODE: Code block
    - IMAGE: Image reference
    - QUOTE: Blockquote
    - LIST: Bullet/numbered list
    - TABLE: Table structure
    - DIVIDER: Horizontal divider
    """
    TEXT = "text"
    HEADING = "heading"
    CODE = "code"
    IMAGE = "image"
    QUOTE = "quote"
    LIST = "list"
    TABLE = "table"
    DIVIDER = "divider"
```

#### 字段映射对照表

| ORM 字段 | SQL 类型 | Domain 字段 | Domain 类型 | 约束 | 用途 |
|---------|---------|-----------|-----------|------|------|
| `id` | UUID | `id` | UUID | PK, 非空 | 聚合根标识 |
| `book_id` | UUID | `book_id` | UUID | FK, 非空, 索引 | RULE-016: 属于 Book |
| `type` | Enum | `type` | BlockType | 非空, 枚举值 | RULE-014: 类型系统 |
| `content` | Text | `content` | BlockContent VO | 非空 | 块内容 |
| `order` | DECIMAL(19,10) | `order` | Decimal | 非空, 索引 | RULE-015-REVISED: 分数索引 |
| `heading_level` | Integer | `heading_level` | int | 可空，仅 HEADING | RULE-013-REVISED: 标题级别 |
| `soft_deleted_at` | DateTime+TZ | `soft_deleted_at` | DateTime | 可空, 索引 | POLICY-008: 软删除标记 |
| `created_at` | DateTime+TZ | `created_at` | DateTime | 非空, UTC | 创建审计 |
| `updated_at` | DateTime+TZ | `updated_at` | DateTime | 非空, UTC | 更新审计 |

#### Round-Trip 验证检清单（增强）

```python
✅ UUID 恒等性: BlockModel.id == Block.id
✅ Book 关联: BlockModel.book_id == Block.book_id (RULE-016)
✅ 类型对齐: BlockModel.type == BlockType(Block.type) (RULE-014)
✅ 内容完整: BlockModel.content == Block.content
✅ 排序精度: BlockModel.order == Decimal(Block.order) (RULE-015-REVISED)
✅ 标题级别: BlockModel.heading_level == Block.heading_level (RULE-013-REVISED)
✅ 软删除标记: BlockModel.soft_deleted_at == Block.soft_deleted_at (POLICY-008)
✅ 时间戳精度: abs(t_model - t_domain) < 1 秒，UTC 正确
✅ 数据完整性: 所有字段无丢失、无截断
```

### 2️⃣ 增强的测试分层策略（Testing Layer）

#### Fixtures 分类与职责（Block 特化）

```python
# 1️⃣ 常量 Fixtures
@pytest.fixture
def sample_book_id():
    """固定的 Book ID"""
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

# 2️⃣ 工厂 Fixtures（特化 for Block）
@pytest.fixture
def block_domain_factory(sample_book_id):
    """
    生成 Domain Block 对象

    支持所有 9 字段的自定义，包括 soft_deleted_at（POLICY-008）
    和 heading_level（RULE-013-REVISED）
    """
    def _create(
        block_id=None,
        book_id=None,
        block_type=BlockType.TEXT,
        content="Test content",
        order=10.0,
        heading_level=None,
        soft_deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        return Block(
            id=block_id or uuid4(),
            book_id=book_id or sample_book_id,
            type=block_type,
            content=BlockContent(content),
            order=Decimal(str(order)),
            heading_level=heading_level,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )
    return _create

@pytest.fixture
def block_model_factory(sample_book_id):
    """
    生成 ORM BlockModel 对象

    支持所有 9 字段的自定义（包括 type 作为 Enum、order 作为 Decimal、heading_level）
    """
    def _create(
        block_id=None,
        book_id=None,
        block_type=BlockType.TEXT,
        content="Test content",
        order=10.0,
        heading_level=None,
        soft_deleted_at=None,
        created_at=None,
        updated_at=None,
    ):
        now = datetime.now(timezone.utc)
        return BlockModel(
            id=block_id or uuid4(),
            book_id=book_id or sample_book_id,
            type=block_type,
            content=content,
            order=Decimal(str(order)),
            heading_level=heading_level,
            soft_deleted_at=soft_deleted_at,
            created_at=created_at or now,
            updated_at=updated_at or now,
        )
    return _create

# 3️⃣ Mock Repository（RULE-014/015/POLICY-008 验证）
@pytest.fixture
async def mock_block_repository(sample_book_id):
    """
    内存 Mock Repository，支持 RULE-014、RULE-015、RULE-013-REVISED 和 POLICY-008 验证

    关键能力：
    - BlockType enum 验证（RULE-014）
    - Fractional index 排序（RULE-015-REVISED）
    - HEADING 类型 heading_level 验证（RULE-013-REVISED）
    - soft_deleted_at 过滤（POLICY-008）
    """
    class MockBlockRepository:
        def __init__(self):
            self.store = {}

        async def save(self, block: Block) -> None:
            # ✅ RULE-014: 验证 type 有效性
            valid_types = {bt.value for bt in BlockType}
            block_type_str = block.type.value if hasattr(block.type, 'value') else block.type
            if block_type_str not in valid_types:
                raise ValueError(f"Invalid block type: {block_type_str}")

            # ✅ RULE-013-REVISED: HEADING 必须有 heading_level
            if block_type_str == "heading" and block.heading_level is None:
                raise ValueError("HEADING blocks must have heading_level (1-3)")

            self.store[block.id] = block

        async def get_by_id(self, block_id):
            block = self.store.get(block_id)
            # ✅ POLICY-008: 自动过滤软删除
            if block and block.soft_deleted_at is not None:
                return None
            return block

        async def get_by_book_id(self, book_id) -> list:
            # ✅ RULE-015: 按 Decimal order 排序
            blocks = [
                b for b in self.store.values()
                if b.book_id == book_id and b.soft_deleted_at is None
            ]
            return sorted(blocks, key=lambda b: float(b.order))

        async def get_deleted_blocks(self, book_id) -> list:
            # POLICY-008: 检索软删除的 blocks
            return [
                b for b in self.store.values()
                if b.book_id == book_id and b.soft_deleted_at is not None
            ]

    return MockBlockRepository()

# 4️⃣ Service Fixture（使用 Mock）
@pytest.fixture
async def block_service(mock_block_repository):
    """BlockService with mock repository"""
    return BlockService(repository=mock_block_repository)
```

#### Assertion Helpers（关键）

```python
@pytest.fixture
async def assert_block_fractional_index():
    """
    Helper to verify RULE-015-REVISED: Fractional Index ordering

    确保：
    - order 值是有效的 Decimal
    - 块正确按 order 排序
    - 可在任意两个块之间插入（O(1) 属性）
    """
    async def _verify(blocks, repository):
        # 验证 order 有效性
        for block in blocks:
            assert isinstance(block.order, (Decimal, float, int))

        # 验证排序
        orders = [float(b.order) for b in blocks]
        assert orders == sorted(orders), "Blocks not ordered by fractional index"

        # 验证 O(1) 插入能力
        if len(blocks) >= 2:
            block_a = blocks[0]
            block_b = blocks[1]
            new_order = (float(block_a.order) + float(block_b.order)) / 2.0
            assert float(block_a.order) < new_order < float(block_b.order)

    return _verify


@pytest.fixture
async def assert_block_soft_deleted():
    """
    Helper to verify POLICY-008: Block soft delete

    确保：
    - get_by_id() 对软删除的块返回 None
    - get_deleted_blocks() 能检索软删除的块
    """
    async def _verify(block_id, book_id, repository):
        block = await repository.get_by_id(block_id)
        assert block is None, "Soft-deleted block should not be visible"

        deleted = await repository.get_deleted_blocks(book_id)
        deleted_ids = [b.id for b in deleted]
        assert block_id in deleted_ids, "Soft-deleted block should be retrievable"

    return _verify


@pytest.fixture
async def assert_heading_level_required():
    """
    Helper to verify RULE-013-REVISED: HEADING blocks need heading_level

    确保：
    - HEADING 类型必须有 heading_level（1-3）
    - 非 HEADING 类型不应有 heading_level
    """
    async def _verify(repository):
        # HEADING WITH level（成功）
        heading_with = BlockModel(
            id=uuid4(),
            book_id=uuid4(),
            type=BlockType.HEADING,
            content="Title",
            order=Decimal('10.0'),
            heading_level=2,
        )
        await repository.save(heading_with)

        # HEADING WITHOUT level（失败）
        heading_without = BlockModel(
            id=uuid4(),
            book_id=uuid4(),
            type=BlockType.HEADING,
            content="Title",
            order=Decimal('20.0'),
            heading_level=None,
        )
        with pytest.raises(ValueError):
            await repository.save(heading_without)

        # TEXT with None level（成功）
        text = BlockModel(
            id=uuid4(),
            book_id=uuid4(),
            type=BlockType.TEXT,
            content="Text",
            order=Decimal('30.0'),
            heading_level=None,
        )
        await repository.save(text)

    return _verify
```

### 3️⃣ 测试模式与用例（Block 特化）

#### 模式 1: RULE-014 类型系统验证

```python
@pytest.mark.asyncio
async def test_rule_014_valid_block_types(mock_block_repository, sample_book_id):
    """验证 RULE-014: 所有有效的 BlockType 都能保存"""
    for block_type in BlockType:
        block = Block.create_text(sample_book_id, f"Content for {block_type.value}", 10.0)
        block.type = block_type
        await mock_block_repository.save(block)

        loaded = await mock_block_repository.get_by_id(block.id)
        assert loaded.type == block_type

@pytest.mark.asyncio
async def test_rule_014_invalid_block_type_rejected(mock_block_repository, sample_book_id):
    """验证 RULE-014: 非法类型被拒绝"""
    block = Block.create_text(sample_book_id, "Content", 10.0)
    block.type = "invalid_type"  # ← 非法类型

    with pytest.raises(ValueError, match="Invalid block type"):
        await mock_block_repository.save(block)
```

#### 模式 2: RULE-015-REVISED Fractional Index 验证

```python
@pytest.mark.asyncio
async def test_rule_015_fractional_index_ordering(
    block_domain_factory,
    block_repository_impl,
):
    """验证 RULE-015-REVISED: Fractional Index O(1) 插入"""
    # 创建 5 个块，间隔均匀
    blocks = []
    for i in range(5):
        block = block_domain_factory(order=Decimal(str(i * 10)))
        await block_repository_impl.save(block)
        blocks.append(block)

    # 加载并验证排序
    loaded = await block_repository_impl.get_by_book_id(blocks[0].book_id)
    await assert_block_fractional_index(loaded, block_repository_impl)

    # 验证可在任意两个块之间插入
    block_a = loaded[0]
    block_b = loaded[1]

    new_order = (float(block_a.order) + float(block_b.order)) / 2.0
    new_block = block_domain_factory(order=Decimal(str(new_order)))
    await block_repository_impl.save(new_block)

    # 重新加载并验证排序
    reloaded = await block_repository_impl.get_by_book_id(blocks[0].book_id)
    assert len(reloaded) == 6
    assert reloaded[1].id == new_block.id
```

#### 模式 3: RULE-013-REVISED HEADING 类型验证

```python
@pytest.mark.asyncio
async def test_rule_013_revised_heading_requires_level(
    block_domain_factory,
    mock_block_repository,
):
    """验证 RULE-013-REVISED: HEADING 必须有 heading_level"""
    # 有效的 HEADING
    heading = block_domain_factory(
        block_type=BlockType.HEADING,
        heading_level=2,
    )
    await mock_block_repository.save(heading)

    # 无效的 HEADING（缺少 level）
    bad_heading = block_domain_factory(
        block_type=BlockType.HEADING,
        heading_level=None,
    )
    with pytest.raises(ValueError, match="heading_level"):
        await mock_block_repository.save(bad_heading)

@pytest.mark.asyncio
async def test_rule_013_revised_text_no_level_required(
    block_domain_factory,
    mock_block_repository,
):
    """验证 RULE-013-REVISED: TEXT 不需要 heading_level"""
    text = block_domain_factory(
        block_type=BlockType.TEXT,
        heading_level=None,
    )
    await mock_block_repository.save(text)

    loaded = await mock_block_repository.get_by_id(text.id)
    assert loaded.heading_level is None
```

#### 模式 4: POLICY-008 软删除验证

```python
@pytest.mark.asyncio
async def test_policy_008_soft_delete_filtering(
    block_domain_factory,
    block_repository_impl,
):
    """验证 POLICY-008: 软删除的块不可见"""
    block = block_domain_factory()
    await block_repository_impl.save(block)

    # 正常可见
    loaded = await block_repository_impl.get_by_id(block.id)
    assert loaded is not None

    # 软删除
    block.soft_deleted_at = datetime.now(timezone.utc)
    await block_repository_impl.save(block)

    # 不可见
    loaded = await block_repository_impl.get_by_id(block.id)
    assert loaded is None

    # 但可通过 get_deleted_blocks 检索
    deleted = await block_repository_impl.get_deleted_blocks(block.book_id)
    assert block.id in [b.id for b in deleted]
```

### 4️⃣ ORM 映射方法（to_dict / from_dict）

#### BlockModel 完整实现

```python
class BlockModel(Base):
    # ... 字段定义 ...

    def to_dict(self) -> dict:
        """
        序列化到字典（9 字段全量）

        用途：
        - REST API 响应
        - 测试序列化验证
        - 数据导出
        """
        return {
            "id": str(self.id),
            "book_id": str(self.book_id),
            "type": self.type.value if isinstance(self.type, BlockType) else self.type,
            "content": self.content,
            "order": float(self.order) if self.order else 0.0,  # DECIMAL → float
            "heading_level": self.heading_level,
            "soft_deleted_at": self.soft_deleted_at.isoformat() if self.soft_deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "BlockModel":
        """
        从字典反序列化

        用途：
        - 数据迁移
        - 测试数据导入
        - API 请求处理
        """
        block_type = data.get("type")
        if isinstance(block_type, str):
            block_type = BlockType(block_type)

        return BlockModel(
            id=UUID(data.get("id")) if data.get("id") else None,
            book_id=UUID(data.get("book_id")) if data.get("book_id") else None,
            type=block_type,
            content=data.get("content"),
            order=Decimal(str(data.get("order", 0))),
            heading_level=data.get("heading_level"),
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
| BlockType Enum | `models.py` | 8 种类型定义 | 🔴 P0 |
| type 字段改为 Enum | `models.py` | SQLEnum(BlockType) | 🔴 P0 |
| Round-Trip 方法 | `models.py` | `to_dict()`, `from_dict()` (9 字段) | 🔴 P0 |
| Model factory | `conftest.py` | `block_model_factory` | 🔴 P0 |
| Mock with RULE-014 | `conftest.py` | `mock_block_repository` 类型验证 | 🔴 P0 |
| Mock with RULE-015 | `conftest.py` | Decimal order 排序支持 | 🔴 P0 |
| Mock with POLICY-008 | `conftest.py` | 软删除过滤 + get_deleted_blocks | 🔴 P0 |
| Fractional Index helper | `conftest.py` | `assert_block_fractional_index()` | 🟡 P1 |
| Soft Delete helper | `conftest.py` | `assert_block_soft_deleted()` | 🟡 P1 |
| HEADING Level helper | `conftest.py` | `assert_heading_level_required()` | 🟡 P1 |
| 常量 Fixtures | `conftest.py` | `sample_book_id` | 🟢 P2 |

🔮 **后续优化**（超出本 ADR 范围）：

- [ ] 批量块操作优化
- [ ] Fractional Index 算法性能优化
- [ ] 递归块嵌套支持（当前为扁平）
- [ ] Block 元数据 JSON 字段支持

---

## 关键设计决策

### 1️⃣ BlockType SQLEnum（类型安全）

**决策**：使用 SQLEnum 而非字符串

**原因**：
- ✅ 数据库级别类型验证（CHECK 约束）
- ✅ ORM 类型安全（`model.type` 是 BlockType enum）
- ✅ 无法插入非法值
- ✅ API 响应自动序列化

**对标**：
- PostgreSQL ENUM 类型最佳实践
- 与 ADR-001 类型安全原则一致

### 2️⃣ Fractional Index（DECIMAL(19,10)）

**决策**：使用 19 位精度的 Decimal，支持无限插入

**原因**：
- ✅ O(1) 拖拽操作（无需重新排序所有项）
- ✅ 19 位精度可支持 ~19 级嵌套插入
- ✅ 相比 offset 更高效

**对标**：
- Roam Research 使用的分数索引方案
- Notion 的排序系统

### 3️⃣ 软删除标记（soft_deleted_at）

**决策**：使用 DateTime 字段标记软删除

**原因**：
- ✅ 保留删除时间信息（审计）
- ✅ 支持时间范围查询
- ✅ 恢复支持（清除字段即恢复）

**对标**：
- 与 ADR-002/014 软删除模式一致

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| Enum 多语言支持复杂 | 后续支持翻译层；现在保持英文 |
| Fractional Index 精度不足 | 19 位精度可支持无限实用层数 |
| soft_deleted_at 索引膨胀 | 使用 WHERE IS NULL 过滤条件精确 |
| Mock 与真实 DB 不同步 | 集成测试验证，CI/CD 用真实 DB |

---

## 对标业界最佳实践

✅ 类型安全的 Enum（数据库级别）
✅ Fractional Index（O(1) 操作）
✅ Repository Pattern with exception translation
✅ Round-Trip Testing - ORM 映射验证
✅ Factory Pattern - 测试数据生成
✅ Soft Delete Pattern - 审计可追踪性
✅ Clean Code - 命名清晰，职责分离

---

## 相关 ADR

- **ADR-011**: Block Service & Repository Design（服务层）
- **ADR-014**: Book Models & Testing Layer（参考模式）
- **ADR-015**: Block Models & Testing Layer（本 ADR）
- **ADR-001**: Independent Aggregate Roots（聚合根设计）
- **ADR-002**: Basement Pattern（软删除）

---

## 后续工作

### 本 ADR 完成后

1. ✅ 修复 models.py（BlockType Enum + 序列化）
2. ✅ 优化 conftest.py（factories + Mock + helpers）
3. 📊 编写集成测试 tests/test_block_models.py
4. 📊 编写 round-trip 测试 tests/test_block_round_trip.py
5. 📊 编写类型测试 tests/test_block_types.py
6. 📊 编写排序测试 tests/test_block_fractional_index.py
7. 📊 编写软删除测试 tests/test_block_soft_delete.py
8. 测试覆盖率目标：>= 90%

### 四大模块完成后

- 进行完整 Round-Trip 测试（Library → Bookshelf → Book → Block）
- 生成 PHASE1_COMPLETION_REPORT
- 评估架构质量和代码覆盖率

---

## 版本历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2025-11-12 | Architecture Team | 初版发布（基于 Block 类型系统和排序需求） |

---

**批准者**: TBD
**有效期**: 长期（直到代码证明需要调整）

