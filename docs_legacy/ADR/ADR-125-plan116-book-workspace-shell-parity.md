# ADR-125: Plan116 Book Workspace Shell Parity

- Status: Accepted (Dec 4, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-099 (Book workspace tabs integration), ADR-111 (Maturity + timeline integration), ADR-117 (Book maturity combined view), ADR-124 (Plan115 maturity shell visual consistency)
- Related Artifacts: `frontend/src/app/admin/books/[bookId]/page.tsx`, `frontend/src/app/admin/books/[bookId]/page.module.css`, `frontend/src/features/book/ui/NextStepsChecklist.(tsx|module.css)`, `frontend/src/features/maturity/ui/MaturityScoreBreakdown.(tsx|module.css)`, `frontend/src/features/block/ui/BlockList.tsx`, `assets/docs/VISUAL_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`

## Problem / 背景

1. **Shell 视觉漂移。** Overview → Blocks → Chronicle 三个 Tab 在 Screenshot #1 中应复用同一 sectionCard（16px 圆角 + 1px subtle border + 24px padding），但实际实现出现 spacing/边框/背景不一致，QA 难以比对设计稿，也破坏 Plan118 "resilient shell" 目标。
2. **Tab 与胶囊排版割裂。** Overview Pill tabs（Overview/Blocks/Chronicle）字重与 letter-spacing 与 hero 区不一致，结构任务/Chronicle pill 也未同步总体 token，导致 Shell 看起来像两套系统。
3. **无谓的领域噪音请求。** 由于壳层未对齐，有人提议在 DTO 中加入 `shell_section_order`、`structure_task_shell_state` 字段辅助渲染。若不明确本迭代纯属 UI，未来可能重复扩展领域合同解决纯视觉问题。

## Decision / 决策

1. **统一 sectionCard。** Overview hero、Score/Usage/Timeline 卡、Structure Tasks、Blocks Tab 主容器全部复用 `styles.sectionCard`（16px radius、1px subtle border、var(--color-surface-shell,#fafbfc) 背景），Spacing token 固定（外侧 32px gutter，卡间 24px），避免单独的 css hack。
2. **Tabs 与 pills 采用 Plan116 字体栈。** Overview/Blocks/Chronicle Tab ribbon 与结构任务 pills 字重锁定：active=600、inactive=500，letter-spacing 0.02em，字号 0.95rem；Segmented control/Chronicle pill 也 adopt 同一 token，所有字体/颜色记录在 `book_workspace_tabs_visual_rules` + `book_workspace_shell_parity` 中。
3. **确认 UI-only 范围。** HEXAGONAL_RULES + DDD_RULES 记录 Plan116 不引入任何新的端口或 DTO 字段；Structure Tasks 计数、Chronicle pill 值仍由既有 snapshot/chronicle 端口提供的原始数字，所有组合、副本、aria-label 由 UI 负责。

## Consequences / 影响

- **正面：** Book workspace 任一 Tab 打开都呈现统一壳层，截图验收对齐 Screenshot #1；后续主题切换只需更新 tokens 即可联动全部卡片。
- **正面：** Tab/pill 字重统一后，用户能更快识别当前视图；结构任务/Chronicle CTA 与 hero 区信息增益一致，降低误点。
- **正面：** 通过文档申明 UI-only，阻止团队为了视觉差异扩展领域合同；未来排版问题直接更新 VISUAL/HEXAGONAL/DDD 三份规则即可。
- **负面：** 所有壳层都依赖相同 CSS token，若主题故障（token 缺失）会影响整页；需要增加视觉回归监控。
- **风险：** Blocks Tab 现有 sectionCard 包裹 BlockList，未来若引入虚拟滚动需确保卡片 padding 不被动态宽度影响。

## Implementation Notes / 实施

1. **Frontend：**
   - `frontend/src/app/admin/books/[bookId]/page.module.css` 新增 `sectionCard`, `shellGrid`, `shellTabs` 等样式，复用 `var(--spacing-lg)` + `--color-border-subtle` token；Blocks Tab wrapper/Structure Tasks/Chronicle CTA 改为这些类。
   - `page.tsx` 清理内联 spacing，把 Overview hero、Structure Tasks、Blocks Tab、Chronicle CTA 都包裹在 `sectionCard`，Tab ribbon className 更新为 `styles.shellTabs`；Structure Tasks 计数使用 UI helper（completed/total）并在 `NextStepsChecklist` 旁渲染 pills。
   - `frontend/src/features/book/ui/NextStepsChecklist.(tsx|module.css)` 注入分隔线 + spacing token，标题/pill 字号/字重匹配 Plan116；`MaturityScoreBreakdown` / `ChronicleTimelineList` 保持 Plan115 百分比/背景规则。
2. **Docs：**
   - `assets/docs/VISUAL_RULES.yaml` 添加 `book_workspace_shell_parity`（layout/typography/a11y）和 tabs 字重条目；`assets/docs/HEXAGONAL_RULES.yaml` 标明 Plan116 复用现有端口；`assets/docs/DDD_RULES.yaml` 增补 POLICY-BOOK-WORKSPACE-SHELL-PARITY-PLAN116，声明 UI-only。
3. **Testing：**
   - Storybook/Chromatic：Book Detail Overview + Blocks Tab screenshot 对比，确保卡片 radius、边框、spacing 一致，Tabs active/inactive 字重正确。
   - Playwright：切换 Overview/Blocks/Chronicle 验证无额外网络请求且 tab 状态在 localStorage 恢复正常；结构任务 pills 的 aria-label 描述可被读屏读取。
   - Manual：按 Screenshot #1 checklist 复核卡片顺序、padding、tab ribbon 高度；QA 标记 shell parity 验收项。
