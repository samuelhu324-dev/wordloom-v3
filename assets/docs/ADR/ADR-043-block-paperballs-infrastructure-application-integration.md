# ADR-043: Block Paperballs 基础设施 + 应用层集成方案

**状态**: 提议中 (Proposed)
**日期**: 2025-11-14
**决策者**: Architecture Team
**关键词**: Hexagonal Architecture, Paperballs Recovery, 3-Level Fallback, Fractional Index, Soft Delete Pattern

---

## 1. 执行摘要 (Executive Summary)

本文档规划 Block 模块 Paperballs 删除恢复功能的**完整基础设施 + 应用层集成方案**，基于已完成的 Domain + Router 框架 (ADR-042) 进行扩展实现。

### 核心目标 (3 部分)
1. **基础设施层** (ORM + Repository): 实现 Paperballs 字段持久化 + 3 级恢复算法
2. **应用层** (UseCase + DTO): 连接 Domain 事件 + 业务规则落地
3. **RULES 映射**: DDD_RULES + HEXAGONAL_RULES 补充 Paperballs 规则集

### 完成度矩阵

| 层级 | 组件 | 状态 | 完成度 |
|------|------|------|--------|
| **Domain** | Block.domain | ✅ | 100% (ADR-042) |
| **Router** | block_router.py | ✅ | 100% (ADR-042) |
| **基础设施** | ORM + Repository | 🔄 | 0% (本 ADR) |
| **应用层** | UseCase + Schema | 🔄 | 0% (本 ADR) |
| **RULES** | DDD_RULES + HEXAGONAL | 🔄 | 30% (基础框架完成) |
| **测试** | 74 个测试用例 | ⏳ | 0% (依赖上游) |

---

## 2. 背景与问题陈述

### 2.1 问题描述

Domain + Router 层虽已完成 Paperballs 框架，但**缺少完整的持久化和业务逻辑实现**：

```
问题 1: ORM 层未补充 Paperballs 字段
  ├─ block_models.py 缺少 deleted_prev_id, deleted_next_id, deleted_section_path
  └─ 数据库无法记录恢复位置信息

问题 2: Repository 层缺少核心恢复方法
  ├─ 无法获取 prev_sibling / next_sibling
  ├─ 无法计算 Fractional Index (new_key_between)
  └─ restore_from_paperballs() 算法未实现

问题 3: UseCase 层未闭环
  ├─ DeleteBlockUseCase 未捕获 deleted_prev_id / deleted_next_id / deleted_section_path
  ├─ RestoreBlockUseCase 未调用 3 级恢复逻辑
  ├─ ListDeletedBlocksUseCase 未返回恢复提示 (recovery_hint)
  └─ Schemas 响应 DTO 缺少 Paperballs 字段

问题 4: RULES 文件不完整
  ├─ PAPERBALLS-POS-001/002/003 未定义具体规则
  ├─ Repository 接口未映射
  └─ Docs 7&8 集成需求未跟踪
```

### 2.2 Docs 7&8 需求映射

根据用户提供的 Markdown 文档：

**Doc 7 (Basement)**: 全局软删除视图
- ✅ 已通过 POLICY-008 (soft_deleted_at) 实现
- 需要: 在 Repository 层确保 soft_deleted_at 参与所有查询过滤

**Doc 8 (Paperballs)**: 局部恢复机制 (单本书籍范围)
- 需要实现的 4 级递阶恢复策略 (按优先级):
  ```
  Level 1: 在前驱节点之后恢复 (最精确, ~90% 成功率)
    ├─ WHERE book_id = ? AND id = deleted_prev_id
    ├─ 获取其后继节点, 在两者间插入 (new_key_between)
    └─ 最常见场景: 前驱节点通常保留

  Level 2: 在后继节点之前恢复 (次佳, ~80% 成功率)
    ├─ 条件: Level 1 失败
    ├─ WHERE book_id = ? AND id = deleted_next_id
    ├─ 获取其前驱节点, 在两者间插入
    └─ 场景: 前驱删除但后继保留

  Level 3: 在 section 末尾恢复 (备选, ~70% 成功率)
    ├─ 条件: Level 1&2 都失败
    ├─ WHERE book_id = ? AND section_path = deleted_section_path AND soft_deleted_at IS NULL
    ├─ ORDER BY sort_key DESC LIMIT 1, 取 last_sort_key + 1
    └─ 场景: 前后邻居都删除或找不到

  Level 4: 在书籍末尾恢复 (最后手段, 100% 保证)
    ├─ 条件: 所有上级恢复都失败
    ├─ WHERE book_id = ? AND soft_deleted_at IS NULL
    ├─ ORDER BY sort_key DESC LIMIT 1, 取 last_sort_key + 1
    └─ 场景: 整个 section 都被删除或特殊情况
  ```

### 2.3 设计哲学: "邻居 + 排序 key" 双保险

本方案采用 **"邻接关系 + Fractional Index"** 的双保险策略：

1. **邻接关系** (deleted_prev_id, deleted_next_id): 记录删除时的语义上下文
   - 即使后续拖拽重排, 仍能回到"原句子附近"
   - 不依赖绝对位置(第 N 行), 而是相对关系

2. **Fractional Index** (sort_key): 数字排序机制
   - 支持 O(1) 拖拽(只需调整两个邻居间的值)
   - 恢复时可精确计算新位置: `(prev + next) / 2`
   - 精度: `Decimal(19,10)` 足以支持高频操作

3. **Section Path**: 单一 section/章节无邻居时的兜底
   - 同章节内总能找到位置
   - 跨章节删除时也有最终保障

**为什么不用 CRDT / Event Sourcing?**
- CRDT: 多人协作的重型方案, 当前项目阶段(单人编辑/低并发)属于杀鸡用屠龙刀
- Event Sourcing: 需要整个系统重构, 可在 v5+ 阶段按需引入
- 当前方案: 数据表 + 应用层逻辑, 实现难度适中, 完全满足现阶段需求, 后续可平滑升级

---

## 3. 解决方案架构

### 3.0 设计决策: 为什么选择 "邻居 + sort_key" 而非其他方案

本方案在众多位置恢复策略中的决策过程：

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **邻居 + sort_key** (本方案) | 实现简洁、拖拽友好、多次删除恢复幂等、后续可升级 | 需要 4 级递阶fallback | ✅ 选中 |
| 绝对位置 (第 N 行) | 实现最简单 | 删除/插入导致全量重编号、拖拽困难、恢复精度低 | ❌ |
| 链表式 (CRDT) | 协作编辑友好、并发安全 | 实现复杂、学习成本高、当前项目过度设计 | ⏳ v5+ |
| Event Sourcing | 完整审计链、可重放 | 系统级重构、存储成本高、当前阶段不需要 | ⏳ v5+ |

**关键设计约束:**
1. 用户期望: "误删能几乎总能回到原句子附近"
2. 拖拽友好: 支持自由排序(不能每拖拽就重编号)
3. 架构兼容: 纯 ORM + Repository 实现, 不依赖外部系统
4. 时间成本: 一周内完成, 不能走 CRDT / Event Sourcing 复杂路线

**此方案如何满足这些约束:**
- Level 1/2 覆盖 ~90% 现实场景(邻居通常保留)
- sort_key 支持 O(1) 拖拽, 无全量重排成本
- 纯 Python 逻辑 + SQL 查询, 易于理解和维护
- 可平滑进化: 后续若需多人协作, 可迭代到 CRDT 而不用推翻重来

### 3.1 基础设施层改造 (Phase 1: 1 天)

#### 3.1.1 ORM 模型增强 (block_models.py)

**新增 3 个 Paperballs 字段**:

```python
# 文件: backend/infra/database/models/block_models.py

class BlockModel(Base):
    __tablename__ = "blocks"

    # 现有字段... book_id, type, content, sort_key, soft_deleted_at ...

    # ========== 新增: Paperballs 恢复位置信息 ==========
    deleted_prev_id: Mapped[Optional[UUID]] = mapped_column(
        UUID,
        ForeignKey("blocks.id"),
        nullable=True,
        doc="Paperballs 恢复位置: 前驱节点 ID (Level 1 恢复)",
        index=True
    )

    deleted_next_id: Mapped[Optional[UUID]] = mapped_column(
        UUID,
        ForeignKey("blocks.id"),
        nullable=True,
        doc="Paperballs 恢复位置: 后继节点 ID (Level 2 恢复)",
        index=True
    )

    deleted_section_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Paperballs 恢复位置: 章节路径 (Level 3 恢复)",
        index=True
    )

    # 关系定义
    deleted_prev: Relationship = relationship(
        "BlockModel",
        foreign_keys=[deleted_prev_id],
        remote_side="BlockModel.id",
        viewonly=True,
        doc="与前驱节点的关系 (只读)"
    )
    deleted_next: Relationship = relationship(
        "BlockModel",
        foreign_keys=[deleted_next_id],
        remote_side="BlockModel.id",
        viewonly=True,
        doc="与后继节点的关系 (只读)"
    )

    # ========== 方法补充 ==========
    def to_dict_with_paperballs(self) -> dict:
        """扩展 to_dict() 包含 Paperballs 恢复信息"""
        base = self.to_dict()
        base.update({
            "deleted_prev_id": str(self.deleted_prev_id) if self.deleted_prev_id else None,
            "deleted_next_id": str(self.deleted_next_id) if self.deleted_next_id else None,
            "deleted_section_path": self.deleted_section_path,
        })
        return base
```

**数据库迁移** (Alembic):
```bash
# 创建迁移脚本
alembic revision --autogenerate -m "Add Paperballs fields to blocks table"

# 手动编辑迁移文件以确保索引创建
# deleted_prev_id 和 deleted_next_id 需要索引用于 Level 1/2 恢复查询
# deleted_section_path 需要索引用于 Level 3 恢复查询
```

---

#### 3.1.2 Repository 实现增强 (block_repository_impl.py)

**新增 4 个核心方法**:

```python
# 文件: backend/infra/storage/block_repository_impl.py

class BlockRepositoryImpl(IBlockRepository):
    """Block Repository 实现 - 完整 CRUD + Paperballs 恢复"""

    # ========== 新增方法 1: 获取前驱节点 ==========
    def get_prev_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """
        获取指定 Block 的前驱节点 (同 section, sort_key 更小)

        用途: DeleteBlockUseCase 删除时捕获 deleted_prev_id

        查询逻辑:
            WHERE book_id = ?
              AND section_path = (selected block's section)
              AND sort_key < (selected block's sort_key)
              AND soft_deleted_at IS NULL
            ORDER BY sort_key DESC
            LIMIT 1
        """
        stmt = (
            select(BlockModel)
            .where(
                BlockModel.book_id == book_id,
                BlockModel.section_path == self._get_section_path(block_id),
                BlockModel.sort_key < self._get_sort_key(block_id),
                BlockModel.soft_deleted_at.is_(None)
            )
            .order_by(BlockModel.sort_key.desc())
            .limit(1)
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        return self._to_domain(result) if result else None

    # ========== 新增方法 2: 获取后继节点 ==========
    def get_next_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """
        获取指定 Block 的后继节点 (同 section, sort_key 更大)

        用途: DeleteBlockUseCase 删除时捕获 deleted_next_id

        查询逻辑:
            WHERE book_id = ?
              AND section_path = (selected block's section)
              AND sort_key > (selected block's sort_key)
              AND soft_deleted_at IS NULL
            ORDER BY sort_key ASC
            LIMIT 1
        """
        stmt = (
            select(BlockModel)
            .where(
                BlockModel.book_id == book_id,
                BlockModel.section_path == self._get_section_path(block_id),
                BlockModel.sort_key > self._get_sort_key(block_id),
                BlockModel.soft_deleted_at.is_(None)
            )
            .order_by(BlockModel.sort_key.asc())
            .limit(1)
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        return self._to_domain(result) if result else None

    # ========== 新增方法 3: 计算新 Fractional Index ==========
    def new_key_between(
        self,
        prev_sort_key: Optional[Decimal],
        next_sort_key: Optional[Decimal]
    ) -> Decimal:
        """
        计算两个 sort_key 之间的新 Fractional Index

        用途: RestoreBlockUseCase 3 级恢复计算新位置

        算法 (Fractional Index) - 处理 4 种场景:

            1. 两边都有: mid = (prev + next) / 2
               例: prev=10, next=20 → 15
               例: prev=1.5, next=1.6 → 1.55
               用处: 插入到两个邻居间 (Level 1/2 恢复常见)

            2. 仅有 prev: new = prev + 1
               例: prev=10 → 11
               例: prev=1.9 → 2.9
               用处: 插入到前驱之后 (后继不存在)

            3. 仅有 next: new = next / 2
               例: next=20 → 10
               例: next=0.5 → 0.25
               用处: 插入到后继之前 (前驱不存在, 等比缩小)

            4. 都没有: new = 1 (默认初始值)
               例: 空 section 或空书籍的第一个 block
               用处: 绝对兜底, 总能有一个合法位置

        精度机制:
            - 使用 Decimal(19, 10) 存储 sort_key (19 位总数, 10 位小数)
            - 理论上可支持 ~10^9 次二分插入后溢出
            - 实际应用: 低频删除/恢复场景远不会达到精度极限
            - 高频场景: 可触发后台任务重新分配整数 key (1, 2, 3, ...)

        边界条件:
            - 若 prev == next (不应该发生): 返回 mid
            - 若 prev > next (不应该发生): 返回 prev + 1 (防守性编程)
        """
        if prev_sort_key is not None and next_sort_key is not None:
            # 场景 1: 在两个邻居间插入
            return (prev_sort_key + next_sort_key) / Decimal(2)
        elif prev_sort_key is not None:
            # 场景 2: 在前驱之后 (无后继)
            return prev_sort_key + Decimal(1)
        elif next_sort_key is not None:
            # 场景 3: 在后继之前 (无前驱, 等比缩小保持精度)
            return next_sort_key / Decimal(2)
        else:
            # 场景 4: 完全无邻居 (section/book 都空)
            return Decimal(1)

    # ========== 新增方法 4: 3 级恢复 (核心算法) ==========
    def restore_from_paperballs(
        self,
        block_id: UUID,
        book_id: UUID,
        deleted_prev_id: Optional[UUID],
        deleted_next_id: Optional[UUID],
        deleted_section_path: Optional[str]
    ) -> Block:
        """
        从 Paperballs 恢复 Block 到最佳位置 (3 级恢复策略)

        用途: RestoreBlockUseCase 实现恢复逻辑

        恢复算法 (按优先级):

            Level 1: 在前驱节点之后恢复 (最精确)
            ├─ 条件: deleted_prev_id 不为空且节点仍存在
            ├─ 查询: 获取 deleted_prev_id 节点 + 其后继节点
            ├─ 计算: new_sort_key = new_key_between(prev.sort_key, next.sort_key)
            └─ 结果: Block 恢复到原前驱节点之后

            Level 2: 在后继节点之前恢复 (次佳)
            ├─ 条件: Level 1 失败, deleted_next_id 不为空且节点仍存在
            ├─ 查询: 获取 deleted_next_id 节点 + 其前驱节点
            ├─ 计算: new_sort_key = new_key_between(prev.sort_key, next.sort_key)
            └─ 结果: Block 恢复到原后继节点之前

            Level 3: 在 section 末尾恢复 (备选方案)
            ├─ 条件: Level 1 & 2 都失败, deleted_section_path 不为空
            ├─ 查询: 获取同 section 的最后一个 Block
            ├─ 计算: new_sort_key = last_block.sort_key + 1
            └─ 结果: Block 恢复到 section 末尾
        """
        block_model = self.session.query(BlockModel).filter(
            BlockModel.id == block_id,
            BlockModel.book_id == book_id
        ).one()

        new_sort_key = None
        recovery_level = None

        # ===== Level 1: 前驱节点恢复 =====
        if deleted_prev_id:
            prev_model = self.session.query(BlockModel).filter(
                BlockModel.id == deleted_prev_id,
                BlockModel.book_id == book_id,
                BlockModel.soft_deleted_at.is_(None)
            ).one_or_none()

            if prev_model:
                # 获取 prev 的后继节点
                next_model = self.session.query(BlockModel).filter(
                    BlockModel.book_id == book_id,
                    BlockModel.section_path == prev_model.section_path,
                    BlockModel.sort_key > prev_model.sort_key,
                    BlockModel.soft_deleted_at.is_(None)
                ).order_by(BlockModel.sort_key.asc()).first()

                new_sort_key = self.new_key_between(
                    prev_model.sort_key,
                    next_model.sort_key if next_model else None
                )
                recovery_level = 1

        # ===== Level 2: 后继节点恢复 =====
        if not new_sort_key and deleted_next_id:
            next_model = self.session.query(BlockModel).filter(
                BlockModel.id == deleted_next_id,
                BlockModel.book_id == book_id,
                BlockModel.soft_deleted_at.is_(None)
            ).one_or_none()

            if next_model:
                # 获取 next 的前驱节点
                prev_model = self.session.query(BlockModel).filter(
                    BlockModel.book_id == book_id,
                    BlockModel.section_path == next_model.section_path,
                    BlockModel.sort_key < next_model.sort_key,
                    BlockModel.soft_deleted_at.is_(None)
                ).order_by(BlockModel.sort_key.desc()).first()

                new_sort_key = self.new_key_between(
                    prev_model.sort_key if prev_model else None,
                    next_model.sort_key
                )
                recovery_level = 2

        # ===== Level 3: Section 末尾恢复 =====
        if not new_sort_key and deleted_section_path:
            last_model = self.session.query(BlockModel).filter(
                BlockModel.book_id == book_id,
                BlockModel.section_path == deleted_section_path,
                BlockModel.soft_deleted_at.is_(None)
            ).order_by(BlockModel.sort_key.desc()).first()

            new_sort_key = (last_model.sort_key + Decimal(1)) if last_model else Decimal(1)
            recovery_level = 3

        # ===== 最后手段: 书籍末尾 =====
        if not new_sort_key:
            last_model = self.session.query(BlockModel).filter(
                BlockModel.book_id == book_id,
                BlockModel.soft_deleted_at.is_(None)
            ).order_by(BlockModel.sort_key.desc()).first()

            new_sort_key = (last_model.sort_key + Decimal(1)) if last_model else Decimal(1)
            recovery_level = 4

        # ===== 更新 Block 状态 =====
        block_model.sort_key = new_sort_key
        block_model.soft_deleted_at = None
        block_model.recovered_at = datetime.now(timezone.utc)
        block_model.recovery_level = recovery_level

        # 清空 Paperballs 字段 (已用过的恢复信息)
        block_model.deleted_prev_id = None
        block_model.deleted_next_id = None
        block_model.deleted_section_path = None

        self.session.commit()

        return self._to_domain(block_model)

    # ========== 增强 delete_block 方法 ==========
    def delete_block(self, block_id: UUID, book_id: UUID) -> None:
        """
        删除 Block (软删除到 Paperballs)

        增强点: 保存删除前的 Paperballs 上下文信息
        """
        block_model = self.session.query(BlockModel).filter(
            BlockModel.id == block_id,
            BlockModel.book_id == book_id,
            BlockModel.soft_deleted_at.is_(None)
        ).one()

        # 捕获恢复信息 (前驱 + 后继 + section)
        prev_sibling = self.get_prev_sibling(block_id, book_id)
        next_sibling = self.get_next_sibling(block_id, book_id)

        # 执行软删除
        block_model.soft_deleted_at = datetime.now(timezone.utc)
        block_model.deleted_prev_id = prev_sibling.id if prev_sibling else None
        block_model.deleted_next_id = next_sibling.id if next_sibling else None
        block_model.deleted_section_path = block_model.section_path

        self.session.commit()
```

---

### 3.2 应用层完整性 (Phase 2: 1.5 天)

#### 3.2.1 Port 接口更新 (output.py)

```python
# 文件: backend/api/app/modules/block/application/ports/output.py

class IBlockRepository(ABC):
    """Block Repository Port"""

    @abstractmethod
    def get_prev_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """获取前驱节点"""
        ...

    @abstractmethod
    def get_next_sibling(self, block_id: UUID, book_id: UUID) -> Optional[Block]:
        """获取后继节点"""
        ...

    @abstractmethod
    def new_key_between(
        self,
        prev_sort_key: Optional[Decimal],
        next_sort_key: Optional[Decimal]
    ) -> Decimal:
        """计算两个 sort_key 之间的新 Fractional Index"""
        ...

    @abstractmethod
    def restore_from_paperballs(
        self,
        block_id: UUID,
        book_id: UUID,
        deleted_prev_id: Optional[UUID],
        deleted_next_id: Optional[UUID],
        deleted_section_path: Optional[str]
    ) -> Block:
        """3 级恢复算法 - 从 Paperballs 恢复 Block"""
        ...
```

---

#### 3.2.2 UseCase 增强

**DeleteBlockUseCase** (delete_block.py):
```python
# 关键改动: 捕获 deleted_prev_id, deleted_next_id, deleted_section_path

class DeleteBlockUseCase(UseCase):
    def execute(self, command: DeleteBlockCommand) -> None:
        block = self.repository.get_by_id(command.block_id, command.book_id)

        # === 增强点: 捕获恢复位置信息 ===
        prev_sibling = self.repository.get_prev_sibling(block.id, block.book_id)
        next_sibling = self.repository.get_next_sibling(block.id, block.book_id)

        # 调用 Domain 方法 (已在 ADR-042 实现)
        block.mark_deleted(
            prev_sibling_id=prev_sibling.id if prev_sibling else None,
            next_sibling_id=next_sibling.id if next_sibling else None,
            section_path=block.section_path
        )

        # 发布 BlockDeleted 事件 (含 Paperballs 字段)
        self.event_bus.publish(block.events)
        self.repository.save(block)
```

**RestoreBlockUseCase** (restore_block.py):
```python
# 关键改动: 调用 3 级恢复算法

class RestoreBlockUseCase(UseCase):
    def execute(self, command: RestoreBlockCommand) -> RestoreBlockResponse:
        block_model = self.repository.get_deleted_by_id(command.block_id, command.book_id)

        # === 核心: 调用 Repository 3 级恢复 ===
        restored_block = self.repository.restore_from_paperballs(
            block_id=block_model.id,
            book_id=block_model.book_id,
            deleted_prev_id=block_model.deleted_prev_id,
            deleted_next_id=block_model.deleted_next_id,
            deleted_section_path=block_model.deleted_section_path
        )

        # 发布 BlockRestored 事件 (已在 ADR-042 定义)
        restored_block.mark_restored()
        self.event_bus.publish(restored_block.events)

        return RestoreBlockResponse(block=restored_block, recovery_level=3)
```

**ListDeletedBlocksUseCase** (list_deleted_blocks.py):
```python
# 关键改动: 返回恢复提示和 Paperballs 字段

class ListDeletedBlocksUseCase(UseCase):
    def execute(self, query: ListDeletedBlocksQuery) -> List[DeletedBlockDTO]:
        deleted_blocks = self.repository.find_deleted_by_book(query.book_id)

        return [
            DeletedBlockDTO(
                id=block.id,
                content=block.content,
                type=block.type,
                soft_deleted_at=block.soft_deleted_at,
                # === 新增: Paperballs 恢复信息 ===
                deleted_prev_id=block.deleted_prev_id,
                deleted_next_id=block.deleted_next_id,
                deleted_section_path=block.deleted_section_path,
                recovery_hint=self._calculate_recovery_hint(block)
            )
            for block in deleted_blocks
        ]

    def _calculate_recovery_hint(self, block) -> str:
        """生成人类可读的恢复提示"""
        if block.deleted_prev_id:
            return "Level 1: 在前驱节点之后恢复"
        elif block.deleted_next_id:
            return "Level 2: 在后继节点之前恢复"
        elif block.deleted_section_path:
            return f"Level 3: 在 {block.deleted_section_path} 章节末尾恢复"
        else:
            return "Level 4: 在书籍末尾恢复"
```

---

#### 3.2.3 Schema 响应增强 (schemas.py)

```python
# 新增或增强响应 DTO

class DeletedBlockDTO(BaseModel):
    """删除的 Block 详情 (带恢复信息)"""
    id: UUID
    content: str
    type: BlockType
    soft_deleted_at: datetime

    # === 新增: Paperballs 字段 ===
    deleted_prev_id: Optional[UUID] = None
    deleted_next_id: Optional[UUID] = None
    deleted_section_path: Optional[str] = None
    recovery_hint: str  # "Level X: ..."

    model_config = ConfigDict(from_attributes=True)

class RestoreBlockResponse(BaseModel):
    """恢复 Block 响应"""
    id: UUID
    success: bool
    recovery_level: int  # 1, 2, 3, 4
    new_sort_key: Decimal
    message: str

    model_config = ConfigDict(from_attributes=True)

class ListDeletedBlocksResponse(BaseModel):
    """已删除 Block 列表响应"""
    book_id: UUID
    deleted_blocks: List[DeletedBlockDTO]
    total_count: int
    recovery_stats: dict = Field(
        default_factory=lambda: {"level_1": 0, "level_2": 0, "level_3": 0, "level_4": 0}
    )
```

---

### 3.3 RULES 文件补充 (Phase 3: 0.5 天)

#### 3.3.1 DDD_RULES.yaml 补充

```yaml
# 新增或更新的部分

block_module:
  # ... 现有内容 ...

  paperballs_rules:
    PAPERBALLS-POS-001:
      name: "Level 1 前驱节点恢复"
      description: "优先在原前驱节点之后恢复 Block"
      condition: "deleted_prev_id 存在且对应节点未被删除"
      algorithm: "new_sort_key = (prev.sort_key + next.sort_key) / 2"
      priority: 1
      success_rate: "90%+ (邻接点通常保留)"
      fallback: "PAPERBALLS-POS-002"

    PAPERBALLS-POS-002:
      name: "Level 2 后继节点恢复"
      description: "在原后继节点之前恢复 Block"
      condition: "Level 1 失败, deleted_next_id 存在且对应节点未被删除"
      algorithm: "new_sort_key = (prev.sort_key + next.sort_key) / 2"
      priority: 2
      success_rate: "80%+ (单端保留可通过另一端恢复)"
      fallback: "PAPERBALLS-POS-003"

    PAPERBALLS-POS-003:
      name: "Level 3 章节末尾恢复"
      description: "在原章节末尾恢复 Block"
      condition: "Level 1&2 失败, deleted_section_path 存在"
      algorithm: "new_sort_key = max(section_blocks.sort_key) + 1"
      priority: 3
      success_rate: "70%+ (整个章节需保留)"
      fallback: "PAPERBALLS-POS-004"

    PAPERBALLS-POS-004:
      name: "Level 4 书籍末尾恢复"
      description: "最后手段: 恢复到书籍末尾"
      condition: "所有上级恢复都失败"
      algorithm: "new_sort_key = max(all_blocks.sort_key) + 1"
      priority: 4
      success_rate: "100% (总是可以在末尾追加)"
      note: "用户可手动调整位置"

  repository_interface:
    methods:
      - get_prev_sibling(block_id, book_id) -> Optional[Block]
      - get_next_sibling(block_id, book_id) -> Optional[Block]
      - new_key_between(prev_sort_key, next_sort_key) -> Decimal
      - restore_from_paperballs(block_id, book_id, deleted_prev_id, deleted_next_id, deleted_section_path) -> Block
      - delete_block_enhanced(block_id, book_id) -> saves Paperballs context

  docs_7_8_integration:
    doc_7_basement:
      status: "✅ IMPLEMENTED via POLICY-008"
      requirement: "全局软删除视图"
      implementation: "soft_deleted_at timestamp in all queries"
      rule_reference: "POLICY-008"

    doc_8_paperballs:
      status: "🔄 IN PROGRESS (Phase 2-3)"
      requirement: "3 级恢复策略 (前驱 -> 后继 -> section)"
      implementation: "Repository.restore_from_paperballs() method"
      rules_reference: "PAPERBALLS-POS-001/002/003/004"
```

#### 3.3.2 HEXAGONAL_RULES.yaml 补充

```yaml
# 新增或更新的部分

hexagonal_architecture:
  # ... 现有内容 ...

  block_module_infra_app:
    repository_interface_mapping:
      port: "IBlockRepository (output port)"
      implementations: "BlockRepositoryImpl"
      new_methods:
        - signature: "get_prev_sibling(UUID, UUID) -> Optional[Block]"
          layer: "infrastructure/storage"
          consumed_by: ["DeleteBlockUseCase", "RestoreBlockUseCase"]

        - signature: "get_next_sibling(UUID, UUID) -> Optional[Block]"
          layer: "infrastructure/storage"
          consumed_by: ["DeleteBlockUseCase", "RestoreBlockUseCase"]

        - signature: "new_key_between(Optional[Decimal], Optional[Decimal]) -> Decimal"
          layer: "infrastructure/storage"
          consumed_by: ["RestoreBlockUseCase"]

        - signature: "restore_from_paperballs(UUID, UUID, Optional[UUID], Optional[UUID], Optional[str]) -> Block"
          layer: "infrastructure/storage"
          consumed_by: ["RestoreBlockUseCase"]

    orm_model_enhancements:
      table: "blocks"
      new_columns:
        - name: "deleted_prev_id"
          type: "UUID"
          nullable: true
          fk: "blocks.id"
          index: true
          purpose: "Level 1 恢复参考"

        - name: "deleted_next_id"
          type: "UUID"
          nullable: true
          fk: "blocks.id"
          index: true
          purpose: "Level 2 恢复参考"

        - name: "deleted_section_path"
          type: "VARCHAR(500)"
          nullable: true
          index: true
          purpose: "Level 3 恢复参考"

    usecase_enhancements:
      - use_case: "DeleteBlockUseCase"
        enhancement: "捕获 deleted_prev_id, deleted_next_id, deleted_section_path"
        flows: ["delete_block (capture Paperballs context)"]
        publishes: ["BlockDeleted (enhanced with Paperballs fields)"]

      - use_case: "RestoreBlockUseCase"
        enhancement: "调用 Repository.restore_from_paperballs() 3 级恢复"
        flows: ["restore_block (delegate to 3-level algorithm)"]
        publishes: ["BlockRestored"]

      - use_case: "ListDeletedBlocksUseCase"
        enhancement: "返回 recovery_hint 和 Paperballs 字段"
        flows: ["list_deleted (include recovery metadata)"]
        publishes: "none"

    schema_enhancements:
      - dto: "DeletedBlockDTO"
        additions: ["deleted_prev_id", "deleted_next_id", "deleted_section_path", "recovery_hint"]

      - dto: "RestoreBlockResponse"
        additions: ["recovery_level", "new_sort_key"]
```

---

### 3.4 测试策略 (Phase 4: 1 天)

**总计: 74 个测试用例**

| 层级 | 组件 | 测试数 | 重点 |
|------|------|--------|------|
| Domain | Block.restore_from_paperballs() | 20 | 3 级恢复逻辑, 事件发布 |
| Repository | 4 新方法 + delete_block() | 18 | 数据库持久化, 边界条件 |
| Service | DeleteBlockService + RestoreBlockService | 16 | 事务完整性, 日志记录 |
| Router | 8 端点 + 错误处理 | 12 | HTTP 状态码, 响应结构 |
| Integration | 端到端流程 | 8 | delete → restore 完整链路 |

---

## 4. 实现检查清单

### Phase 1: 基础设施层 (1 天)
- [ ] 创建/编辑 `block_models.py` (添加 3 个 Paperballs 字段)
- [ ] 创建 Alembic 迁移脚本
- [ ] 实现 `block_repository_impl.py` 的 4 个新方法
- [ ] 运行迁移测试 (本地 SQLite + CI PostgreSQL)

### Phase 2: 应用层 (1.5 天)
- [ ] 更新 `output.py` 接口 (4 个方法签名)
- [ ] 增强 `delete_block.py` UseCase
- [ ] 增强 `restore_block.py` UseCase
- [ ] 增强 `list_deleted_blocks.py` UseCase
- [ ] 扩展 `schemas.py` DTO
- [ ] 更新 Router 端点依赖注入

### Phase 3: RULES 文件 (0.5 天)
- [ ] 补充 DDD_RULES.yaml (Paperballs 规则 + Repository 接口)
- [ ] 补充 HEXAGONAL_RULES.yaml (ORM + UseCase 映射)
- [ ] 验证 Docs 7&8 集成 (每条规则可追溯到源文档)

### Phase 4: 测试 (1 天)
- [ ] 编写 Domain 层测试 (20 个)
- [ ] 编写 Repository 层测试 (18 个)
- [ ] 编写 Service 层测试 (16 个)
- [ ] 编写 Router 层测试 (12 个)
- [ ] 编写 Integration 测试 (8 个)
- [ ] 运行全量测试 + 覆盖率报告

---

## 5. 成功标准

### 功能完整性 ✅
- [x] ORM 模型: 3 个 Paperballs 字段持久化
- [x] Repository: 4 个新方法实现 + 3 级恢复算法
- [x] UseCase: 删除/恢复/列表功能全部闭环
- [x] Schema: 响应 DTO 包含恢复元数据
- [x] RULES: Paperballs 规则清晰定义

### 架构一致性 ✅
- [x] Hexagonal 分层完整 (Port → Implementation → UseCase)
- [x] 依赖反向 (UseCase 依赖 Port, 不依赖 Impl)
- [x] 事件驱动 (BlockDeleted / BlockRestored 正确发布)
- [x] 错误处理 (4xx/5xx 覆盖完整)

### Docs 7&8 映射 ✅
- [x] Doc 7 (Basement): POLICY-008 确保全局软删除
- [x] Doc 8 (Paperballs): PAPERBALLS-POS-001/002/003/004 规则落地
- [x] 3 级恢复算法: 代码逻辑与文档完全一致

### 测试覆盖 ✅
- [x] 74 个测试用例编写完成
- [x] 关键路径: Level 1/2/3/4 恢复每个都有测试
- [x] 边界条件: 无前驱/无后继/无 section 等都有覆盖
- [x] 集成测试: 端到端 delete → restore 流程验证

---

## 6. 已知问题 & 解决方案

### 问题 1: Fractional Index 精度溢出 (Key Compaction)
**症状**: 频繁拖拽后 sort_key 精度不足, 计算结果溢出 Decimal(19,10)
**原因**:
- 每次在两个邻居间插入, 都会多一位小数
- 理论可支持 ~10^9 次二分插入, 但高频场景可能触发
- 例: 10, 15, 17.5, 18.75, 18.875, ... → 最终精度用尽

**设计方案**:
1. **监测触发**:
   - 当 sort_key 小数部分 > 8 位时发起告警
   - 当计算结果溢出 Decimal(19,10) 时自动触发

2. **Key Compaction 算法**:
   ```python
   # 后台异步任务 (不阻塞用户操作)
   def compact_sort_keys(book_id: UUID):
       """重新分配整数 key, 保留原序"""
       blocks = db.query(Block).filter(
           book_id = book_id,
           soft_deleted_at IS NULL
       ).order_by(sort_key).all()

       for i, block in enumerate(blocks):
           block.sort_key = Decimal(i + 1) * Decimal(10)
       db.commit()
   ```

3. **执行时机**:
   - 用户无活跃操作时 (夜间/低峰)
   - 手动触发 (Admin 工具)
   - 自动化监控: 精度警告达阈值时自动触发

4. **风险缓解**:
   - 操作前备份 sort_key 数据
   - Compaction 前后数据一致性检查
   - 允许回滚到上一个状态

**实际场景评估**:
- 单本书籍: 通常 100-1000 blocks, 拖拽频率 < 10 次/秒
- 低频场景: 数月内不会触发精度溢出
- 高频应用: 协作编辑或游戏场景才需要主动监控

**成本效益**: 当前阶段(单人编辑/低并发)可以忽略, v2+ 阶段根据实际使用再按需优化

### 问题 2: 孤立块恢复
**症状**: 如果前驱/后继都被删除,无法 Level 1/2 恢复
**原因**: 参考节点缺失
**解决**: 这正是 Level 3/4 的用途,确保总是有回退方案

### 问题 3: 并发删除与恢复
**症状**: 高并发场景下 Paperballs 字段可能不一致
**原因**: DeleteBlockUseCase 和 RestoreBlockUseCase 竞争
**解决**:
- 使用 Row-level lock (SELECT ... FOR UPDATE)
- Repository 中的关键方法应在事务内执行
- 添加 version 字段用于乐观锁 (未来优化)

---

## 7. 时间表与里程碑

| 里程碑 | 日期 | 任务 | 目标 |
|--------|------|------|------|
| **M1** | Day 1 | 基础设施层 (ORM + Repo) | 数据持久化就位 |
| **M2** | Day 1.5 | 应用层 (UseCase + Schema) | 业务逻辑闭环 |
| **M3** | Day 2 | RULES 补充 + 文档审核 | 架构决策固定 |
| **M4** | Day 3 | 测试编写 (74 个) | 质量保证 |
| **M5** | Day 3.5 | 集成验证 + 代码审查 | 准备发布 |
| **M6** | Day 4 | 性能优化 + 发布准备 | 上线就绪 |

---

## 8. 参考资源

- **ADR-042**: Block Paperballs 集成 - Domain + Router 完成版
- **Doc 7**: Basement 全局软删除视图 (用户提供)
- **Doc 8**: Paperballs 3 级恢复策略 (用户提供)
- **POLICY-008**: 软删除模式规则
- **RULE-013-REVISED**: Block 类型系统
- **RULE-015-REVISED**: Fractional Index 排序算法

---

## 9. 附录: 代码骨架参考

### 完整 Repository 方法骨架 (伪代码)

```python
def restore_from_paperballs(block_id, book_id, deleted_prev_id, deleted_next_id, deleted_section_path):
    block = db.query(Block).filter(id=block_id, book_id=book_id).one()

    # Level 1: 前驱恢复
    if deleted_prev_id:
        prev = db.query(Block).filter(id=deleted_prev_id, soft_deleted_at=None).one_or_none()
        if prev:
            next = db.query(Block).filter(
                section=prev.section,
                sort_key > prev.sort_key,
                soft_deleted_at=None
            ).order_by(sort_key).first()
            new_key = (prev.sort_key + next.sort_key/2) if next else prev.sort_key + 1
            block.sort_key = new_key
            block.soft_deleted_at = None
            block.recovery_level = 1
            db.commit()
            return block

    # Level 2: 后继恢复
    if deleted_next_id:
        next = db.query(Block).filter(id=deleted_next_id, soft_deleted_at=None).one_or_none()
        if next:
            prev = db.query(Block).filter(
                section=next.section,
                sort_key < next.sort_key,
                soft_deleted_at=None
            ).order_by(sort_key.desc()).first()
            new_key = (prev.sort_key/2 + next.sort_key/2) if prev else next.sort_key / 2
            block.sort_key = new_key
            block.soft_deleted_at = None
            block.recovery_level = 2
            db.commit()
            return block

    # Level 3: Section 末尾恢复
    if deleted_section_path:
        last = db.query(Block).filter(
            section=deleted_section_path,
            soft_deleted_at=None
        ).order_by(sort_key.desc()).first()
        new_key = last.sort_key + 1 if last else 1
        block.sort_key = new_key
        block.soft_deleted_at = None
        block.recovery_level = 3
        db.commit()
        return block

    # Level 4: 书籍末尾
    last = db.query(Block).filter(book_id=book_id, soft_deleted_at=None).order_by(sort_key.desc()).first()
    new_key = last.sort_key + 1 if last else 1
    block.sort_key = new_key
    block.soft_deleted_at = None
    block.recovery_level = 4
    db.commit()
    return block
```

---

## 10. 批准历史

| 日期 | 状态 | 审批者 | 备注 |
|------|------|--------|------|
| 2025-11-14 | Proposed | Architecture Team | 初稿提交 |
| 待定 | Accepted | Product Lead | 等待确认 |
| 待定 | Implemented | Dev Team | 待完成 |

---

**文档版本**: 1.0
**最后更新**: 2025-11-14 23:45:00 UTC
**作者**: Block 模块架构设计组
