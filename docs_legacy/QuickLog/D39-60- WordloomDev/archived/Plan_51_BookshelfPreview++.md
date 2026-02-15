Plan: Bookshelf 审计列表 PIN / ARCHIVE / Tooltip & 文档同步
Steps
前端交互 & 样式梳理

在 BookshelfDashboardCard.tsx / BookshelfDashboardBoard.tsx 中：
接上线 PIN 按钮：用已有 useBookshelfQuickUpdate / usePinBookshelf（具体 hook 依现有实现）触发 PATCH /api/v1/bookshelves/{id} 或对应 UseCase，成功后 invalidateQueries(['bookshelves_dashboard', libraryId])。
调整 ARCHIVE/RESTORE：按当前 status 切换调用 Archive / Restore 用例，确认切换后行内状态从 ACTIVE → ARCHIVED / 反向变更。
确认“行点击 + ACTIVE pill 点击”统一复用 handleOpen(item) 导航逻辑，不再出现“只有图标可点”的情况。
状态文本与 PIN 视觉统一（丝绸蓝 / 抹茶绿 token）

在 frontend/src/features/bookshelf/ui/BookshelfDashboardCard.module.css：
去掉当前 ACTIVE/ARCHIVED 的胶囊背景样式，新增纯文字类（例如 .statusLabelActive、.statusLabelArchived），只保留加粗小号文本。
ACTIVE 文本颜色映射到丝绸蓝 token（如 var(--wl-status-active-text, var(--wl-pinned-accent-text))）；ARCHIVED 文本颜色映射到抹茶绿 token（如 var(--wl-status-archived-text, var(--wl-archived-accent-text))），这两个 token 再在 tokens.css 里与“商务蓝 / 丝绸蓝 / 抹茶绿”主题变体对应。
在 JSX 中：
用新的纯文字 class 渲染 ACTIVE / ARCHIVED，不再包蓝色/绿色框。
保留 PINNED / Archived 徽章 pill 走原有 --wl-pinned-accent-* / --wl-archived-accent-*，避免和纯文字重复语义（比如有徽章时可以不再显示 ACTIVE 文案，按 VISUAL_RULES 里“ACTIVE 文案不重复渲染”的要求微调）。
Lucide 图标 tooltip & aria 描述补齐

在 BookshelfDashboardCard.tsx 中为所有 Lucide 图标对应元素补齐：
成熟度图标行：在外层 span 上加 title 和 aria-label（如 title="Seed 3 本"），icon 本体 aria-hidden="true"。
指标行（总书数 / 近7天编辑 / 近7天浏览 / 最近活动）：为每个指标 span 设置 title 和 aria-label，例如“总书数 10 本”“近 7 天编辑 3 次”“最近活动：8 小时前（2025/11/25）”。
操作列按钮：在现有 aria-label 基础上统一 title 文案，比如：
Edit: 编辑名称和标签
Pin: 置顶书橱 / 取消置顶书橱
Archive: 归档书橱 / 恢复书橱
Delete: 删除书橱（不可恢复）
确保这些 tooltip 与 a11y 约束对齐 VISUAL_RULES 和 HEXAGONAL_RULES：图标只作装饰，语义由文本 + aria 提供。
三份 RULES 文件更新（你已经给我对应，我按此补齐）

DDD_RULES.yaml
在 POLICIES_ADDED_NOV25.POLICY-BOOKSHELF-AUDIT-LIST-INTERACTIONS 下追加几行：
状态在审计列表中用纯文字 ACTIVE/ARCHIVED 展示，颜色来自前端 silk-blue / matcha-green token，Domain 不持久化任何视觉属性。
说明 PIN / ARCHIVE / DELETE / EDIT + Tag Dialog 都是走既有 UseCase，当前这轮只是交互与视觉收口。
HEXAGONAL_RULES.yaml
在 bookshelf_audit_list_action_contract 段落下增加一个小节（例如 presentation_contract）：
Adapter 只透传 DTO 字段（status, pinned, tag_ids, tags_summary, metrics），不创建额外“视觉枚举”。
明确 Lucide 图标 tooltip 文案由 UI adapter 负责，但必须与 DTO 语义对齐（比如指标单位、成熟度枚举）。
VISUAL_RULES.yaml
在 bookshelf_dashboard_layout_v2.visual_language 中补充：
PINNED 徽章仍用 --wl-pinned-accent-* pill；ACTIVE/ARCHIVED 状态在标题行右侧以纯文字呈现，ACTIVE 默认丝绸蓝（对应 silk-blue / business 主题自动切换），ARCHIVED 默认抹茶绿。
在 bookshelf_dashboard_layout_v2.accessibility 里加：
所有 Lucide 图标并非信息唯一载体，必须有可读文字 + title + aria-label。
成熟度/指标图标 aria-hidden="true"，屏幕阅读器只读文本。
ADR-097：模仿 ADR-096 的风格与路径

新建 assets/docs/ADR/ADR-097-bookshelf-dashboard-audit-list-final-polish-pin-archive-tooltips.md，结构推荐：
标题：ADR-097: Bookshelf 审计列表最终交互与视觉收口（Plan50 Final Polish）
Status: Accepted (Nov 25, 2025)
Context：说明 Layout V2 已经落地，但 PIN / ARCHIVE 视觉与 Libraries 略有偏差、tooltip 不完整，a11y 有缺口。
Decision：
PIN 使用与 Library 列表一致的丝绸蓝 token。
ACTIVE/ARCHIVED 改为纯文字 + silk-blue / matcha-green，去掉胶囊背景。
为成熟度、指标、操作列所有 Lucide icon 增补 tooltip + aria 描述。
RULES 三份文件和本 ADR 一起作为正式约束。
Rationale：统一视觉语言、提升可扫读和 a11y、一处改主题即可（tokens）。
Scope：仅改前端 Bookshelf Dashboard + 文档，不引入新端点/字段。
Non-Goals：不改枚举 / 不重新设计布局 / 不碰后端排序过滤。
UX / Layout Notes：用文字描述截图1/2 对齐后的样子（PIN 风格、ACTIVE/ARCHIVED 颜色、tooltip 示例）。
Implementation Notes：列出具体文件（BookshelfDashboardCard.tsx/.module.css、RULES 三份）和主要修改点。
Testing：快照 + 交互 + a11y 检查（比如 tab 到按钮时看到 tooltip、读屏读对）。
Rollback：如何退回旧状态 pill，而不影响后端。
References：ADR-094/095/096 + DDD/HEXAGONAL/VISUAL_RULES 各对应段。
注意事项 / 潜在坑点

Token 映射：
需要在 tokens.css 里确认 / 新增对应 --wl-status-active-text / --wl-status-archived-text，并让 silk-blue / business-blue 主题都覆盖；避免硬编码十六进制。
重复状态问题：
避免同时展示 PINNED 徽章 + ACTIVE 纯文字 + 其它状态 chip 造成信息噪音，按 VISUAL_RULES 里“ACTIVE 文案不重复渲染”微调显示逻辑。
a11y 文案的一致性：
Tooltip 的中文说明要和列表上方汇总卡片文案一致（“活跃”“减速”“趋冷”等），同时兼顾键盘用户（焦点到达时能看到、听到）。
多主题兼容：
改完状态颜色后，在暗色主题下检查对比度（至少 4.5:1），必要时通过 token 暗色变体专门调亮/调暗。
如果你愿意，下一步我可以：

先帮你把 ADR-097 的完整中文正文草稿写出来，或者
更细地列出 BookshelfDashboardCard.tsx / .module.css 里建议改动的行级说明（不直接改代码，只给你“照着写”的指引）。

//////////////////////////////////////////////////////////////////////////////////

Plan: 丝绸蓝主题下的 PIN/ARCHIVE 收口
丝绸蓝系的 PIN/状态视觉需完全复刻 Libraries 页面：PIN 徽章沿用 --wl-pinned-accent-*，ARCHIVED 相关绿色统一映射到“抹茶绿” token，并在 Bookshelf 审计列表上落实纯文字状态、Lucide tooltip、三份 RULES 与 ADR-097 的中文描述，确保设计语言与文档同步。

Steps
扫描 frontend/src/features/bookshelf/ui/BookshelfDashboardCard.tsx/.module.css 与 tokens.css，确认现有丝绸蓝/商务蓝/抹茶绿 token 并找出需要新增的 --wl-status-active-text、--wl-status-archived-text 定义。
规划组件改动：PIN/ARCHIVE/tooltip 行为、纯文字状态样式、Lucide 描述，列出确切 JSX/CSS 位置与需要触及的 hook（如 useBookshelfQuickUpdate）供实现时引用。
制定 RULES 与 ADR 更新方案：标注 DDD_RULES、HEXAGONAL_RULES、VISUAL_RULES 具体段落（POLICY-BOOKSHELF-AUDIT-LIST-INTERACTIONS、bookshelf_audit_list_action_contract、bookshelf_dashboard_layout_v2）及 ADR-097 章节框架，全部以中文叙述抹茶绿=丝绸蓝系的一部分。
输出最终中文执行清单：包括 token 对应关系、前端修改点、文档章节、ADR-097 提纲，调用者照单实现即可。