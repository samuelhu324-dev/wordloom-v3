Plan: Plan121 Block 编辑器细化改造
TL;DR：在不破坏现有 Plan120/Hexagonal 契约的前提下，本轮只改前端 Block 编辑体验：拿掉第一个块上方的插入行、让 view/edit 使用同一套排版、把标题/段落的微编辑器改成「单行起步自动增高」、并让背景与操作图标只在 hover/编辑时轻量出现，不再造成“整块弹起”的错觉。同时在 VISUAL/HEXAGONAL/DDD 里新增 Plan121 规则段落。

Steps
梳理现状并定位受影响组件
1.1 在 BlockList.tsx 中标出：顶部「写点什么…」占位块、每个块前后的 inline + 插入行的渲染逻辑（尤其是第一个块上方的 handle）。
1.2 在 BlockRenderer.tsx 中确认 Heading / Paragraph 的 view 组件与 edit 组件结构（是否有单独的 ParagraphEditor / HeadingEditor 子组件）。
1.3 查阅 BlockList.module.css 中与标题/段落/编辑壳层相关的 class（现有 .blockHeading1、.headingTextarea、.blockItemEditing 等）以及 inline 插入行 .inlineInsertRow。
1.4 快速搜索工程内是否已有自动高度文本域或通用输入壳（如 AutoSizeTextarea、TextArea 类组件），以决定是复用还是新建组件。

去掉「第一行插入行」，但保留其余行行为
2.1 在 BlockList.tsx 里找到用于渲染行间插入行的函数（通常类似 renderInlineHandle(block, position)），看它在 map blocks 时如何被调用。
2.2 调整顶部区域：对第一个可见块（index===0），在其上方不再调用 renderInlineHandle('before')，仅保留块本身；其余块维持「每个块前后都可插入」的模式。
2.3 确认 fractional_index 计算逻辑（在 admin/books/[bookId]/page.tsx 和 admin/blocks/page.tsx 中）不依赖“第一行 handle”存在，保证删除该 UI 元素不会影响插入顺序。
2.4 检查与键盘行为（Enter 新建段落）以及 Slash 命令插入的交互是否仍然只依赖 onAddBlock，与首行 handle 解绑；如有文案/空态提示（「写点什么…」）依旧放在第一个块内而不是单独的插入行。

统一 Heading / Paragraph 的 view/edit 排版壳结构
3.1 在 BlockRenderer.tsx 中为文字类 block 抽出统一的壳组件，比如 TextBlockShell 或 HeadingShell：接收 isEditing、children 和操作图标区，内部始终使用同一块文字节点。
3.2 定义文字节点 class（例如 .block-heading-1-text、.block-paragraph-text），并保证 view/edit 两种状态都用这一套 class；编辑态仅在壳层加 modifier（如 .block-heading-shell--editing）。
3.3 在 CSS（BlockList.module.css）中：
- 为壳层新增 .block-heading-shell / .block-paragraph-shell，固定 padding、border-radius 和 border-width，默认 border-color: transparent。
- 为编辑态增加 .block-heading-shell--editing / .block-paragraph-shell--editing，仅修改 background-color、border-color、box-shadow，不改变 padding/字体大小/行高。
3.4 确认现有 .blockItemEditing 等通用编辑态 class：决定是继续使用并内部转发到壳层，还是用更细粒度的新 class 取代；避免重复叠加导致视觉过重。
3.5 调整 Heading / Paragraph 的 view/edit 实现：移除编辑态时额外套用的专用文本 class（如 .headingTextarea 若和 view 样式冲突），改为在文字节点上只使用一个统一 class，通过 font: inherit 等方式保证一致性。

实现「单行起步 + 自动高度上限三行」的微编辑器
4.1 新建一个通用的自动高度文本组件（例如 frontend/src/shared/ui/AutoSizeTextarea.tsx 或放在 features/block/ui 内的 AutoSizeTextarea），只负责：
- 接收 value、onChange、className 等常规 props；
- 内部通过 useLayoutEffect 或 ResizeObserver 在 value 变化时重置高度为 0，然后根据 scrollHeight 计算真实高度；
- 把高度限制在「单行高度 × 3」以内（行高可从 CSS 变量或 props 注入）。
4.2 在该组件的 textarea 上使用 rows={1} 并在 CSS 中设置：width:100%、resize:none、overflow:hidden、border:none、background:transparent、font:inherit、line-height:inherit、padding:0。
4.3 将 Heading / Paragraph 编辑态中原有的 textarea 或 contentEditable 改为使用 AutoSizeTextarea（可分别传入不同的 class，例如 .heading-input、.paragraph-input，但其字体相关属性都通过 inherit 自父节点）。
4.4 调整现有 CSS：删除或缩小为「三行高度」的 min-height 设置，改由 JS 控制高度上限；避免在 CSS 再写死 height: 72px 之类的值。
4.5 在 BlockRenderer 内部，保证 AutoSizeTextarea 与当前 focus / selection 管理兼容（例如 Slash 菜单光标位置逻辑）：检查依赖 onKeyDown / selectionStart 的代码能在新组件上透传正常运行。

让图标和背景「贴边」且只在 hover / edit 时出现
5.1 在 TextBlockShell 或 HeadingShell 中为操作按钮区域提供固定包裹元素（如 <div className="block-heading-actions">），由壳负责 position: relative。
5.2 在 CSS 中：
- .block-heading-actions / .block-paragraph-actions 设置 position:absolute; top:4px; right:6px; display:flex; gap:4px; opacity:0; pointer-events:none;；
- 通过 .block-heading-shell--editing .block-heading-actions 和 .block-heading-shell:hover .block-heading-actions 将 opacity 切到 1 并打开 pointer-events。
5.3 校验当前图标布局（时钟、删除等）是否由 BlockItem 外层控制，如果是，则在 BlockItem 中只渲染图标内容本身，把对齐/显隐交由壳层 class 控制，避免双重布局。
5.4 确保壳层的高度完全由文字内容决定：图标采用绝对定位后不占据行高，不会推高第一行或挤压文字。
5.5 在其它 BlockKind（如 todo/callout/quote）上复用同样模式或确认是否需要保持不同视觉；至少保证它们不会在 hover 时突然增高。

更新规则文档与 ADR 以记录 Plan121 决策
6.1 在 VISUAL_RULES.yaml 中新增 block_editor_plan121_micro_editor（名称可按现有风格）条目，写入：
- 「Heading / paragraph view/edit 字体与行高一致」
- 「Block shell 透明边框占位，不因编辑态改变布局」
- 「微编辑器默认 1 行高度，自动增长但最多 3 行」
- 「背景与图标仅在 hover / edit 显示，图标绝对定位不影响行高」等硬约束。
6.2 在 HEXAGONAL_RULES.yaml 中补充对 Plan121 的一句说明：
- 明确这是 UI-only 迭代，不新增 UseCase/端口；
- 强调 Create/UpdateBlockUseCase 契约未变，Block 内容仍为 JSON，AutoSize 逻辑完全在前端。
6.3 在 DDD_RULES.yaml 的 POLICIES_ADDED_DEC01 下增加一个 POLICY-BLOCK-PLAN121-MICRO-EDITOR，说明：
- 本次改动仅限 Block 聚合的展示与编辑外壳；
- 禁止为了解决“弹一下”问题修改 Block/Book 聚合结构或额外持久化 view/edit 状态。
6.4 视需要在 ADR 中新增 ADR-129-plan121-block-editor-micro-editor-refinement.md，记录：问题背景（截图）、决策（四条规则）、以及与 Plan120/Plan118 的关系。

Further Considerations
建议在实现后用一轮手动回归：分别在 Book 页面和 Blocks Debug 页面验证首行无插入行、view/edit 几乎无抖动、长标题/长段落在三行内自动增高。
若后续需要做自动化测试，可优先在 BlockRenderer 层加 Vitest 渲染测试（检查 class 是否随 isEditing 切换），以及一两个 Playwright 场景测试「点击标题不抖动」。