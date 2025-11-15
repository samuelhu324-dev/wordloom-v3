# Wordloom Deletion & Recovery Design (Basement / Paperballs / Vault)

> Draft for refactor – to be aligned with DDD_RULES.yaml & HEXAGONAL_RULES.yaml

---

## 1. Overall Principles

- 不新增多余容器实体，优先用 **视图 (View) + 状态字段** 实现删除/恢复体验。
- 删除优先采用 **软删 (soft delete)**：
  - 保留原始实体（Library / Bookshelf / Book / Block / Asset）
  - 通过 `is_deleted` + `deleted_at` 标记状态
- 单独区分三个概念：
  - **Basement**：跨 Library 的全局“删除内容视图”
  - **Paperballs**：每本 Book 内的局部回收站（只管 Block）
  - **Vault**：用户文件/媒体的资产库（真正的文件“老家”）

---

## 2. Basement – Global Deleted Content View

### 2.1 概念定位

- Basement **不是新的 Library / Container**，而是一个 **视图 (Application Concept)**：
  - 展示所有 `is_deleted = True` 的 Library / Bookshelf / Book 等实体
  - 按一定规则分组（例如按 Bookshelf 分组）

```text
BasementView
  - Libraries (deleted)
  - Bookshelves (deleted or containing deleted books)
  - Books (deleted; bookshelf may exist or not)

2.2 数据与分组模型（示意）

Application 层可以返回类似结构：

class BasementShelfGroup(BaseModel):
    bookshelf_id: UUID | None
    bookshelf_name: str
    bookshelf_deleted: bool           # 书架本身是否 is_deleted
    books: list[BasementBookItem]     # 该书架下被删除的 Books

class BasementBookItem(BaseModel):
    book_id: UUID
    book_title: str
    deleted_at: datetime
    original_position: str            # 如 "Shelf A / Chapter 2 / #5"

UI 展示建议：

bookshelf_deleted == True

视为 “已删除书架”：正常颜色 + tag Deleted Shelf

bookshelf_deleted == False 且 books 非空

视为 “仍存在、但有被删图书的书架”：半透明/灰色 + tag Has Deleted Books

找不到原始 bookshelf（硬删或迁移异常）

按分组 [Books with missing bookshelf] 展示（bookshelf_id = None）

2.3 恢复规则（关键用例）

恢复 Book（原 Bookshelf 存在且未删除）

Book.is_deleted = False

恢复到其 original_bookshelf_id

UI 提示：“已恢复到 {bookshelf_name}”

恢复 Book（原 Bookshelf 已删除但 Library 仍存在）

强制用户选择新的 Bookshelf 或 自动创建：

新建 bookshelf（如 Recovered from Basement (YYYY-MM-DD)）

将 Book 放入该 bookshelf

记录迁移情况（便于以后审计）

恢复 Book（原 Library 已删除或归档）

禁止直接恢复 Book

需先恢复 Library（以及 Bookshelf），否则不允许操作

UI 提示：“无法恢复：所属 Library 已删除，请先恢复 Library。”

恢复 Bookshelf

若其 Library 存在且未删除：

Bookshelf.is_deleted = False

可选择是否同步恢复其下所有 Book.is_deleted（策略可配置）

若 Library 已删除：

要求先恢复 Library 后才能恢复 Bookshelf

2.4 规则摘要（可放入 DDD_RULES.yaml）

basement:
  concepts:
    - name: BasementView
      type: ApplicationConcept
      description: "统一查看所有 is_deleted=true 的 Libraries / Bookshelves / Books 的视图，不是新的容器。"

  invariants:
    - id: BASEMENT-001
      text: "任何子级实体（Book, Bookshelf）恢复时，其父级实体必须处于非删除状态。"
    - id: BASEMENT-002
      text: "Basement 仅展示软删状态的实体，不改变实体的原始归属关系（library_id / bookshelf_id）。"
    - id: BASEMENT-003
      text: "无法单独恢复没有有效父级（library 或 bookshelf）的子实体。"

3. Paperballs – Per-Book Local Trash for Blocks
3.1 概念定位

Paperballs = 每本 Book 内部的局部回收站视图，专门展示该 Book 中被删除的 Blocks。

范围：只在 某一本 Book 内 生效

目的：容错用户“写作时误删 Block”的高频事故

非新容器：Block 仍然属于同一本 Book，只是状态变为“已删除”

3.2 Block 字段设计（示例）
Block
- id
- book_id
- content
- position_index          # 正文排序位置（已有）
- is_deleted: bool        # 是否进入 Paperballs
- deleted_at: datetime    # 删除时间
- previous_position: int  # 删除前的位置快照（可选 JSON / richer info）


3.3 删除 Block 行为

UseCase：DeleteBlock(block_id)：

block.is_deleted = True

block.deleted_at = now()

block.previous_position = current position_index

从 Book 的“活跃 Block 列表”中排除（正文不再展示）

触发 BlockDeleted 领域事件（用于日志、统计等）

注意：book_id 不变，Block 并没有“被搬到某个容器”，
Paperballs 是 Book 内部对 is_deleted=True blocks 的视图。

3.4 Paperballs 视图

UseCase：BrowsePaperballs(book_id)

查询：blocks WHERE book_id = :id AND is_deleted = TRUE

排序：ORDER BY deleted_at DESC

返回字段包括：

简要预览（content 片段 / 缩略信息）

deleted_at

previous_position 描述（如“第二章，第 5 段”）

3.5 恢复 Block 行为

UseCase：RestoreBlockFromPaperballs(block_id)：

确认 Book 存在且未删除/未归档

block.is_deleted = False

恢复位置：

优先尝试将 position_index 恢复为 previous_position

若该位置已被占用：

采用排序策略（gap / float sort_key），将其插入临近位置

或退而求其次：放在章节末尾 / Book 末尾，并提示“位置已近似恢复”

触发 BlockRestored 领域事件

3.6 规则摘要
paperballs:
  concepts:
    - name: PaperballsView
      type: ApplicationConcept
      description: "Book 内部的局部回收站，用于查看和恢复被标记为 is_deleted=true 的 Blocks。"

  invariants:
    - id: PAPERBALLS-001
      text: "删除 Block 不改变其 book_id，仅将其标记为 is_deleted 并记录删除前的位置。"
    - id: PAPERBALLS-002
      text: "从 Paperballs 恢复 Block 时，应尽量恢复到原位置；若无法精确恢复，则插入临近位置并保证书籍结构合法。"
    - id: PAPERBALLS-003
      text: "Paperballs 不引入新的 Book 容器类型，仅作为 Block 集合的视图。"

4. Vault – User Asset Repository (Images / PDFs / Files)

Vault 目前可以“先设计思路、后实现”，不急于上线。

4.1 概念定位

Vault = 用户所有上传文件的资产库，是真正的“文件老家”：

图片 / PDF / 文档 / 音频 / 视频等

Block / Book / 其它实体 只保存 Asset 的引用（asset_id），而不是文件路径本身

与 Trash / Basement / Paperballs 的关系：

Trash / Basement / Paperballs 管的是“引用关系和实体状态”

Vault 管的是“文件本体”及其生命周期

4.2 Asset 模型示例

class Asset(BaseModel):
    id: UUID
    owner_id: UUID
    kind: Literal["image", "pdf", "doc", "audio", "video", "other"]
    path: str            # 存储路径或 URL
    filename: str
    size: int
    created_at: datetime
    # 可扩展: tags, source_url, checksum, etc.

4.3 删除/恢复规则（建议方向）

从 Block 中删除图片/附件：

仅删除引用（Block ↔ Asset 的关联）

Asset 本体仍存在于 Vault 中

用户可在 Vault 里重新插入该 Asset 到任意 Block

从 Vault 中删除 Asset：

视为真正删除

可选择是否有 Vault 自己的二级 Trash（例如 7 天可恢复）

对用户来说：

“在内容里删图片” = 删除可见内容

“在 Vault 里删文件” = 真正抛弃资产

4.4 规则摘要
vault:
  concepts:
    - name: Asset
      type: Aggregate
      description: "用户上传的所有文件的统一资产模型，Block 仅持有其引用。"

  invariants:
    - id: VAULT-001
      text: "Block 删除附件只会删除 Asset 引用，不会自动删除 Asset 本体。"
    - id: VAULT-002
      text: "真正删除 Asset 必须在 Vault 维度进行，可选择是否引入 Vault 层的回收机制。"

5. 三者关系总结

Vault：

负责“文件本体”的生命周期（上传 / 保留 / 真删除）；

与具体 Library / Book / Block 的结构解耦。

Paperballs（per Book）：

负责“写作时误删 Block 的局部容错”；

范围局限于单本 Book，直接作用于 Block 状态和位置。

Basement（global view）：

负责统一查看/处理被软删的 Library / Bookshelf / Book（以及未来的其它实体）；

是跨 Library 的全局视图，不引入新容器，仅基于原始实体上的删除标记。

整体目标：

对用户：

写作时误删 Block 有就地安全网（Paperballs）；

删除整本书/书架有全局回收视图（Basement）；

上传的文件有可浏览、可重用的仓库（Vault）。

对开发与维护：

Domain 模型保持干净：只扩展字段和状态，不乱加新容器类型；

Paperballs / Basement / Vault 都以 UseCase + View 的形式实现，方便迭代与测试。
