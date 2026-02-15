# ADR-122: Plan113 Maturity Detail Tabs

- Status: Accepted (Dec 2, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-111 (Maturity + timeline integration), ADR-117 (Combined view/search), ADR-118 (Resilient shell), ADR-120 (Plan111 score alignment), ADR-121 (Plan112 overview card)
- Related Artifacts: `frontend/src/app/admin/books/[bookId]/page.tsx`, `frontend/src/app/admin/books/[bookId]/page.module.css`, `frontend/src/features/book/ui/NextStepsChecklist.tsx`, `frontend/src/features/maturity/ui/MaturityScoreBreakdown.tsx`, `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`

## Problem / 背景

1. **信息链条断裂。** 评分拆解、结构任务、Chronicle 时间线、Promoted TODO 分布在多个卡片，用户需要滚动来回对照才能把“分数→行动→事件→待办”串联起来，违背 Plan113 希望的“评估面板”体验。
2. **纵向空间不足。** Plan112 单卡布局已经填满视窗，再额外堆叠结构任务/时间线/Todo 卡导致 Overview Tab 加长，移动端更难浏览。
3. **交互不一致。** Score 区域提供“查看评分构成”按钮，而其他卡片缺少同层级入口，反馈节奏断开。Product 希望所有 maturity 相关模块共享同一语境与导航模式。

## Decision / 决策

1. **启用四个二级 Tab。** 在 Plan112 概览卡底部新增 pill 风格 Tab Header，面板依次承载“查看评分构成”“结构任务”“时间线”“TODO”，默认选中 Score。任务/时间线/TODO 标签追加实时计数，帮助用户预判工作量。
2. **复用现有数据源。** 所有面板都消费既有 Hook/组件：Score 使用 `MaturityScoreBreakdown`；Tasks 使用 `NextStepsChecklist`（hideSummary=true）；Timeline 内嵌 `ChronicleTimelineList`（pageSize=10, variant='embedded'）；TODO 使用 `extractPromotedTodosFromBlocks` + `useUpdateBlockContentMutation` 勾选 Block 内容。切换 Tab 只更新前端 state，不触发额外 API。
3. **去除刷新按钮。** 依托成熟度模块自动刷新机制，移除“刷新成熟度”按钮，右上角只保留覆盖 ≥40 分时出现的人工评估入口，文案与样式沿用丝绸蓝 primary token。
4. **文档同步。** DDD_RULES 记录 Plan113 仍属 UI-only 组织并覆盖时间线/TODO；HEXAGONAL_RULES 更新 `book_maturity_detail_tabs_port`；VISUAL_RULES `overview_card_v3` 补充 Tab 布局与无刷新按钮规范。

## Consequences / 影响

- **正面：** 评分解释、行动建议、关键事件、Promoted TODO 全部汇集在同一视区，用户无需滚动即可串联“分数→行动→时间线→待办”。
- **正面：** Overview 卡片维持单容器结构且高度可控，移动端纵向长度收敛，Plan113 草图得到落实。
- **正面：** Tab header 具备 aria 语义，四个面板共享丝绸蓝视觉并保留既有交互（Score 展开、Tasks Checklist、Timeline 列表、TODO 勾选）。
- **负面：** 去掉刷新按钮后，运营若需强制刷新只能依赖后端自动任务，需要通过 CLI 或 API 手动触发；短期内需加强 snapshot 监控确保自动刷新可靠。
- **风险：** 未来若 Tab 状态需要持久化（例如每个用户记忆偏好），必须扩展前端存储或用户偏好服务，而不是把 active tab 写回 Book DTO。

## Implementation Notes / 实施

1. **Frontend:**
   - `frontend/src/app/admin/books/[bookId]/page.tsx` 新增 `detailTab` state、Tab Header、共享面板容器，并把 `NextStepsChecklist`、`ChronicleTimelineList`、Promoted TODO 列表都移入 Tab。Score 面板保留 `MaturityScoreBreakdown` 展开按钮，但文案更新为“展开/收起拆解”。
   - `frontend/src/app/admin/books/[bookId]/page.module.css` 新增 `.detailTabsRoot/.detailTabsHeader/.detailTabButton/.detailTabButtonActive/.detailTabPanel/.detailPanelSection/.detailPanelTitle/.detailPanelMeta` 等样式，沿用丝绸蓝主题色；Stage chip 颜色切换为 `var(--color-primary)`。
   - `frontend/src/features/book/ui/NextStepsChecklist.tsx` 的空态提示改为“系统自动刷新”，避免再提示点击刷新按钮。
2. **Documentation:**
   - `assets/docs/VISUAL_RULES.yaml` 更新 `overview_card_v3` 动作行与 Tab 规范，`detail_tabs` 小节覆盖 Score/Tasks/Timeline/TODO。
   - `assets/docs/HEXAGONAL_RULES.yaml` 更新 `book_maturity_detail_tabs_port`，强调 Tab 完全在 UI shell 内完成且不得触发额外 UseCase。
   - `assets/docs/DDD_RULES.yaml` 更新 `POLICY-BOOK-MATURITY-PLAN113-TABS`，重申新增 Timeline/TODO 仍不引入 Domain 字段。
3. **Testing:**
   - Playwright 需新增 Tab 切换快照；RTL 针对 Tab header aria 接口和 Score 展开按钮进行断言；手动验证移动端 Tab 排列。
