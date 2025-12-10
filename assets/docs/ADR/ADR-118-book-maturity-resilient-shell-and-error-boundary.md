# ADR-118: Book Maturity Resilient Shell & Error Boundary

- Status: Accepted (Nov 30, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-072 (Book maturity segmentation rollout), ADR-096 (Bookshelf dashboard layout v2), ADR-117 (Combined filter/search), DDD_RULES `POLICY-BOOK-MATURITY-RESILIENT-SHELL`, HEXAGONAL_RULES `book_maturity_resilient_shell`, VISUAL_RULES `book_maturity_view_v2.resilient_shell`
- Related Artifacts: `frontend/src/widgets/book/BookMainWidget.tsx`, `frontend/src/widgets/book/main-widget/maturity.tsx`, `frontend/src/shared/ui/ErrorBoundary.tsx`

## Problem

1. BookMaturityView 同时承载 SummaryBar、阶段列表、Header slot（视图切换 + FilterBar）以及 Search feedback，一旦组件内部语法 / runtime 出错，React 会卸载整棵 BookMainWidget，导致筛选、创建书籍、全局搜索全部消失。
2. 复用 slot 的方式把 header/filter/search DOM 节点塞进 maturity 组件深处，任何结构性改动都难以测试，也不符合“控件与数据展示分层”的治理目标。
3. 缺乏 ErrorBoundary/Fallback 机制，调试阶段的语法错误（例如 jsx fragment 拼写）会直接把 Bookshelf 页面打成 React 红屏，运营无法继续工作。
4. 文档没有规定成熟度壳层的职责，容易再次出现“把控件塞进 maturity 组件”“组件内部发起额外 API”等违规实现。

## Decision

1. **拆分壳层。** BookMainWidget 负责渲染 Header（视图切换 + 新建）、Filter/Search 工具条与 SearchResultSheet；BookMaturityView 仅负责 SummaryBar + sections。两者之间只通过 `snapshot`/`hiddenSections`/`searchMeta` 等展示型 props 交互。
2. **引入共享 ErrorBoundary。** 在 `frontend/src/shared/ui/ErrorBoundary.tsx` 新增可复用的 Class 组件，BookMainWidget 将 BookMaturityView 包裹其中，fallback 告知用户“成熟度视图加载失败，但筛选/搜索仍可继续”，并提供重试按钮。
3. **限制 props & 重置策略.** BookMaturityView 不再接受 header slot，也不得在内部读取 TanStack Query。ErrorBoundary `resetKeys=[bookshelfId,totalCount,orderPreset,searchText]`，确保数据变化/筛选切换时自动清空错误状态。
4. **文档治理。** 在 DDD/Hexagonal/Visual RULES 中写明解耦与降级策略，后续任何想要扩展 maturity 视图的需求都必须沿用该壳层结构。

## Consequences

- **正面：** 即使 maturity 组件崩溃，运营仍然可以使用筛选、全局搜索、创建书籍等功能；fallback 提供即时反馈并允许重试，降低停机时间。
- **正面：** Header/Filter/Search 和 maturity 渲染逻辑分离，结构更清晰，测试/重构更容易，未来可以单独替换 maturity 视图而不影响工具条。
- **正面：** 新的 ErrorBoundary 可在其它高风险 UI（Block editor、Search 结果卡片）复用，逐步提升前端容错能力。
- **负面：** 需要维护额外的样式/状态（fallback、resetKeys），并在每次新增 props 时确认不会破坏解耦约束。
- **负面：** ErrorBoundary 只能捕获 render 阶段错误，仍需在 effect/async 场景中显式处理异常。

## Implementation Notes

1. **Component split:**
   - `BookMainWidget.tsx` 渲染顺序：Header → FilterBar/ResultSheet → `<ErrorBoundary>` → `BookMaturityView` → Dialogs。
   - `BookMaturityView` 删除 `headerSlot` prop，并保证只依赖 `snapshot`, `isLoading`, `viewMode`, `hiddenSections`, `searchMeta`。
2. **ErrorBoundary contract:**
   - Class 组件记录 `hasError` + `error`，`getDerivedStateFromError` 更新状态，`componentDidCatch` 打印日志。
   - 支持 `fallback` 为 ReactNode 或函数（获取 `error` 和 `reset`）。`resetKeys` 对比发生变化时自动调用 `reset()`。
3. **Fallback UX:**
   - 样式 `BookMainWidget.module.css .maturityError`：柔和红色背景 + 重试按钮。
   - 文案提示“异常已记录，仍可使用上方筛选与全局搜索”，按钮 `onClick={reset}` 触发重渲染。
4. **Telemetry & Testing:**
   - Console 记录 `[ErrorBoundary] captured error`，后续可接入 Sentry。
   - 新增 Vitest/RTL 用例：模拟 BookMaturityView 抛错 → fallback 渲染 → 点击“重试”恢复。
   - Playwright 场景：触发开发者模式的报错时，确认 FilterBar + SearchResultSheet 仍可交互。
5. **Documentation:**
   - DDD_RULES 增加 `POLICY-BOOK-MATURITY-RESILIENT-SHELL`，Hexagonal/VISUAL RULES 分别描述端口职责与 UI 布局/交互，防止回退到 slot 注入模式。
