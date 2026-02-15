# ADR-097: Bookshelf Dashboard Audit List Final Polish (Pin/Archive/Tooltips)

- Status: Accepted (Nov 25, 2025)
- Deciders: Wordloom Core Team
- Context: Plan50 & Plan51 execution notes, VISUAL_RULES, DDD_RULES, HEXAGONAL_RULES, frontend bookshelves dashboard implementation
- Related: ADR-094 (Library Dashboard Theme Integration), ADR-096 (Dashboard Layout V2), ADR-095 (Compact View Upgrade)

## Context

Bookshelf Dashboard 行布局已经在 ADR-096 中确定，但真实实现中仍存在以下缺口：
- Pinned/Archived 徽章与状态列重复渲染，配色与 Library 主题未统一，暗色模式对比不足。
- 状态列仍使用徽章样式，存在语义重复；读屏用户难以理解 ACTIVE/ARCHIVED 与最近活动之间的关系。
- 行内 Lucide 图标缺乏 tooltip/aria-label 描述，指示性语义不足；成熟度/指标图标未给出数量/含义说明。
- DDD/HEX/VISUAL 三份规则尚未同步记录最终呈现方式，容易在回归期间被回滚。
- 缺少面向 Plan50/Plan51 的 ADR，无法在未来审计中追溯“纯文本状态 + token 驱动颜色 + Tooltip 合规”的来源。

## Decision

1. **Token 化状态与 Pinned/Archived**：在 `frontend/src/shared/styles/tokens.css` 中新增 `--wl-status-active-text`、`--wl-status-archived-text`、`--wl-status-muted-text`、`--wl-status-pulse-bg`、`--wl-status-pulse-border` 等跨主题变量，并将 `.pinnedBadge`/`.archivedBadge`/状态列文本全部绑定到对应 token。
2. **状态列改为纯文本**：`BookshelfDashboardCard.tsx` 仅渲染纯文本 `ACTIVE` 或 `ARCHIVED`，并附带最近活动时间；不再重复渲染徽章。Pinned 徽章仅出现在标题列，与名称同行。
3. **Tooltip 与 aria 补齐**：成熟度与指标图标、Pin/Archive/Edit/Delete 按钮统一提供中英双语 `title` + `aria-label`，并为状态文本生成 `aria-label`（示例：“ACTIVE，最近更新 3 天前”）。
4. **文档同步**：更新 DDD_RULES、HEXAGONAL_RULES、VISUAL_RULES 记录纯文本状态、token 依赖与 tooltip/a11y 要求。新增本 ADR 作为执行记录。

## Rationale

- 将状态转为纯文本可避免徽章重复，提高可读性并满足读屏顺序要求；token 控制颜色可保证多主题一致。
- Tooltip/aria label 的统一补齐可以为混合语言团队提供一致的操作提示，并为指标图标补充含义。
- 文档与 ADR 同步记录，确保未来的设计/开发/测试在复盘时有据可依。

## Scope

- Frontend：`frontend/src/shared/styles/tokens.css`, `frontend/src/features/bookshelf/ui/BookshelfDashboardCard.tsx`, `frontend/src/features/bookshelf/ui/BookshelfDashboardBoard.module.css`。
- Documentation：`assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`, 本 ADR。

## Non-Goals

- 不更改后台 DTO 字段或新增状态枚举；沿用既有 `status`, `pinned`, `archived_at`, `last_activity_at`。
- 不引入新的操作按钮或快捷键。
- 不重新设计 Dashboard 布局列宽（仍遵循 ADR-096 grid）。

## UX & Accessibility Notes

- 状态文本字体 13px，字母大写；Pinned badge 仅在名称列展示，避免视觉噪音。
- Tooltip 文案示例：`title="成熟度 Seed｜Seed stage readiness"`；指标 icon 提示 `"本周编辑 5 次｜Edits this week"`。
- 状态文本具备 `aria-label`，图标按钮提供 `aria-pressed`（Pin）与 `aria-describedby`（Delete confirm）。
- 最近活动脉冲点使用 `--wl-status-pulse-*` token，亮暗模式保持 ≥3:1 对比。

## Implementation Notes

- CSS 模块新增 `.statusLabel`（默认）、`.statusLabelArchived`（归档灰）等类，引用 token 并保证行高与指标列对齐。
- `BookshelfDashboardCard.tsx` 引入 `statusDescription` 逻辑，集中生成 tooltip、aria 文案以及状态文本。
- Tooltip 字段采用组件内常量，避免重复翻译；aria 与 title 共用描述，确保屏幕阅读器与鼠标用户一致体验。
- DDD/HEX/VISUAL 规则注明：领域模型不关心主题色，所有配色由前端 token 决定；状态列不得再渲染徽章。

## Testing

- 更新 Storybook / Jest snapshot：Pinned+Active、Archived-only、Dark mode。
- 手动验证读屏顺序：行 → 状态 → 指标 → 操作按钮；Pin/Archive 切换时 `aria-pressed`、`title` 同步更新。
- Playwright：hover Tooltip 内容，验证 `title`、`aria-label` 出现在 DOM；状态列仅渲染一次 ACTIVE 文案。

## Rollback

- 回滚可通过 `git revert` 恢复旧 CSS/TSX 与 tokens；同时撤销 DDD/HEX/VISUAL 相关段落。

## References

- Plan50 审计列表 Pin/Archive 收口 QuickLog
- `frontend/src/shared/styles/tokens.css`
- `frontend/src/features/bookshelf/ui/BookshelfDashboardCard.tsx`
- `frontend/src/features/bookshelf/ui/BookshelfDashboardBoard.module.css`
- `assets/docs/DDD_RULES.yaml`
- `assets/docs/HEXAGONAL_RULES.yaml`
- `assets/docs/VISUAL_RULES.yaml`
