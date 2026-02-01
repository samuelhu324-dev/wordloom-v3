# ADR-121: Plan112 Book Maturity Overview Card

- Status: Accepted (Dec 1, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation + UI overhaul), ADR-111 (Maturity + timeline integration), ADR-117 (Combined view/search), ADR-118 (Resilient shell), ADR-119 (Summary parity), ADR-120 (Plan111 score alignment)
- Related Artifacts: `frontend/src/app/admin/books/[bookId]/page.tsx`, `frontend/src/app/admin/books/[bookId]/page.module.css`, `assets/docs/VISUAL_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`

## Problem / 背景

1. **Overview 区域信息密度失衡。** 原有“成熟度卡 + 计数泡泡 + STABLE Chip”布局重复传播 maturity stage，却遮蔽 Plan111 的结构/活跃/照护洞察，且无法容纳 Product 提出的“核心指标”对比视图。
2. **Score 细节触达路径不统一。** MaturityScoreBreakdown 与 Structure Tasks 卡片之间重复呈现得分拆解，使用者难以判断两个区域的权责，导致运营回溯问题时仍需查 CLI。
3. **RULES 缺乏 UI-only 约束。** Plan111 上线后，DDD/VISUAL/HEXAGONAL 仍描述老布局，开发者倾向在 Domain 层添加 narrative/summary 字段支撑 UI，破坏“UI 自行组合 copy”原则。

## Decision / 决策

1. **采纳 Plan112 布局。** 成熟度概览卡合并为单一容器：顶部展示 stage headline + narrative + progress bar；主体分为三张核心指标卡（结构/活跃/照护）并显示最新活动；底部保留一键展开的 Score Breakdown 按钮。
2. **彻底移除 Chip 与计数泡泡。** STABLE/Seed/Growing 等标签改为 narrative + stage icon，所有“过去 30 天编辑/访问”统计并入核心卡片，避免重复；Structure Tasks 卡片不再渲染 score breakdown。
3. **明确 UI/Domain 边界。** 新文案、核心指标顺序、CTA 行为全部在前端派生，DDD 记录“Plan112 仅消费既有 BookDto 字段”；HEXAGONAL 引入 `book_maturity_overview_card_port` 标记此改动属于 UI shell；VISUAL RULES `overview_card_v3` 规定布局、间距、焦点次序和辅助说明。
4. **可访问性标准同步。** Progress bar、核心卡片、Score Breakdown 按钮遵循 token 对比和键盘顺序；Narrative copy 必须描述阶段含义 + 下一步建议，替代原来的装饰性 Chip。

## Consequences / 影响

- **正面：** 书籍成熟度状态、结构/活跃/照护指标在同一视野内，运营无需滚动即可获知主段指标与最新活动；Score Breakdown 的入口统一在主卡按钮，减少认知跳转。
- **正面：** 文案与布局完全在 UI 层派生，数据合同无需变更，Plan111 输出可直接复用；RULES+ADR 记录防止后续无意识回退到多卡布局。
- **正面：** Chip/泡泡删除后，前端遵循 Plan112 视觉节奏，与 VISUAL RULES 的 grid/spacing/contrast 要求一致，暗色/亮色主题表现统一。
- **负面：** 结构任务卡不再展示 score breakdown，历史截屏说明必须更新；QA/Playwright 需要刷新基线截屏与可访问性脚本。
- **风险：** Plan112 narrative 全部在客户端拼接，若翻译资源缺失会出现 fallback 英文，需要 localization pipeline 快速补全。

## Implementation Notes / 实施

1. **Frontend:**
   - `frontend/src/app/admin/books/[bookId]/page.tsx` 引入 `overviewStats` helper、核心卡片渲染、Score Breakdown toggle；`page.module.css` 新增 `.maturityTop`, `.coreCardsGrid`, `.coreCard`, `.scoreDetailsTrigger` 等样式并清理旧 `.metricsCounters`。
   - `MaturityScoreBreakdown` 仍负责渲染 Plan111 组件，但只由主卡按钮触发；Structure Tasks 卡移除 score toggle。
2. **Documentation:**
   - `assets/docs/VISUAL_RULES.yaml` 新增 `overview_card_v3` 描述布局、CTA、spacing、accessibility。
   - `assets/docs/HEXAGONAL_RULES.yaml` 添加 `book_maturity_overview_card_port`，声明 UI-only 改动与数据来源。
   - `assets/docs/DDD_RULES.yaml` 加入 `POLICY-BOOK-MATURITY-PLAN112-UI-ONLY`，强调 narrative/metrics 由前端派生，不引入新 Domain 字段。
3. **Follow-up:**
   - 更新 Playwright/RTL 截屏与断言以覆盖单卡布局、核心指标卡顺序、Score Breakdown 按钮行为。
   - Release note（BOOKSHELF_CREATION_FIX_SUMMARY_NOV20.md 下一篇章）记录 Plan112 生效日期及对运营的操作提示。
