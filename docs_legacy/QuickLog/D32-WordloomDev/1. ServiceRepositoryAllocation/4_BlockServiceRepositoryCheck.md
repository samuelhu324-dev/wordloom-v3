
1️⃣ 关于"重新计算顺序"的理解

🏆 稀疏排序 (Fractional Index)
```python
 # ✅ 改进的 Block.reorder_block()
async def reorder_block(
    self,
    block_id: UUID,
    new_order: float,  # ← 改为 FLOAT，支持小数
    user_id: UUID = None
) -> Block:
    """
    Reorder Block using Fractional Index strategy

    无需重新计算所有 Block，只更新当前 Block 的 order

    Example:
    - Block A: order = 1.0
    - Block B: order = 2.0
    - 拖拽 A 到 B 之间：Block A.order = 1.5 ✅

    Args:
        new_order: 新的 order 值（可以是小数）
    """
    block = await self.get_block(block_id)

    # Permission check
    if self.book_repository and user_id and self.library_repository:
        book = await self.book_repository.get_by_id(block.book_id)
        if not book:
            raise BookNotFoundError(f"Book {book.book_id} not found")
        library = await self.library_repository.get_by_id(book.library_id)
        if library and library.user_id != user_id:
            raise PermissionError(...)

    # 只更新当前 Block 的 order（O(1) 操作）
    block.set_order(new_order)
    await self.repository.save(block)

    logger.info(f"Block {block_id} reordered to {new_order}")
    return block


# ✅ 辅助方法：计算插入位置的 order
def calculate_fractional_order(
    before_order: Optional[float] = None,
    after_order: Optional[float] = None
) -> float:
    """
    计算两个 Block 之间的 order 值

    用于前端在 UI 中完成拖拽后计算新的 order
    """
    if before_order is None and after_order is None:
        return 1.0  # 第一个 Block

    if before_order is None:
        return after_order / 2  # 插在开头

    if after_order is None:
        return before_order + 1.0  # 插在末尾

    # 插在中间
    return (before_order + after_order) / 2


# 📝 前端流程示例：
# 1. 用户拖拽 Block A 到 Block B 和 C 之间
# 2. 前端计算：new_order = (B.order + C.order) / 2
# 3. 前端发送：PUT /blocks/{id}/reorder?order=2.5
# 4. 后端只做 UPDATE WHERE id = ? SET order = ?
# 5. 完成！无需重新计算其他 Block
```

2️⃣ 关于"标题是单独的 Block 类型"

┌─────────────────────────────────────────────────────────────────┐
│ 当前方案 vs 新方案对比                                           │
├─────────────────────────────────────────────────────────────────┤

【当前方案：每个 Block 可选标题】
├─ 数据结构：
│  {
│    id: uuid,
│    type: "TEXT",
│    content: "Lorem ipsum...",
│    title: "Chapter 1",        ← 可选
│    title_level: 1,            ← 可选
│  }
│
├─ 问题：
│  ❌ 每个 Block 都要处理 title 逻辑
│  ❌ UI 组件要判断 title 是否存在
│  ❌ 删除时要判断是否级联删除标题
│  ❌ type=IMAGE 时，title 字段意义不大
│  ❌ 难以扩展（如果以后标题要有样式呢？）
│
└─ 结果：复杂度分散在各个地方

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【新方案：标题作为独立 BlockType】
├─ 数据结构：
│  {
│    id: uuid,
│    book_id: uuid,
│    type: "HEADING",          ← 独立类型
│    content: "Chapter 1",
│    level: 1,                 ← 只有标题才有
│    order: 1.0,
│  }
│  {
│    id: uuid,
│    book_id: uuid,
│    type: "TEXT",
│    content: "Lorem ipsum...",
│    level: null,              ← TEXT 没有 level
│    order: 2.0,
│  }
│
├─ 优势：
│  ✅ 明确的语义：HEADING Block 就是标题
│  ✅ 简化逻辑：HEADING 和 TEXT 各自处理
│  ✅ UI 友好：前端直接根据 type 渲染不同组件
│  ✅ 易于扩展：HEADING 可以独立添加样式属性
│  ✅ 排序统一：所有 Block（包括 HEADING）都用同一个 order
│  ✅ 删除简单：删除 HEADING Block，下面的 TEXT 自动"升上来"
│
└─ 结果：职责清晰，易于维护


