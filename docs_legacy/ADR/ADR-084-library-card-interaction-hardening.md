# ADR-084: Library Card Interaction Hardening & Silk Blue Default

Date: 2025-11-21
Status: Accepted
Authors: Frontend / Product Experience
Related: ADR-082, ADR-083, VISUAL_RULES v2.6, DDD_RULES v3.10, HEXAGONAL_RULES v1.9
Supersedes: (None) – Follows up UI workbox refactor (ADR-083)

## Context
1. Library 卡片右上角的操作图标与封面层叠不当，hover 时被绿色/紫色渐变挡住。
2. 点击“更换封面”后，上传弹层中选择文件仍会触发卡片根节点 onClick，直接跳转到 Library 页面，导致无法完成上传。
3. 卡片缺乏可点击反馈：鼠标指针维持默认箭头、键盘无法激活、focus 样式缺失，使用体验与可访问性不足。
4. 主题系统仍以商务蓝作为默认色，与最新的视觉策略（黑白中性 + 丝绸蓝点睛）不一致，需要统一默认主题。

## Forces / Drivers
- **可访问性 (A11y)**：卡片需满足键盘导航与 focus 可见性要求，符合 WAI-ARIA。
- **交互防呆**：上传等局部操作不能破坏导航流；统计逻辑只在真实跳转时记录。
- **视觉一致性**：丝绸蓝作为唯一强调色，需成为默认 data-theme 与 localStorage 回退值。
- **技术债治理**：解决冒泡/层级问题后，避免后续弹层出现同样缺陷；以规则文档固化。

## Decision
- LibraryCard 根节点仅在存在 onClick 时暴露 `role="button"` 与 `tabIndex=0`，并实现 Enter/Space 激活与 `focus-visible` 描边。
- `actionsOverlay` 与上传弹层容器添加 `onMouseDownCapture`/`onClick` 级别的 `event.stopPropagation()`；`handleActivate` 检测 overlay/dialog 输入后直接返回，杜绝误跳转。
- 使用 `setStats((prev) => …)` 更新 clickCount，并仅在成功调用 `onClick`（即真正导航）后累加，覆盖层/弹层交互不计入统计。
- `.clickable` 类引导鼠标指针、hover 阴影与压下反馈；覆盖层 `z-index` 提升到 10，使操作图标永远浮于封面之上。
- ThemeProvider、config、app/layout 等默认主题值设置为 `silk-blue`，ThemeMenu 选项顺序调整为丝绸蓝优先；tokens.css 根变量切换到黑白+丝绸蓝调色板。
- 将以上决策同步到 VISUAL_RULES、DDD_RULES、HEXAGONAL_RULES，新增 Library 卡片交互与主题默认化条目。

## Implementation Summary
Frontend:
- 更新 `frontend/src/features/library/ui/LibraryCard.tsx`，新增 `overlayRef`/`dialogRef` 防冒泡、键盘处理与统计守卫。
- 扩充 `LibraryCard.module.css`：`.clickable` 指针/outline/active 状态；封面与操作层明确 `z-index`。
- 主题相关文件：`ThemeProvider.tsx`, `shared/lib/config.ts`, `app/layout.tsx`, `ThemeMenu.tsx`, `shared/styles/tokens.css` 修改默认主题与色板。
Documentation:
- VISUAL_RULES.yaml 新增主题默认状态与卡片交互状态；
- DDD_RULES.yaml 加入 `POLICY-LIBRARY-CARD-INTERACTION`；
- HEXAGONAL_RULES.yaml 记录默认主题、库卡片集成准则。
Testing / Validation:
- 本地手动验证：hover 动作图标不被遮挡；点击上传按钮、文件输入与取消不会跳转；卡片必需时显示指针、键盘可激活；主题切换保持丝绸蓝默认。

## Alternatives Considered
1. **直接在按钮上使用 `event.stopPropagation()` 而不加 overlay 捕获**：上传弹层内其它元素（空白区域、文件输入）仍会冒泡。
2. **将统计逻辑移动到调用方**：需要改写多个调用点且易遗漏，故在组件内部集中处理更可靠。
3. **保留商务蓝为默认主题**：与新视觉目标冲突，且需要额外说明，放弃。

## Consequences
Positive:
- 上传弹层体验恢复正常，卡片交互符合预期并满足键盘与屏幕阅读器需求。
- usage stats 更真实，避免误计；未来可直接基于 clickCount 进行排序或推荐。
- 主题系统统一丝绸蓝默认值，为后续视觉规范打下基础。
Trade-offs:
- LibraryCard.tsx 逻辑更复杂，需要遵循文档策略管理事件冒泡。
- 当 onClick 缺失时卡片不再可聚焦，若未来需要静态详情需另设入口。

## Rollback Plan
若出现不可接受的回归：
1. 暂时移除事件捕获改动，恢复早期实现（保留 CSS 修复），同时禁用上传弹层入口。
2. Theme 默认可通过 env `NEXT_PUBLIC_DEFAULT_THEME=business-blue` 覆盖，或在 ThemeProvider 切回旧常量。
3. 使用 git revert 恢复 LibraryCard 与 tokens.css 相关提交，并在 VISUAL_RULES 加上临时告警。

## Future Work
- 为 LibraryCard 引入统一的“更多操作”菜单与批量选择手势。
- 将 usage stats 与后端同步，探索跨设备共享浏览数据。
- 编写 Playwright E2E 场景覆盖 hover 操作与键盘激活流程。
- 若引入更多弹层，提炼 `useStopPropagation` Hook 以减少重复样板。

## Status Links
- VISUAL_RULES: theme_default_status, library_card_interaction_status
- DDD_RULES: POLICY-LIBRARY-CARD-INTERACTION
- HEXAGONAL_RULES: theme_runtime_strategy.default_theme, ui_integration_guidelines.library_card_interaction

## References
- Plan_9_LibraryUITheme.md（丝绸蓝调色方案）
- lucide-react 图标层级问题截图（2025/11/21）
- Accessibility guidelines: WCAG 2.1 – Focus Visible (2.4.7)

## Decision Record
Accepted 2025-11-21. 生效直至 Library Stats 同步与批量操作推出的后续 ADR 替换。
