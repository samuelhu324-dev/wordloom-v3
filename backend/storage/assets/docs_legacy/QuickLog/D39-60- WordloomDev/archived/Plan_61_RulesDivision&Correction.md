Plan: 三 RULES 修订与 Book/Block 边界梳理
下面是基于你当前 UI（截图 1–5）以及三份 RULES 的“规划版”方案，不动代码，只给出规则层面的完整改造建议和后续编辑路线。

Steps
明确 Book / Block / Chronicle 三者的职责边界与当前文档中的偏差。
给出一份领域→应用→UI 的 Book vs Block 边界矩阵，作为后续修文的“总参考线”。
分别为 DDD_RULES.yaml、HEXAGONAL_RULES.yaml、VISUAL_RULES.yaml 列出需要新增、删除、改写的 key 和段落。
单独点出 /admin/books/[bookId] Tab 工作台与旧 /admin/blocks、旧 BlockEditor overlay 的关系与清理策略。
汇总成一个“中文修缮路线图”，你或后续 agent 可以直接按此逐条修改文件。
一、先澄清：现在的“正式结构”与目标形态
结合截图 + 规则文件，你现在的正式产品结构可以理解为：

Library 层
/admin/libraries：Library 卡片列表（Pinned + All）。
/admin/libraries/[libraryId]：Library Detail + Bookshelf Dashboard（紧凑列表 + 审计对话框 + inline 创建）。
Bookshelf 层
/admin/bookshelves/[bookshelfId]：Bookshelf Detail + BookMainWidget（按成熟度分区的书籍列表 + 横向预览卡片）。
Book 层
/admin/books/[bookId]：唯一 Book 工作区：
顶部 hero 卡：标题、摘要、库·书橱链路、成熟度 & 状态 pill、简单指标。
下方三 Tab：概览 / 块编辑 / 时间线。
Block 层
已经内嵌在 Book 页的“块编辑” Tab 中，使用 InlineCreateBar + BlockList + BlockEditor（行内）+ DeletedBlocksPanel。
旧 /admin/blocks 仍存在，但应视作“调试/遗留”而不是主业务入口。
行业/DDD 视角看，这个结构非常合理：Library/Bookshelf 保持列表与分段概览，Book 专注于单本书的上下文与历史，Block 只作为内容的最小单元，Chronicle 提供跨聚合时间线。

接下来要做的事情主要是：让三份 RULES 完全“说同一种话”，并清理掉所有把 /admin/books/[bookId] 当成“Block 详情页”、或把 /admin/blocks 当主场的旧描述。

二、Book / Block / Chronicle 边界矩阵（总纲）
你后面修文可以把这张“矩阵”拆成 YAML 条目，本质是一个统一基线。

1. Domain 层

Book 可以做

持有：id, bookshelf_id, library_id, title, summary, status, maturity, block_count, 时间戳等。
行为：创建、重命名、更新简介；成熟度迁移（SEED→GROWING→STABLE→LEGACY→STABLE）、归档/删除/恢复；在库内移动书橱。
参与 Basement：软删除 / 恢复（但不保存 Basement 的 UI 状态）。
Book 不能做

不存 Block 正文、富文本结构、编辑状态。
不感知“Tab”“概览卡片布局”等 UI 概念。
不直接操作 Chronicle 或 Media（这些通过事件或 UseCase 间接发生）。
Block 可以做

保存：id, book_id, order, type, content, meta, soft_deleted_at 等。
行为：按类型创建；更新内容/元数据；重排（接收新 order，不负责算法）；删除/恢复。
Block 不能做

不改变 Book 的成熟度、状态、书橱；不能创建 Book。
不记录时间线（Chronicle 记录），不操作 Media 文件本身。
不感知 UI（编辑器行内/overlay）和页面路由。
Chronicle 可以做

记录来自 Book/Block 领域事件的审计日志（轻 payload）。
提供按 Book（未来可扩展 Bookshelf/Library）分页查询时间线。
Chronicle 不能做

不回写 Book/Block 状态，不参与业务决策。
不承载全文快照，只保存引用 ID 与少量上下文。
2. Application 层

Book UseCases
ListBooksUseCase（分页 + 过滤）、GetBookUseCase、CreateBookUseCase、UpdateBookUseCase（含成熟度）、Delete/Restore。
可更新 block_count 等聚合统计（基于 Block 仓储读数），但不直接编辑 Block。
Block UseCases
ListBlocksUseCase(book_id, page, size, include_deleted)。
Create/Update/Delete/Restore/Reorder 针对单本 Book 下的块。
Chronicle Services
Recorder：从 EventBus 接收 Book/Block 事件写入表。
Query：按 book_id + 过滤条件分页查询。
3. UI / Adapter 层

/admin/bookshelves/[bookshelfId]：
可以：渲染按成熟度分组的 Book 列表（BookMainWidget）。
不可以：在这里直接编辑 Block；点击 Book 后跳到 /admin/books/[bookId]。
/admin/books/[bookId]：
可以：用三个 Tab 提供概览 / 块编辑 / 时间线视图；所有数据来自现有 hooks。
不可以：再嵌套“Books 列表”或跨书橱“全局块列表”。
/admin/blocks：
只保留作为“运维/调试工具路由”（如果你还需要），不允许在 RULES 中被定位为主工作区。
三、逐文件修缮建议
1. DDD_RULES.yaml 修缮计划
(1) 顶部 POLICIES_ADDED_NOV26

保留已存在的：
POLICY-BOOKSHELF-AUDIT-DIALOG-DESCRIPTION
POLICY-BOOKSHELF-INLINE-CREATION-SHARED-FORM
完善 POLICY-BOOK-WORKSPACE-TABS（现在只是简要几行）：
建议补充 4–6 条子规则：
/admin/books/{bookId} 是唯一 Book 工作区，包含「概览/块编辑/时间线」三个视图。
所有 Block CRUD 必须通过 Block UseCase；禁止在 Book UseCase 里直接操作 BlockRepository。
Tab 选中状态只允许存 localStorage，不允许存进 Domain / DB。
概览的统计只使用 Book / Chronicle DTO 提供的字段，不臆造字段回写后端。
旧 /admin/blocks 如继续存在，明确为 “Admin 工具页”，不参与常规用户流程。
(2) Domain 3: Book 一节（现在几乎空白）

建议新增小块：

POLICY-BOOK-CONTENT-RESPONSIBILITY：
强调 Book 只保存元信息，不保存 Block 文本；
summary 是简短摘要，正文永远在 Block。
RULE-BOOK-REQUIRES-BOOKSHELF：
创建 Book 时必须指明 bookshelf_id（遵守独立聚合但有 FK 约束）。
更新 UI-FLOW-001 中 Book 部分：
明确“点击 Bookshelf 列表中的 Book 卡片 → 跳转至 /admin/books/{bookId} 工作区”。
(3) Domain 4: Block 一节

新增 / 强化三条：

RULE-BLOCK-REQUIRES-BOOK：
Block 创建时必须传入 book_id，禁止孤立 Block；
Repository 不提供“无 book_id 全表列表端点”给业务使用，仅 admin/debug 可用。
POLICY-BLOCK-CONTENT-FORMAT：
content 可以是纯文本或 JSON 字符串；
Domain 不解析 Markdown/表格等，只检查长度/类型。
POLICY-BLOCK-PAPERBALLS：
简要说明删除/恢复字段属于删除恢复框架，不涉及 UI 编辑职责（目前是散落在 deletion_recovery_framework 中，可加交叉引用）。
(4) Chronicle 段落

在 POLICY-CHRONICLE-TIMELINE 内补充两个子块：

EVENT-SOURCE-BOOK：
列出 Book 相关会写入 Chronicle 的事件：Created, Moved, MovedToBasement, Restored, Deleted, Opened。
EVENT-SOURCE-BLOCK：
建议至少列出：Created / ContentChanged / Reordered / Deleted / Restored；
声明 payload 仅包含 book_id, block_id, 简短 summary，不复制正文。
增加一行：
“Book 详情页与 /admin/chronicle 只通过 Chronicle API 获取事件，不从 Book/Block DTO 重建时间线。”
(5) Basement / 删除恢复

在 deletion_recovery_framework 描述末尾加一条：

Basement UI 只支持“查看/恢复/永久删除”，不允许直接编辑 Book/Block 内容；
对应 VISUAL_RULES 中 Basement 卡片说明。
2. HEXAGONAL_RULES.yaml 修缮计划
(1) theme_runtime_strategy 下的 dashboard / bookshelf 相关不用动，这部分已对齐。

(2) book_workspace_tabs_integration（你已新增）

建议再小幅调整使其更“端口化”：

inbound_ports 中把 Blocks 端点改成扁平风格：
从：GET /api/v1/books/{id}/blocks?...
改为：GET /api/v1/blocks?book_id={id}&page=&page_size=（保持与 “扁平端点 + 独立聚合根” 一致）。
constraints 部分加两条：
“Blocks 主编辑 UI 不再推荐绑定 /admin/blocks 路由；如存在，仅作为 admin 工具页。”
“Chronicle Tab 只使用 ChronicleQueryService，不允许直接从 Book/Block Repository 读取历史变更用于时间线。”
(3) Block Editor 相关

在 block_editor_inline_decisions 下添加子 key：

supersedes:
指向旧 overlay 策略名，status: deprecated。
book_workspace_alignment:
明确 BlockEditor 不再拥有独立主路由，而是由 /admin/books/{bookId} 的 Blocks Tab 宿主；
所有端口（Create/Update/Delete/Reorder）都以 book_id 为必传参数。
(4) Chronicle 策略

在 chronicle_timeline_strategy 里加上：

event_mapping：
用 bullet list 写明 Book / Block 事件到 ChronicleEventType 的映射；
book_detail_integration：
指出 /admin/books/{bookId} 时间线 Tab 的 hook 合约：useChronicleTimeline；
指出 Book 页不负责写 Chronicle，只有在 Book 打开时调用 POST /chronicle/books/{id}/opened（如果你确实有该端点）。
(5) Blocks Repository / 端点规则

在 hexagonal 的“端口规范”部分（convention 里已有 CONVENTION-RESPONSES-001 和 “不嵌套路由”）：

补一个示例：
RULE-FLAT-ENDPOINTS-BOOK-BLOCKS：
/books 与 /blocks 为两个独立资源；
GET /blocks?book_id= 是 Blocks 列表推荐形式；
禁止设计 /books/{id}/blocks 这样的 REST 栈式路径。
3. VISUAL_RULES.yaml 修缮计划
(1) book_maturity_visual_rules

在 exclusions 里把旧描述：

由：“/admin/books/[bookId]（Block 详情页仅展示单本书信息…”）
改为：“/admin/books/[bookId]（Book 详情工作区：展示单本书的成熟度徽章和简单统计，不渲染成熟度分区列表）”。
(2) chronicle_timeline_visual_rules

在 hook_contract 下面增加一行：

“Book 详情页的时间线 Tab 必须复用此 hook，不得单独拼装其他端点返回值。”
在 card_layout 下再补一条：

“Block 事件（如 BlockDeleted）只显示简要 payload，例如 ‘删除块 #3’；不展示块完整内容。”
(3) book_workspace_tabs_visual_rules（你已补充，但可以再稍微加强）

建议补三块内容：

数据源约束

清楚写出：
概览 Tab 只用 Book DTO 字段 + 可能的 latest_event_at 之类聚合指标；
块编辑 Tab 只来源 usePaginatedBlocksPhase0；
时间线 Tab 只来源 useChronicleTimeline。
加一条：
“禁止在 UI 中写兼容逻辑：例如用 Blocks 列表推导 block_count 并写入 Book 对象。”
无 /admin/blocks 主路由

在说明块编辑 Tab 时加一句：
“这是用户进行 Block 编辑的主工作视图；导航栏不再暴露 /admin/blocks 入口。”
可访问性和交互

明确：
TabList 使用 role="tablist"，按钮 role="tab" + aria-selected；
InfoPanel 使用 <dl>，字段名/值对应；
切换 Tab 时不重置到页首（避免频繁滚动）。
(4) Bookshelf / Library 视图里关于 Chronicle 的内容

在 bookshelf_compact_list_view / bookshelf_dashboard_layout_v2 中：

对“最近活动时间”“health”这类字段，补一条说明：
“这些值来自 Dashboard DTO，前端不需要单独调 Chronicle；Chronicle 保留给 Book 详情和 /admin/chronicle。”
(5) /admin/blocks 相关条目

搜索 VISUAL_RULES 文件中所有 /admin/blocks / “BlockEditor overlay” 文字：
若是主流程描述：改为说明“已废弃 / 仅用于调试”；
若纯历史记录：标记为 “status: deprecated”。
四、三 RULES 的“中文修缮路线图”
你可以按下面顺序实操修文（建议开一个专门分支）：

第一轮：顶层政策对齐

在 DDD_RULES.yaml 中把 POLICY-BOOK-WORKSPACE-TABS 写全；
在 HEXAGONAL_RULES.yaml 完成 book_workspace_tabs_integration 的端点 & 约束补充；
在 VISUAL_RULES.yaml 里将 book_workspace_tabs_visual_rules 扩写为完整 UI 规范。
第二轮：Book / Block / Chronicle 边界补条款

DDD：补 POLICY-BOOK-CONTENT-RESPONSIBILITY、RULE-BLOCK-REQUIRES-BOOK、Chronicle 的事件映射部分；
HEXAGONAL：增加 Blocks 扁平端点示例和 Chronicle event mapping；
VISUAL：强化 book_maturity_visual_rules 和 chronicle_timeline_visual_rules 的 scope / exclusions。
第三轮：清理遗留 / 标记废弃

三文件统一搜索：
“BlockEditor overlay” / /admin/blocks / “Block Detail page” 等旧名词；
对每一处：
不是必须保留的直接删；
必须保留作历史说明的，标 status: deprecated 并指向 ADR-081、ADR-099。
第四轮：增加交叉引用

在 DDD 中 Book / Block / Chronicle 段落末尾添加 synced_with 字段：
例如：synced_with: [HEXAGONAL_RULES.book_workspace_tabs_integration, VISUAL_RULES.book_workspace_tabs_visual_rules]；
便于未来你查到“修改某一个地方要记得同步哪里”。
第五轮：整理 ADR

你已经有 ADR-099-book-detail-workspace-tabs-integration；
建议在 100 号左右再补一个 “Book–Block–Chronicle Boundaries and Timeline Policy”：
把本回答中的矩阵和分工提纯成正式 ADR；
三 RULES 中相关段落 adr_reference 指向它。
如果你希望，我可以在下一步直接给出每个文件具体 key 的“目标版提纲 YAML”（不是长篇正文，只是结构 + 一句话描述），你或实现 agent 按这个骨架填充即可。