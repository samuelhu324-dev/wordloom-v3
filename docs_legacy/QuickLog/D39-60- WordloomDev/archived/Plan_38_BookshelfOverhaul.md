你现在的目标

目标页面：LibraryLog 详情里的「书橱列表」页（Bookshelves 页面），也就是截图 2 那个地方。
参考方案：你已有的 Plan21 + Plan13 两份设计方案。
约束与文档：
需要和 HEXAGONAL_RULES.yaml、VISUAL_RULES.yaml、DDD_RULES.yaml 三份规则文件对齐并更新。
这次是一次「大改版」，最终要形成新的 ADR：ADR-091-xxx.md（路径在截图 3 的 ADR 目录里）。
你现在希望先有一份详细、结构化、可靠的中文实施计划，后面再切换到 agent 模式，让我按这个计划自动改代码。
下面是一份可以直接拿来 review / 修改的计划草案，我按「阶段→步骤」来写，方便你裁剪。

一、范围与定位
页面边界

前端工程：frontend
目标页面：
page.tsx
对应内部 Bookshelf 区域使用的组件（预计在 features/bookshelf / widgets 层）
不改动：
后端 API 语义（除非 Plan13/21 明确要求）。
其他 domain（Book / Block）仅在必要的 UI 展示层轻触。
设计输入

Plan21：Library Overview / Bookshelves 网格布局 + 排序过滤方案。
Plan13：旧版 bookshelf UI 交互要素（如卡片信息结构、操作按钮）。
VISUAL_RULES：视觉风格（色板、间距、卡片尺寸、字体）。
HEXAGONAL_RULES / DDD_RULES：保证不破坏六边形架构与聚合边界。
二、信息梳理阶段（只读，不改代码）
梳理现有 Bookshelf 页面结构

找出：
LibraryLog 详情页：page.tsx
此页内部引用的 Bookshelf 列表组件（例如 BookshelfListWidget / BookshelfMainWidget 等）。
记录：
当前 UI 切换（grid/list）、排序、过滤、分页逻辑在什么组件实现。
当前卡片组件路径（如 features/bookshelf/ui/BookshelfCard.tsx、widgets/bookshelf/* 等）。
阅读 Plan21 / Plan13 关键内容

对照截图 2，整理出目标页面需要具备的模块：
顶部导航：Library 标题区 + 描述（已存在，确认复用）。
控制条：视图切换、排序、过滤、创建 Button。
Bookshelf 卡片区：Pinned 区 + 其他区，支持 grid/list 两种布局（若 Plan21 要求）。
把 Plan21/13 中「必须实现的要点」列出来（如：Pinned 段落、归档过滤、卡片信息字段、悬停操作等）。
阅读三份 RULES 中与 Library/Bookshelf/UI 相关的条目

DDD_RULES.yaml
RULE-LIB-LAST-ACTIVITY-SORT、RULE-LIB-PINNED-SEGMENT 等涉及 Library / Bookshelf 列表的规则。
HEXAGONAL_RULES.yaml
library_listing_mode、library_cover_avatar_strategy 等关于列表模式与封面策略的规则。
VISUAL_RULES.yaml
library_overview_plan20_status、library_card_poster_strategy_status、library_list_layout_strategy_status 等。
输出一个简短对照表：
哪些规则已经在当前实现中生效。
哪些规则只在 Library 卡片生效、但还没下沉到 Bookshelf 列表，需要这次一起补齐。
哪些规则会被这次改版「扩展 / 演进」（需要在 ADR-091 中说明）。
三、前端实现计划（页面 + 组件）
3.1 整体布局与入口
Library 详情页顶部区域保持不变

保留面包屑、Library 标题、描述、统计信息。
重构 Bookshelves 部分为独立 Widget

若当前已存在 Bookshelf 列表 widget，则确认接口（props）是否满足 Plan21 要求。
若不存在：
新建 BookshelfMainWidget.tsx（或复用 features/bookshelf/ui 里的组件）。
由 page.tsx 传入 libraryId，Widget 内部负责：
调用 useBookshelves(libraryId)。
渲染顶部控制条 + 卡片列表。
3.2 控制条（Control Bar）
对照 Plan21/13，控制条至少包含：

布局与基本元素

左侧：Section 标题 书橱（如截图）。
右侧：
视图切换按钮：网格 / 列表（和 Library 列表保持交互一致）。
排序下拉：默认 last_activity，可选 name、created_at 等（与 RULE-LIB-LAST-ACTIVITY-SORT 一致）。
归档过滤：全部 / 仅活跃 / 仅归档（映射到 archived_at 字段）。
「新建书橱」主按钮。
状态持久化

视图模式、排序、过滤：
本地存储 key 设计如：wl_bookshelves_view_${libraryId}、wl_bookshelves_sort_${libraryId}。
初次加载从 localStorage 恢复，变更时更新 localStorage + 触发 refetch。
行为与 API 对齐

不改变后端 UseCase 签名：
若当前 GET /bookshelves 已支持 sort_by, status 参数，直接通过 query 传递。
若没有排序/过滤参数，这次只做前端排序（在 ADR-091 中标为「临时策略」）。
3.3 Bookshelf 卡片（Grid 视图）
参考你刚刚在 Library 卡片上做的「海报式」设计和 Plan21：

外观风格

宽高：统一 16:9 或 Plan21 指定尺寸（例如 320×220）。
上半部分：封面图 / 渐变背景 + Title 覆盖在图片里。
Title 字体：
font-family：走你前面定义的 .library-card-title 字体栈（Inter / system-ui）。
font-weight: 600，letter-spacing: 0.02em，字号略小于 Library 大卡片。
右上角：PINNED / Archived 等 small badge。
下部：
第一行：Tags + Pinned badge 同行，标签靠左、badge 靠右。
第二行：统计信息（Notes 数量、最近活跃时间、浏览数等）。
第三行：辅助说明（如状态、访问频率）。
交互

整卡点击：进入对应 Bookshelf 详情页面。
悬停操作区（根据 Plan13）：
编辑书橱。
归档 / 恢复。
置顶 / 取消置顶。
上传封面按钮：
沿用 Library 卡片中封面上传的交互模式（同一 UX/视觉）。
Pinned 分段

在 Widget 中按 pinned 字段把 Bookshelves 分为：
「PINNED」段：固定在列表顶部，有分组标题。
「OTHERS」段：普通书橱。
前端排序逻辑：
Pinned 段内按 pinned_order 或 last_activity 排序（对齐 RULE-LIB-PINNED-SEGMENT）。
其他段按当前选中的排序项。
3.4 列表视图（List 视图）
布局

行式卡片，左侧小封面（方形 thumbnail），右侧标题/描述/统计，风格参考 VISUAL_RULES 中 library_list_layout_strategy。
Pinned & Archive 状态通过小徽章标识。
重用逻辑

数据处理（分段 / 排序 / 过滤）与 Grid 视图共用 Hook/Selector，只改变渲染方式。
四、规则文档更新计划（三份 RULES）
4.1 VISUAL_RULES.yaml
在 metadata 或 library_*_status 中更新：

library_card_poster_strategy_status: 从 ⏳ 改为 ✅，说明 Bookshelf 列表也采用 Poster 风格。
library_list_layout_strategy_status: 更新为 ✅，注明 Bookshelf 内部列表已对齐。
在 component_styles 或新的小节中增加：

「Bookshelf Poster Card Visual Rules」：
卡片尺寸、阴影、圆角。
标题字体栈（引用 .library-card-title 片段）。
Pinned 段落分组视觉策略。
4.2 HEXAGONAL_RULES.yaml
在 library_listing_mode 下补充：
Bookshelf 在 Library 详情页展示的规则（仍属于同一 Aggregate 上下文，只是 UI 视图）。
新增小节或扩展：
library_cover_avatar_strategy：注明 Bookshelf 同样遵守封面策略（cover_large / cover_thumb）。
任何对 UseCase 调用方式的新约束（比如：排序/过滤参数必须由 UI 传递，不在 infra 强写）。
4.3 DDD_RULES.yaml
在 Library / Bookshelf 相关 policy 下补充：
「Library Detail Bookshelf Management v2」：说明 grid/list、Pinned 段落、归档策略在 UI 层的统一。
若前端引入了新的字段（如 bookshelf.last_activity_at 已经存在）：
确认规则里已有说明，缺失的补上；没有改动 domain 行为时在 ADR 中注明「UI-only change」。
五、ADR-091 撰写计划
在 ADR 下新增 ADR-091-library-bookshelves-page-plan21-13-integration.md（名称可微调），内容结构建议：

Context
描述 LibraryLog / Bookshelf 当前交互存在的问题（对照老 UI）。
引用 Plan13 / Plan21、VISUAL_RULES、HEXAGONAL_RULES、DDD_RULES 的相关部分。
Decision
采用 Poster 式 Bookshelf 卡片（标题覆盖在封面图上）。
在 Library 详情页统一管理 Bookshelf（grid/list + sorting + pinned segment）。
不改变后端聚合边界与 API 语义，仅扩展查询参数（若有）。
Consequences
优点：信息密度、视觉一致性、Pinned/Archive 策略可视。
风险：前端复杂度提高、卡片组件与 LibraryCard 有重复，需要后续抽象公共 UI 模块。
Implementation Notes
列出关键文件路径和需要修改/新增的组件。
记录 localStorage 键名 / Query 参数契约。
Migration / Rollout
UI 迁移步骤：A/B 切换策略（如果需要）、回滚方案。
测试要点：Pinned 排序、归档过滤、无封面时的渐变背景等。
六、任务拆分与执行顺序（给 agent 用）
阶段 1：代码探查 & Hook 设计
定位并阅读所有和 Bookshelf 与 Library 详情相关的前端文件。
输出一个小的「文件—职责」清单，确认哪里插入新 Widget 最合理。
阶段 2：提取公共视觉组件（可选）
若 LibraryCard 和 BookshelfCard 有大量重复：
在 shared/ui 层抽出基础 PosterCard 组件。
阶段 3：实现 BookshelfMainWidget（Grid 视图）
加入控制条、Pinned 分段、Poster 卡片。
阶段 4：实现 List 视图
共用数据逻辑，添加小型行式卡片组件。
阶段 5：规则文件与 ADR 更新
同步修改 VISUAL_RULES.yaml / HEXAGONAL_RULES.yaml / DDD_RULES.yaml。
新增 ADR-091 并记录本次改造细节。
阶段 6：验证
本地跑前端，手动验证：
Pinned 段落排序；
grid/list 切换；
归档/置顶操作与视觉反馈；
无封面 / 有封面场景下标题可读性。