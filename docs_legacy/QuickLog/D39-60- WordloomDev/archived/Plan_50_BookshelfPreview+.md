我先给你一个这轮“Bookshelf 审计列表交互版”的中文 TODO 计划，然后你可以按这个计划分几次推进（或交给我下一轮逐块实现）。

---

### 2025-11-25 快速进展（中文）

1. `/admin/tags` 目录页升级为可创建 / 编辑 / 恢复的完整 CRUD：补齐 `restoreTag` API&hook、列表操作列、中文表单和 Toast 提示，顺手把 ACTIVE pill 改到顶部按钮区。
2. Bookshelf 审计列表的标签区去掉色点，仅保留文本 chip，并把 ACTIVE 徽标与 PINNED/ARCHIVED 一起放在名称上方，视觉对齐 Library 模块。
3. 待续：a) duplicate tag 冲突 toast（LibraryMainWidget → resolveTagId）；b) 默认标签种子/筛选；c) 文档同步（RULES、ADR-096）；d) Basement 书橱流程复核。

---

一、交互激活层 TODO（建议优先级最高）

PIN 置顶按钮接线

在 BookshelfDashboardCard.tsx 的 actions 数组里：
为 handler: onPinToggle 衔接实际 hook/useCase（例如 usePinBookshelf）。
实现 onPinToggle(item)：发送 PATCH /bookshelves/{id} 或已有端点，成功后触发 Dashboard/List 的 refetch 或本地状态更新。
改进 UI：按钮 hover/pressed 状态与 Library 列表的 PIN 一致，aria-pressed 反映 pinned 状态。
ACTIVE / ARCHIVED 状态切换

域模型/DTO：
UI 文案统一为 ACTIVE 和 ARCHIVED（不再显示 FROZEN），DTO 字段仍可使用 status: 'active'|'archived'。
在 card actions 中添加一个状态切换按钮或复用现有 Archive 按钮：
ACTIVE → ARCHIVED 调用 Archive 用例。
ARCHIVED → ACTIVE 调用 Restore 用例。
成功后刷新列表或直接更新本地 item.status 字段。
行点击 / ACTIVE pill 导航

在 BookshelfDashboardCard 最外层 <div className={styles.row}> 上：
注入 onClick：调用一个 onOpen 回调或直接使用 router.push(/admin/bookshelves/${item.id}) 之类。
加 role="button" + tabIndex={0}，并在 onKeyDown 里处理 Enter/Space。
状态 pill（ACTIVE）点击：
直接复用行点击逻辑（内部 onClick={handleRowClick}），但 stopPropagation 不要阻断。
删除按钮接线

在 actions 中为 Delete 绑定 onDelete(item)：
弹出确认对话框（可以沿用 Library 列表的删除确认组件）。
确认后调用 DeleteBookshelf 用例，成功后从 Dashboard/List 的数据源中移除该行。
二、视觉对齐 TODO（状态/标签样式）

ACTIVE / ARCHIVED pill 视觉统一

ACTIVE：
直接复用 Library 列表 PINNED 的 CSS：高度、字体大小、圆角和“丝绸蓝”色（--wl-pinned-accent-* token）。
ARCHIVED（原 FROZEN）：
新设抹茶绿 token，例如：
--wl-archived-accent-bg: rgba(34,197,94,0.12)
--wl-archived-accent-text: #16a34a
Pill 大小与 ACTIVE 一致。
Tag chip 与 Library 列表统一

把 BookshelfDashboardCard 里的 .tagChip/.tagChipMore/.tagsEmpty 样式改成：
高度和圆角、边框颜色、字体大小全部参考 Library 标签那套样式（LibraryList 使用的 chip CSS）。
若 Library 有公共 chip class（例如 .tagPill），可以直接在 Bookshelf 复用。
三、Tag 编辑 TODO

简单 Tag 编辑对话框

新建组件 BookshelfTagEditDialog（路径建议：frontend/src/features/bookshelf/ui/BookshelfTagEditDialog.tsx）：
Props：bookshelf: BookshelfDto，open，onClose，onSaved.
内容：
书橱名称输入框（可编辑）；
Tag 选择区：从全局 Tag 列表下拉选择多个标签（或简单多选 checkbox 列表），支持删除。
提交时：
调用 UpdateBookshelf 用例，传 { name, tags }。
成功后 onSaved(updated)，关闭对话框并让列表用新数据替换。
行内编辑入口

在 BookshelfDashboardCard 的“编辑”图标按钮上：
打开上述 BookshelfTagEditDialog。
BookshelfDashboardBoard 或 BookshelfList 层维护一个 editingItem 状态，用于控制对话框显隐。
四、文档 TODO（等交互跑通后）

RULES 同步

DDD_RULES.yaml：新增 Bookshelf 审计列表策略，写明列顺序、操作只通过 UseCase、成熟度/统计来源。
HEXAGONAL_RULES.yaml：更新 bookshelf_dashboard_layout_v2 和 bookshelf_audit_list_port_v1，列出端口字段与行为。
VISUAL_RULES.yaml：补 bookshelf_audit_list_v1，定义 grid 列、Tag chip、ACTIVE/ARCHIVED pill、图标 tooltip。
ADR-096 更新

在 ADR-096-bookshelf-dashboard-layout-v2-and-action-column.md 中：
加入这次最终布局截图描述；
明确 Pin/Archive/Delete/Tag 编辑/导航交互；
标记本次为 V2 完成版。
如果你愿意，下一轮我可以直接从“交互激活层 TODO”（1–4 点）开始，在代码里逐条接上线，然后再回到 5–8 做样式和 Tag 编辑。