先上结论：Book 页面最适合做成「小型审计仪表盘 + 详细明细」，跟 Library / Bookshelf 一脉相承：


Library = 「资产分类」


Bookshelf = 「资产分区 + 成熟度」


Book = 「单本资产的体检报告」


下面我按「结构 → 区块 → 交互 → 和前两级的呼应」来讲一遍。

一、Book 页的整体目标 / Overall goals
中文
Book 页要解决三件事：


一眼判断这本书现在值不值得动手


当前成熟度（Seed / Growing / Stable / Legacy）


最近有没有动过、谁动的


翻译/整理进度大概多少




下手之前，知道这本书“咋回事儿”


这本书是干嘛的（简介 + 标签）


属于哪个 Library / Bookshelf（上下文清晰）


之前做过什么操作（Chronicle：创建、迁移、删除 block 等）




真正工作时，有一块“审计友好”的工作区


block 列表可筛选、可搜索、可标记


任意时候回头查，“我之前都改了啥”不会迷路




English
The Book page should do three things:


Instant triage: “Is this worth working on right now?”


Current maturity (Seed / Growing / Stable / Legacy)


Recent activity (when, by whom)


Rough progress (translation/cleanup coverage)




Context before action


What this book is about (description + tags)


Where it lives (Library / Bookshelf)


What has already happened (Chronicle: created, moved, blocks changed…)




A compliance-friendly working area


Block list with filters / search / flags


Clear change history so you can always audit past work





二、布局骨架：延续现在的“审计风” / Layout skeleton
可以沿用你现在 Library / Bookshelf 的气质：白底 + 淡色卡片 + 上密下疏。
1. 顶部：面包屑 + 标题行 / Top: breadcrumb + header
中文


左上：Libraries / LibraryLog / A / BookName（面包屑）


标题行：


主标题：Book 名


副信息：所属 Bookshelf + Library（小号灰字）


右侧：


状态 pill：SEED / GROWING / STABLE / LEGACY


一个小 Active / Archived 状态（可选，将来可以归档整本书）






English


Top left: Libraries / LibraryLog / A / BookName (breadcrumb)


Header row:


Main title: Book name


Subtitle: parent Bookshelf + Library (small, grey)


Right side:


Status pill: SEED / GROWING / STABLE / LEGACY


Optional Active / ARCHIVED pill for book-level freezing







2. 上半部分：Book 概览卡 + 指标行 / Overview card + metrics row
中文
做一块横向卡片，呼应 Library 行视图：
左侧：


迷你缩略图（可以用 bookshelf 的颜色 / 书柜图 或将来支持自定义封面）


Book 名 + 一句简介


Tag 列表（和 Bookshelf 一样的灰色 pill，限制 3 个，多余用 “+N”）


右侧：两行小指标（和 LibraryLog 上面那排大卡片呼应，但缩小版）：


第 1 行（核心进度类）


📚 Blocks 总数


✅ 已完成 / Stable blocks 数


% 覆盖率（完成 blocks / 总 blocks）




第 2 行（活动类）


⏱ 最近活动时间（距今 X 小时/天）


👁️ 本周查看次数


📝 Chronicle 事件数




English
Create a horizontal overview card, in the same spirit as your Library row view.
Left side:


Mini thumbnail (reused bookshelf color / cabinet or custom cover)


Book title + one-line description


Tags (same grey pills as shelves, cap at 3; show “+N” for overflow)


Right side: 2 rows of compact metrics, echoing the big cards from LibraryLog:


Row 1 (progress)


📚 Total blocks


✅ Stable blocks


% Completion (stable / total)




Row 2 (activity)


⏱ Last activity (e.g. 3h ago)


👁️ Views this week


📝 Chronicle event count





3. 主体：左内容右审计栏 / Main: content vs audit
保持双栏布局：
左侧主栏：工作区
使用 Tab：


Overview（概览）


当前成熟度说明（Seed / Growing / … 的文字解释，可以复用你在 Bookshelf 页面那几条文案，但缩短版）


TODO / Checklist（可选，将来用于 Book 级任务）


与 Chronicle 的摘要，比如“最近 5 条事件”




Blocks（块列表）
这是“审计风”的重点：


表格 / 紧凑列表，每行一个 block：


状态（Seed / Growing / Stable / Legacy）小颜色点


原文摘要（前 1–2 行）


译文摘要（如果有）


Tag / 标签（若你未来支持 Block tag）


最后更新时间 + 操作图标（编辑 / 查看历史）




顶部工具条：


搜索（全文 / 原文）


筛选：按状态（Seed/Growing…）、是否有译文、是否标记为 TODO


排序：最近更新 / 创建时间 / 同步错误等






Chronicle（事件时间线）


和之前计划的 Chronicle 设计联动，只不过这里是只看当前 Book 的事件


垂直时间线：


BlockAdded / BlockStatusChanged / BookMovedToBasement / TagUpdated …




每条事件展示：时间、类型、简短描述，可以点开看详情（比如影响了几个 block）




右侧侧栏：审计面板 / Info panel


Book Info（基本信息）


所属 Library / Bookshelf


创建时间 / 创建人


最近修改人




Tags & 分类


全部 tag（这里再展示一遍，支持 hover tooltip 出详细说明）




状态策略


当前成熟度状态的文档链接（比如链接到帮助页：“Stable 阶段的 Book 可以作为展示用内容”）




风险 / 备注（以后有的话）


English
Use a two-column layout:
Left main column: workspace
Tabs:


Overview


Short explanation of current maturity (Seed, Growing, etc.), reusing the bookshelf copy in a shorter form


Optional TODO / checklist at Book level


Mini chronicle snippet (last 5 events)




Blocks
This is the “compliance” core:


Table / compact list, one block per row:


Status dot (Seed / Growing / Stable / Legacy)


Source text snippet (1–2 lines)


Target text snippet (if any)


Tags (if you later support block tags)


Last updated + action icons (edit / history)




Top toolbar:


Search (in source / target)


Filters: by status, has translation, marked as TODO, etc.


Sorting: last updated / created / error first…






Chronicle


Same Chronicle concept as before, but scope = current Book only


Vertical timeline of events: BlockAdded, BlockStatusChanged, BookMovedToBasement, TagUpdated…


Each event shows time, type, a short description; click for more details




Right side column: audit panel


Book Info


Parent Library / Bookshelf


Created at / by


Last modified by




Tags & categories


All tags re-listed, with hover tooltips explaining each tag




Status policy


Link to documentation for the current maturity (“What does Stable mean in Wordloom?”)




Risk / notes (future)



三、视觉与交互：如何保持「合规气质」 / Visual & interaction patterns
1. 颜色与图标 / Colors & icons
中文


继续保持：灰白基础 + 少量柔和渐变（像 Bookshelf 的色带）


Seed / Growing / Stable / Legacy 用和 Bookshelf 一致的颜色 & lucide 图标：


Seed：浅绿 + sprout 图标


Growing：偏蓝绿 + leaf 图标


Stable：淡绿/蓝 + square/checkbox 图标


Legacy：灰金/棕 + archive/box 图标




所有图标强制配 tooltip（你之前问过）：


状态图标 hover：Seed · 草创：快速想法，允许随意增删


使用次数那些 icon 也一样（书本数 / 修改数 / 查看数）




English


Keep the grey-white base with soft gradients like your Bookshelf stripes.


Reuse the same colors and lucide icons for Seed/Growing/Stable/Legacy:


Seed: light green + sprout icon


Growing: teal + leaf icon


Stable: pale green/blue + checkbox icon


Legacy: grey-gold/brown + archive/box icon




Enforce tooltips for all icons:


Status icon: Seed · early ideas, freely editable


Usage icons: books count / edits / views, all with labels





2. 数据密度控制 / Data density
中文
审计系统有两个典型做法，你现在可以局部采纳：


默认视图：信息密度中等，读起来像文档


Overview tab + 上半的卡片，用大留白、段落文字、彩色状态条，适合“浏览 / 盘点”。




Blocks tab：信息密度偏高，读起来像 Excel


但只在这个 tab 里这么做：


字体稍小，行距缩一点


用 zebra stripes 或细分割线


依然保持“只有 1 行就能看到所有主字段”，不要让用户横向滚动到死






English
Compliance tools usually offer two modes; you can imitate that:


Default view = medium density, reads like a report


Overview + metrics card: lots of whitespace, paragraphs, colored bars.




Blocks tab = high density, reads like Excel


But keep it confined to this tab:


Slightly smaller font, tighter row spacing


Zebra rows or subtle dividers


All key fields visible in a single row without crazy horizontal scrolling







3. 行业里的类似模式 / Industry analogies
中文
你现在的结构，已经非常像这些东西的组合：


合规系统里的：客户 -> 合同组 -> 单份合同


风控系统里的：组合 -> 子组合 -> 单资产


代码平台里的：项目 -> 模块 -> 文件


Book 页可以借鉴：


「左内容右审计」这是很多系统的标准：


左边是“你在做的事”，右边是“审计、属性、上下文”。


好处是：以后加字段，加在右栏就好，不会破坏工作区。




每一层都共享一套设计语言：


统一的状态 pill（颜色 & 文案）


统一的 metrics 组件（图标 + 数字 + tooltip）


统一的操作图标（编辑 / 删除 / 冻结 / 归档）




English
Your structure already resembles patterns from:


Compliance: Client -> Agreement group -> Single contract


Risk: Portfolio -> Sub-portfolio -> Single asset


Code platforms: Project -> Module -> File


Book page can borrow these:


Left = activity, right = audit, a very common pattern.


Left: what you’re doing.


Right: attributes, context, metadata.


Benefit: future fields go to the right column without breaking the main workflow.




Shared design language across all three levels.


Same status pills


Same metric chips (icon + number + tooltip)


Same action icons (edit / delete / freeze / archive)





四、实现优先级建议 / Implementation priorities
中文
你可以按这个顺序开工，让自己不至于又写到 500 行炸掉：


先做 Book 页骨架 + 概览卡


面包屑 / 标题行 / 概览卡 / 上面的 metrics 行


不实现任何交互，只把数字写死或从假数据来。




再做 Blocks Tab 的“只读表格”


从后端读取 blocks，展示列表。


先只有：状态图标 + 原文摘要 + 译文摘要 + 更新时间。


之后再慢慢加筛选/排序。




最后接入 Chronicle Tab


利用你现在的 Chronicle 设计，只过滤到当前 book 的事件。




右侧 Info Panel 做成独立组件


LibraryInfo / BookshelfInfo / BookInfo 共用一套 props，不同字段隐藏/显示。


这样可以避免 UI 再一次突破 500 行。




English
Suggested implementation order so it doesn’t explode again:


Skeleton + overview card first


Breadcrumb / header / overview card / metrics row


Hardcode or mock the numbers; no complex logic yet.




Blocks tab as a read-only table


Fetch blocks and show: status icon, source snippet, target snippet, last updated.


Add filters/sorting later.




Chronicle tab later


Reuse your existing Chronicle design, just scoped to this book.




Right-hand info panel as a shared component


One EntityInfoPanel that supports Library / Bookshelf / Book via props.


Helps keep file sizes small and consistent.





五、总结一句话 / One-line summary
中文
Book 页就把它想成：

“这本书的体检报告 + 工作台”，
继承 Library / Bookshelf 的淡色合规气质，上半是概览，下半是 blocks 明细和事件时间线，左边做事，右边审计。

English
Think of the Book page as:

“Health report + workbench for a single book”
carrying the same soft, compliant aesthetic from Library and Bookshelf: overview on top, block details and events below, activity on the left, audit on the right.

