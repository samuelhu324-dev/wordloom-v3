Plan: Wordloom Book 页面「Book Surgery」实现方案
基于现有 Library / Bookshelf 页面和 Plan_52_BookSurgery.md，下面是一个尽量贴近你现有代码结构、可分阶段落地的实现计划，并用简略 Markdown 草图辅助说明布局。

Steps
路由与页面骨架：统一到现有 Book 路由

继续使用现有 Book 详情页路由（假设类似：frontend/src/app/admin/libraries/[libraryId]/bookshelves/[shelfId]/books/[bookId]/page.tsx），在其中重构 UI 结构，而不是新开路由。
页面仍包在 AdminLayout 下（顶部 Theme / Libraries / Workbook 导航自动继承），保持与 Library / Bookshelf 一致的「审计风」chrome。
顶部使用现有 Breadcrumbs 组件，路径为：Libraries / {LibraryName} / {BookshelfName} / {BookName}。
骨架草图：
[AdminLayout 顶栏：Wordloom | Theme | Libraries | Workbook]

Libraries / LibraryLog / ShelfQuickLog / {BookName}

┌───────────────────────────────────────────────┐
│         Book Header + Overview Card          │
└───────────────────────────────────────────────┘

┌─────────────────────────┬────────────────────┐
│ 左：Tabs + Blocks/Chron │ 右：Info / Tags    │
└─────────────────────────┴────────────────────┘

顶部区：面包屑 + 标题行 + 概览卡 + 指标行

顶部区域拆成两层：
Breadcrumbs + 主标题区（Book 名、所属 Bookshelf / Library、副标题灰字）。
紧接一张横向「Book 概览卡」，尽量复用 Library / Bookshelf 已有的卡片组件/样式（例如 summary card、metric chip）。
概览卡左侧：
迷你封面（可以沿用 Bookshelf 的渐变背景 / 缩略图方案）。
Book 名（H1）+ 一行简介。
Tag 小胶囊：沿用 Bookshelf 的 tag pill 组件，限制展示前 3 个，超出用 “+N”。
概览卡右侧：两行小指标，复用 Library / Bookshelf metrics 卡的样式（图标 + 数字 + tooltip）：
行 1（进度类）：Blocks 总数 / Stable Blocks 数 / % 覆盖率。
行 2（活动类）：最近活动时间 / 本周查看次数 / Chronicle 事件数。
标题右侧放状态 pill：
复用 Bookshelf 上 Seed / Growing / Stable / Legacy 的状态胶囊样式（颜色 + lucide 图标）。
在旁边预留一个 Active / Archived 小 pill（先只展示状态，不必实现归档操作）。
顶部简略图：
Libraries / LibraryLog / ShelfQuickLog / BookFoo

BookFoo                            [SEED] [ACTIVE]
所属：ShelfQuickLog · LibraryLog

┌───────────────────────────────────────────────┐
│ [缩略图] BookFoo    一行简介       Tag1 Tag2 +2 │
│                                               │
│ 📚 Blocks: 12   ✅ Stable: 5   进度: 41%       │
│ ⏱ 最近活动: 3h  👁 本周查看: 24  📝 事件: 18   │
└───────────────────────────────────────────────┘
主体左栏：Tab 切换 + Overview / Blocks / Chronicle

使用一个 Tabs 组件（可以复用已有的 page-level tab 组件）将左栏划分为三个主视图：
Overview（概览）
Blocks（块列表/编辑工作区）
Chronicle（仅当前 Book 的时间线）
Overview Tab 内容：
「当前成熟度说明」：Seed/Growing/Stable/Legacy 四种状态的简短文案，可直接缩写 Bookshelf 页面那套描述。
「Todo / Checklist」预留区：先放静态占位或极简文本，后续再接入真正的 Book 级任务。
「最近事件摘要」：调用 Chronicle 数据，只取最近 5 条事件，以列表+时间形式展示，点击可导航到 Chronicle Tab。
Blocks Tab 内容（重点）：
顶部工具条：
搜索框（先支持在原文 / 译文中模糊搜索；实现上可以从前端 filter 起步，后续再考虑后端搜索）。
筛选下拉：按状态（Seed/Growing/Stable/Legacy）、是否有译文、是否标记 TODO（可以先只实现状态筛选，TODO 预留）。
排序选择：最近更新 / 创建时间（先以前端排序为主，和现有 hooks 对齐）。
主体为紧凑的「Blocks 表格」：
每行一条 block，列包括：状态点、原文摘要（前 1–2 行）、译文摘要、最后更新时间、操作图标（编辑、历史）。
视觉风格参考审计/Excel：字体略小、行距略紧、可使用 zebra stripes 或细分界线。
优先使用现有 Block 相关 UI 组件（如列表、编辑区、软删除提示），避免重写。
底部：分页器，沿用现有 Block hooks 的分页能力。
Chronicle Tab 内容：
左栏全宽放置现有的 Chronicle 时间线组件（目前已经在老 Book 页右侧用过）。
时间线仅展示当前 Book 相关的事件：BlockAdded / BlockStatusChanged / BookMovedToBasement / TagUpdated 等。
支持简单过滤（如事件类型勾选）可以作为后续增强；首版可保持只读。
左栏 Tabs 草图：
[ Overview | Blocks | Chronicle ]

# Overview
- 当前阶段：Seed · 草创
- 说明：快速捕捉想法，允许随意增删...
- 最近事件：
    [3h前] BlockStatusChanged · 草稿 → 成长
    [1d前] BookCreated · 从 ShelfX 创建
    ...

# Blocks
搜索框 [         ]  状态: [All]  排序: [最近更新]

状态  原文摘要         译文摘要        更新时间    操作
●     lorem ipsum...   ...            3h前       ✎ ⟳
○     ...              ...            1d前       ✎ ⟳

# Chronicle
|  时间线组件（只看当前 Book）         |
主体右栏：审计 Info Panel（复用 Library/Bookshelf 语法）

右栏做成一个统一的 EntityInfoPanel 思路：
未来可以让 Library / Bookshelf / Book 共用一套基础组件，只是按 props 决定展示哪些字段。
在 Book 页右栏展示内容：
Book Info：所属 Library / Bookshelf、创建时间 / 创建人、最近修改人。
Tags & 分类：展示全部 tag，与顶部概览卡一致，但在这里支持 tooltip（悬浮展示标签说明）。
状态策略：基于当前 maturity，展示对应的简短说明，并提供一个链接到帮助页（比如 /docs/book-status）。
风险 / 备注：先预留一块空白区域或「暂无备注」，未来可挂接审计备注。
布局高度与左栏对齐，支持滚动（如果 Info 内容变长，不挤压左侧工作区）。
左右栏简略图：
┌─────────────────────────┬───────────────────────┐
│ [Tabs + Blocks/Chron..]│  Book Info            │
│                         │  - Library: LibraryLog│
│                         │  - Shelf: ShelfQuick…│
│                         │  - 创建: ...         │
│                         │                       │
│                         │  Tags                 │
│                         │  [STUDY] [LAB] [...]  │
│                         │                       │
│                         │  状态策略             │
│                         │  Seed 阶段说明...     │
│                         │                       │
│                         │  风险 / 备注(预留)    │
└─────────────────────────┴───────────────────────┘
数据与 hooks：复用现有层级加载与 Block/Chronicle hooks

顶层数据加载（在 page 组件中）：
使用已有的：useBookDetail(bookId) / useBookshelf( shelfId ) / useLibrary(libraryId) hooks 获取三层上下文。
使用 useBlocksByBook(bookId, { page, filter, sort }) 获取 Block 列表。
使用 useChronicleForBook(bookId) 获取时间线数据。
将上述数据通过 props 下发给三个 Tab 组件和右侧 Info Panel，保持「page 负责数据装配、子组件只关心展示和局部交互」的结构。
Metrics 计算：
Blocks 总数：直接来自 blocks.total 或 blocks.length。
Stable Blocks 数 与 覆盖率：在前端根据 Block status 字段统计即可（先不必依赖专门统计 API）。
活动数据（最近活动 / 本周查看 / 事件数）：
最近活动时间：从 chronicle 里取最新事件的时间戳。
本周查看次数：如果后端有 view-count 字段直接用；如果暂时没有，可以先用假数据或留空/「—」。
事件数：chronicle 事件总数。
状态、Tag、成熟度等字段直接沿用各自 DTO 中定义的枚举/字段，避免再造轮子。
视觉与交互对齐：与 Library / Bookshelf 统一语言

色彩：
从 Library 的主题色 hook（类似 useLibraryThemeColors）推导出 Book 页的 CSS 变量，在概览卡上做轻量渐变条，呼应现有 Library / Bookshelf。
Seed/Growing/Stable/Legacy 用已有的色值和 lucide 图标；确保 tooltip 说明一致。
图标 + Tooltip：
所有指标的 icon 统一加 tooltip：状态说明（Seed · 草创…）、指标含义（“Stable Blocks：已通过校对，可展示使用的 block 数量”）等。
操作图标（编辑、历史）也加简短 tooltip。
数据密度控制：
Overview + 顶部概览卡：留白较多，段落式文本，适合浏览；视觉靠近 Library 统计大卡。
Blocks Tab：信息密度提高，字体略小、行距紧一些，视觉上接近「审计表格」。
保证关键字段在一屏内水平可见，避免横向滚动过多。
渐进式实施顺序（避免单文件再爆 500 行）

第一步：只改结构和静态 UI
在现有 Book 页面中先搭好：Breadcrumbs + 标题行 + 概览卡 + 左右双栏 + Tabs。
所有数字先用 mock / 现成 hooks 的简易结果，先不加搜索 / 筛选 / 复杂交互。
第二步：Blocks Tab 只读表格化
把当前 Block 编辑组件拆分：上层是表格/列表展示，下层/抽屉中保留原编辑逻辑。
先实现：状态点 + 原文摘要 + 译文摘要 + 更新时间 + 编辑入口，不做筛选/排序。
第三步：Chronicle Tab 接入
将原右侧的 Chronicle 抽出为 Tab 内容，数据源保持不变（只过滤当前 Book）。
在 Overview Tab 加一个「最近 5 条事件」的小摘要。
第四步：右侧 Info Panel 组件化
抽一个 EntityInfoPanel（或 BookInfoPanel）组件出来，专管右侧信息。
之后可以在 Library / Bookshelf 页重复使用这个组件，只传不同 props 控制显隐。
第五步：增强交互（可选）
Blocks Tab 上增加：状态/是否有译文/TODO 筛选，排序下拉。
Chronicle Tab 增加事件类型过滤和「跳转到相关 block」的小交互。
Further Considerations
Block 编辑模式选择：你更偏向「表格列表 + 右侧/下方弹出编辑区」还是「列表行内直接展开编辑」？这会影响 Blocks Tab 的微交互设计。
是否需要 Book 级别归档 / 冻结：若短期不做操作按钮，可以先只展示 Active / Archived 状态；未来再挂接 API。
视图偏好持久化：是否要像 Libraries / Bookshelves 一样，用 localStorage 记住用户在 Book 页选择的 Tab / 筛选 / 排序？如果需要，可以沿用现有的 key 命名和 hook 模式。
