# ADR-119: Book Maturity Summary Parity & Spacing

- Status: Accepted (Nov 30, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-096 (Bookshelf dashboard layout v2), ADR-117 (Combined View/Search), ADR-118 (Resilient shell)
- Related Artifacts: `frontend/src/widgets/book/main-widget/maturity.tsx`, `frontend/src/widgets/book/BookMainWidget.module.css`, `frontend/src/widgets/book/BookMainWidget.tsx`

## Problem

1. **Empty-state SummaryBar 断裂。** 截图 1（完成度 0%）显示 SummaryBar 被强制换成纵向栈：进度条与计数 pill 被拉开，hint 文案夹在左侧，导致 Bookshelf Detail 的视觉与 Library Dashboard 脱节。
2. **Row List/空态间距不一致。** 当 maturity section 内没有条目时，`BookRowCard` list 上方没有留白，而有数据时存在 `var(--spacing-lg)` 的间距，造成同一页面里“SEED”标题忽大忽小（截图 2 为期望状态）。
3. **Heading/控件重复。** 当 BookMainWidget header 被 portal 到父级布局之后，Widget 内部仍会渲染一次“该书架的书籍”，出现重复标题与额外空白。
4. **文档缺口。** 三份 RULES 未描述 SummaryBar 的空态布局、Row List 的统一留白以及 heading portal 的约束，后续维护者容易再次回退到 Screenshot 1 的实现。

## Decision

1. **SummaryBar 保持单一布局。** `summaryBar` flex container 不再因为 `data-empty=true` 切换成 column，而是保持与有数据时相同的横向排列，仅让 hint 占用 `flex-basis: 100%` 另起一行。
2. **空态间距对齐。** `.rowList` 与 `.sectionEmpty` 均固定 `margin-top: var(--spacing-lg)`，Combined View 的 empty state 也重用该留白，从而让“SEED”标签与内容之间的距离在空/有数据时保持一致。
3. **Heading portal 单一来源。** BookMainWidget 的 heading intro 仅在本组件独立渲染时展示；当父级（例如 Library detail 顶部）通过 portal 提供 heading 与控件时，内部 heading 自动隐藏。
4. **规则同步。** 把上述约束写入 DDD_RULES `POLICY-BOOK-MATURITY-SUMMARY-PARITY`、HEXAGONAL_RULES `book_maturity_summary_parity`、VISUAL_RULES `book_maturity_view_v2.header_bar/sections`，防止后续热修复偏离合同。

## Consequences

- **正面：** 无论书籍数量多少，SummaryBar 与 Library Dashboard 共享相同的视觉节奏，Screenshot 2 成为唯一形态，减少设计与前端的对齐成本。
- **正面：** Row mode/空态间距一致，运营在“只有 Legacy”或“刚创建书架”场景下不会再看到跳动的版面。
- **正面：** Heading 与控件来源唯一，Bookshelf workspace 的无障碍语义更干净，ARIA 层级也更稳定。
- **负面：** SummaryBar 现在依赖 CSS 来处理 hint 换行，维护者需要谨慎调整 flex 属性；若未来引入更多计数 pill，需重新评估 hint 的断行方式。
- **负面：** 旧的截图（Screenshot 1）不可再作为回归参考，需要更新测试基准与设计规格。

## Implementation Notes

1. **CSS 调整：**
   - `BookMainWidget.module.css`：`summaryBar[data-empty]` 仍为 `flex-direction: row`，hint 元素新增 `flex-basis: 100%` + `margin-top`；`.rowList` 与 `.sectionEmpty` 共享 `margin-top: var(--spacing-lg)`。
2. **组件收敛：**
   - `BookMaturityView` 仍然根据 `counts.total` 设置 `data-empty` 但不渲染不同 DOM；`booksHeading` 仅在 `combinedView && headingSlotAbsent` 时显示，避免重复。
3. **Documentation/Test：**
   - 更新 DDD/Hex/Visual RULES 对应章节，要求 SummaryBar/RowList 空态保持 parity，并把“heading portal 单一来源”写入 header_bar 部分。
   - 补充 Vitest/RTL 覆盖：counts.total=0 场景下 Snapshot AST 未发生结构变化，仅 text 改动；Playwright 基线截图更新为 Screenshot 2 样式。

> Screenshot 1（空态混乱）与 Screenshot 2（期望态）提供了前/后对比，ADR-119 记录的规则以 Screenshot 2 为唯一参考实现。
