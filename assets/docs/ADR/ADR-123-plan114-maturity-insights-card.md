# ADR-123: Plan114 Maturity Insights Card

- Status: Accepted (Dec 3, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-111 (Maturity score v2), ADR-118 (Resilient maturity shell), ADR-121 (Plan112 overview card), ADR-122 (Plan113 detail tabs)
- Related Artifacts: `frontend/src/app/admin/books/[bookId]/page.tsx`, `frontend/src/app/admin/books/[bookId]/page.module.css`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`

## Problem / 背景

1. **双层 Tab 语义冲突。** Overview 顶部提供“概览/块编辑”一级模式，但卡片内部又出现一条全宽 tab（评分/任务/时间线/Todo），两个导航同时包含“时间线”导致用户难以区分层级。
2. **时间线定位分散。** Timeline 既在顶部主 tab，又在概览卡片重复展示一份嵌入式列表；维护两套入口增加视觉噪音且无法突出“完整时间线”视图。
3. **Insights 内容冗长。** 四个面板需要共享同一容器，Timeline 列表高度远大于 Score/Tasks/Todo，导致整个概览卡片被拉长，移动端滚动成本高。

## Decision / 决策

1. **保留单一顶级 Tab 列表。** 页面顶层 tab 固定为 Overview / Blocks / Timeline；Timeline 专属视图仅在顶级 tab 呈现，概览卡片不再嵌入独立时间线列表。
2. **引入 Maturity Insights 卡片。** 概览卡片新增“评估 · Maturity insights”区块，右上角提供轻量 segmented control（Score/Tasks/TODO）。控制项体积小于顶级 tab，视觉上明确为局部切换。
3. **视图内容复用既有组件。** Score 视图渲染 `MaturityScoreBreakdown`；Tasks 视图沿用 `NextStepsChecklist(hideSummary)` 并在标题下方显示阶段/完成度；TODO 视图继续展示 promoted todos 列表并允许 checkbox 写回 Block 内容。
4. **时间线链接仅切换 Tab。** Insights 卡片右上角提供“查看完整时间线”链接，点击后调用同一前端 state 切换至 Timeline 顶级 tab，而不是加载额外数据或调用新端点。
5. **文档同步。** HEXAGONAL_RULES、VISUAL_RULES、DDD_RULES 新增 Plan114 描述，记录 segmented control/顶级 Tab 分工以及 UI-only 约束。

## Consequences / 影响

- **正面：** 页面只剩一条真正的一级导航，Timeline 入口集中，信息层级清晰。
- **正面：** Maturity insights 卡片高度可控，移动端滚动显著减少；Score/Tasks/Todo 均保持在同一容器内。
- **正面：** 交互逻辑更贴近“卡片过滤”模式，阅读成本低，且依旧复用原有 hooks/组件，无需改动 Domain。
- **负面：** Timeline 仅在顶级 tab 渲染，Overview 中不再显示最近事件，需要用户点一次链接；不过 core metrics 卡仍展示最近活动。
- **风险：** segmented control 若误触发新的 API 请求会破坏 UI-only 原则；需持续审查，确保仍复用 maturity snapshot 与 TODO helper。

## Implementation Notes / 实施

1. **Frontend:**
   - `frontend/src/app/admin/books/[bookId]/page.tsx` 删除 detailTab state，新增 `insightsView` segmented control，添加 Timeline 顶级 tab，Insights 视图复用 Score/Tasks/Todo 组件，并在 header 提供“查看完整时间线”按钮。
   - `frontend/src/app/admin/books/[bookId]/page.module.css` 去除旧 `.detailTabs*` 样式，新增 `.insightsCard/.insightsSwitch/.timelineLink/.timelineTab` 等样式，保持与 Overview 主卡一致的视觉节奏。
2. **Docs:**
   - `assets/docs/HEXAGONAL_RULES.yaml` 更新 `book_maturity_detail_tabs_port` 条目，说明 Plan114 segmented control + 顶级 Timeline Tab 约束。
   - `assets/docs/VISUAL_RULES.yaml` 在 `overview_card_v3` 下记录 Insights 卡片布局/交互，移除老版二级 Tab 描述。
   - `assets/docs/DDD_RULES.yaml` 增补 `POLICY-BOOK-MATURITY-PLAN114-INSIGHTS`，强调该变化仍是 UI-only，不得新增领域字段。

3. **Testing:**
   - 手动验证三种 Insights 视图与顶级 Timeline Tab 切换；后续需要补充 RTL/Playwright 覆盖 segmented control 的 aria 表现与 TODO 勾选写回。
