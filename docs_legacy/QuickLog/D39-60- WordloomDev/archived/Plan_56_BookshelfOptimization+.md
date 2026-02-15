Plan: 书橱 PIN、排序与规则同步（Plan_55 落地）
围绕你给的 4 张截图 + Plan_55 + 三份 RULES/ADR，我会把本轮工作拆成前端 UI 行为（PIN 徽标 + 标签列微调）、状态命名校正（FROZEN→ARCHIVED）、排序规则落地，以及规则/ADR 文档收口、Dashboard 和文档语义完全统一。

Steps
明确状态与命名

在后端 BookshelfStatus 枚举和数据库模型里确认只有 ACTIVE / ARCHIVED（无 FROZEN）；用全文搜索列出任何 FROZEN/Frozen/frozen 代码或文档引用。
在 Plan_55_Tag&BookshelfOrder.md 中，将“FROZEN”全部改成“ARCHIVED”，在靠前位置加一行说明：“Plan 早期草稿中的 FROZEN = 实际实现中的 ARCHIVED”。
如代码中还存在 FROZEN 状态值（前端/后端）：计划统一替换为 ARCHIVED，必要时在前端 DTO 解析处加一次性兼容映射（将历史 'frozen' 读成 'archived'）。
置顶行为与 PIN 徽标（Screenshot1/2）

前端：在 Orbit 的书橱列表组件（例如 frontend/src/features/bookshelf/ui/BookshelfList 或 BookshelfDashboardBoard/BookshelfMainWidget）里定位 PIN 图标按钮和书橱名称区域。
交互规则：
点击 PIN → 调用现有 /bookshelves/{id}/pin 接口（或对应 useMutation），取消调用 /unpin；成功后本地列表使用 isPinned 字段将数据分为 pinned 与 regular 两段。
pinned 段始终展示在列表最前，内部按 updatedAt 或 lastActivityAt 降序；regular 段按当前排序选项（名称/最近活动）排列。
徽标样式：
在名称上方与 ACTIVE 同一位置增加 PIN 徽标：文字可为 “PINNED” 或 “已置顶”，颜色使用 VISUAL 里的丝绸蓝（参考 VISUAL_RULES.yaml 中 bookshelf/pinned 色板，抽出 --wl-bookshelf-pinned-bg/fg 变量）。
ACTIVE 保持现有中性色；ARCHIVED 若在该视图展示（例如全部书架视图），依照 VISUAL 里的状态颜色 tokens。
无障碍与状态感知：
为 PIN 按钮加 aria-pressed、aria-label（“置顶书橱 / 取消置顶书橱”），点击成功后可弹出简短 toast。
保证 PIN 徽标在只看一行标题区域时也能一眼分辨 pinned。
标签列左移与内容对齐（Screenshot3）

在 Orbit 书橱列表中找到 “标签” 列头 <th> 与对应每行标签容器（可能是 tag chips 的 <div>）。
调整：
轻微减少列头/内容左 padding（例如从 pl-4 改为 pl-2），或加一个小的负 margin/translate 让列整体左移 2–4 像素。
保证列头文字、-- 无标签 -- 占位、以及 tags chips 左边缘对齐。
如果 Bookshelf Dashboard 列表（管理端）也有 tags 列，对齐方式一并微调，让两个列表的视觉节奏一致。
书橱与标签排序规则按 Plan_55 落地

书橱排序：
默认视图：只看 ACTIVE 书橱（filter=ACTIVE），排序按 “最近活动” （优先 lastActivityAt，没有则退回 updatedAt / createdAt），与 Plan_55 建议保持一致。
高级筛选：提供排序下拉：最近活动 / 名称（A–Z / 拼音）/ 创建时间 / 书本数；状态筛选下拉：全部 / ACTIVE / ARCHIVED。
列表层实现 pinned 段 + regular 段排序逻辑（pinned 段先，内部按最近活动；regular 段按当前排序 key），不在 Domain 里做“神秘移动”。
标签排序：
全局 Tag 列表、下拉搜索：使用名称字母/拼音升序排序（现有 /tags/catalog、/tags 搜索接口已经支持 order=name_asc，前端在 hooks 中默认传这个排序）。
每个书橱卡片上的标签：
最多 3 个标签已经满足 Plan_55 约束；
渲染前对标签数组使用一个 sortTagsByName() helper 做稳定排序；将来若增加“类型优先级”，可在 helper 中引入 category 权重再按名称排序。
同步三份 RULES 以匹配新行为（Step 5）

DDD_RULES.yaml：
在 Bookshelf 模块章节新增/更新规则，例如：
RULE-BOOKSHELF-STATUS: status 仅包括 ACTIVE, ARCHIVED, DELETED；FROZEN 为废弃名。
RULE-BOOKSHELF-PIN: pin 只改变 is_pinned（和可选的 pinned_order），不影响 status；ARCHIVED 时自动取消 pinned。
RULE-BOOKSHELF-ORDERING: 默认排序 last_activity_at；UI 层可对 pinned 段单独排序。
HEXAGONAL_RULES.yaml：
在 bookshelf 的 input/output ports 描述中写清：
ListBookshelves use case 返回 status 与 is_pinned，默认仅 ACTIVE；
pin/unpin use cases 不改变书架其它字段；
任何 “FROZEN 区” 描述改为 “ARCHIVED 区”。
VISUAL_RULES.yaml：
在书橱 dashboard / orbit 列表部分，增加/更新：
PIN 徽标的色板 token 名称和使用位置（在名称上方，颜色丝绸蓝）；
状态文本仅 ACTIVE / ARCHIVED，不再用 FROZEN；
标签列左右 padding 规范，确保头和内容对齐。
新增 ADR-098（Step 6）

在 ADR 下按现有模式创建 ADR-098-bookshelf-orbit-pin-and-ordering.md（名称可微调但保持 ADR-xxx-... 风格，参考 ADR-094~097）。
内容结构：
Context：说明 Orbit 书橱列表当前问题：PIN 只在右侧、不起作用，状态命名与文档 FROZEN 不一致，标签列微偏。
Decision：
统一状态为 ACTIVE/ARCHIVED；
将 PIN 变为“真正的置顶行为”，并在标题上方显示丝绸蓝徽标；
列表排序规则与 Plan_55 一致；
标签按名称排序，列对齐规则如 VISUAL 描述。
Consequences：对用户心智（审计视角）、实现复杂度（不做全局拖拽排序）、风险与回滚方式。
Links：引用 Plan_55 文档、对应 RULES 段落和已有 ADR（特别是 094–097）。
更新 Plan_55 进度与后续拆分（Step 7：周全中文计划）

在 Plan_55_Tag&BookshelfOrder.md 末尾 Progress 区补充新小节：
标记：
[x] ACTIVE/ARCHIVED 状态命名统一
[x] Orbit 书橱列表 PIN 行为与徽标实现（完成后再勾）
[x] 标签列左移/对齐调整
[x] 三份 RULES 同步、ADR-098 完成
为后续可选工作保留 [ ] 条目（例如 “Pinned 区人工排序（pinned_order）”），并注明“非本轮范围”。
确保 Plan_55 中书橱排序 & 标签顺序部分已经完全使用 ARCHIVED 术语，并在最开始用一句话把 “ACTIVE / ARCHIVED / PINNED” 的关系讲清楚，方便你以后翻阅。
Further Considerations
后端需不需要提供 order_by=last_activity_at 的专门参数（而不是前端在内存里算）？可以在当前阶段仍使用 updated_at 替代，后续若引入 Chronicle 统计再补。
Orbit 列表、Dashboard 列表、Library 顶部汇总三处关于 PIN 与 ARCHIVED 的视觉风格，是否需要在 VISUAL_RULES 里做一张小对照表，避免未来出现第四种变体。