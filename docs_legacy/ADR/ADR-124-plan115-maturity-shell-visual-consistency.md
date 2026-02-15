# ADR-124: Plan115 Maturity Shell Visual Consistency

- Status: Accepted (Nov 30, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-111 (Maturity score v2), ADR-118 (Resilient maturity shell), ADR-121 (Plan112 overview card), ADR-123 (Plan114 insights card)
- Related Artifacts: `frontend/src/app/admin/books/[bookId]/page.tsx`, `frontend/src/app/admin/books/[bookId]/page.module.css`, `frontend/src/features/maturity/ui/MaturityScoreBreakdown.(tsx|module.css)`, `frontend/src/features/chronicle/ui/ChronicleTimelineList.module.css`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`

## Problem / 背景

1. **视觉语言割裂。** 设计复盘（截图：Book Overview 列）显示 Score Breakdown、Usage、Timeline 三张卡片处在同一列却使用不同字号、字色与底色，QA 在验收时误判为“来源于不同模块的数据”。
2. **分值表达不统一。** Score Breakdown 仍显示原始整数或带 `+/-` 前缀的分数，而主卡和时间线都用百分比；产品希望所有贡献值在 UI 中都带 `%` 以强化“占比”心智。
3. **Usage 标签冗余。** Usage 卡已经包含 blocks/events 两行指标，再额外渲染“使用情况”字样导致内容拥挤且在移动端截断。
4. **时间线背景与主题脱节。** ChronicleTimelineList 默认白底，而成熟度 shell 使用浅灰 `#fafbfc`，两个卡片贴在一起时出现“拼色”，破坏计划 118 的 resilient shell 一致性要求。

## Decision / 决策

1. **Score Breakdown 百分比化。** `MaturityScoreBreakdown` 继续消费 `score.components[].points`，但统一格式化为 `{value}%`，同时把 Header/Group/Item 字体与 Chronicle 时间线保持 0.85rem/0.75rem secondary 字色，移除早期的虚线 hover 效果。
2. **Maturity 眉标题放大。** Hero 卡中 `MATURITY` 与 `MATURITY INSIGHTS` 眉标题字号提升至 1rem、letter-spacing ≥0.12em，维持 uppercase 与 secondary 色，Stage chip/segmented control因此获得更清晰的层级。
3. **Usage 卡只留数据。**界面层去掉“使用情况”文字，只保留 blocks/events 两行数值 + lowercase suffix；aria-label 继续提供描述以保持可访问性。
4. **时间线卡片共用 shell token。** `ChronicleTimelineList` 的 `.timelineCard` 改为 `var(--color-surface-shell,#fafbfc)` 背景，并沿用 maturity 卡的边框与 spacing，让 Overview 列看起来像同一栈。
5. **规则同步。** HEXAGONAL_RULES 增加 Plan115 UI-only 声明、VISUAL_RULES/DDD_RULES 更新字体/百分比/背景要求，确保后续不再向 Domain 请求“格式化”字段。

## Consequences / 影响

- **正面：** Overview 列中的卡片拥有一致的 shell、字体和色彩，对 QA/设计而言更容易对照 screenshot 验收。
- **正面：** 所有得分项都显式展示百分比，Curator 能立即判断各结构/活动/任务贡献占比，减少解释成本。
- **正面：** Usage 卡空间释放，blocks/events 数字在桌面与移动端都能完整展示，同时保持读屏友好。
- **正面：** 文档记录 UI-only 决策，阻止后续团队因为样式问题扩展 DTO。
- **负面：** Score Breakdown 如需展示绝对值（例如 +3）需在组件内自行拼接，无法依赖后端提供格式化字符串。
- **风险：** 后续主题切换若修改 `color-surface-shell`，Timeline/Overview 同时受影响；需要在 tokens.css 做好跨主题验证。

## Implementation Notes / 实施

1. **Frontend:**
   - `frontend/src/features/maturity/ui/MaturityScoreBreakdown.tsx` 把 `formatPoints` 输出改为百分比字符串，并复用 Chronicle 字色/字号；CSS 移除虚线 hover、收紧行距。
   - `frontend/src/app/admin/books/[bookId]/page.tsx` & `.module.css` 放大 MATURITY/MATURITY INSIGHTS eyebrow 文案，Usage 卡仅保留 blocks/events，两行 suffix 小写；Insights header/timeline link 继续触发顶级 Tab 切换。
   - `frontend/src/features/chronicle/ui/ChronicleTimelineList.module.css` 把 `.timelineCard` 背景改为 `var(--color-surface-shell,#fafbfc)`，保持与 sectionCard 一致，并确认移动端 padding 维持 24/16px。
2. **Docs:**
   - `assets/docs/HEXAGONAL_RULES.yaml` 新增 `book_maturity_shell_visual_hotfix`，标记此次修复只在 UI 层执行、禁止新增 DTO 字段。
   - `assets/docs/VISUAL_RULES.yaml` 更新 `book_maturity_visual_rules`（Usage 卡描述、格式化规则、formatting_hotfix_2025_11_30）并在 `chronicle_timeline_visual_rules` 记录背景 token 变化。
   - `assets/docs/DDD_RULES.yaml` 添加 `POLICY-BOOK-MATURITY-VISUAL-CONSISTENCY`，强调百分比/字体/背景均属于 UI-only。
3. **Testing:**
   - 手动核对 Overview Screenshot：Score Breakdown/Usage/Timeline 三卡背景一致；百分比显示在组标题与明细上无截断。
   - Visual 回归（Chromatic/Storybook 或 Playwright screenshot）对比 Score Breakdown 展开/收起 + Timeline 卡片，确保颜色/字号一致。
   - 可访问性回归：确认 Usage 卡 aria-label 仍为“使用情况”，读屏发音未受影响。
