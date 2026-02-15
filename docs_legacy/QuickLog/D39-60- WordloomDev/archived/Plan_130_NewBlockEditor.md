先确认一下理解：你要的是「看起来像一整篇流文档、几乎感觉不到块存在，但内部仍是 block editor」，关键目标是：

打开/关闭任何块编辑都不导致布局抖动、没有覆盖层弹跳。
DOM 结构稳定，不做大规模 mount/unmount，最大限度减少 React 重排。
结合现在 modules/book-editor 的插件体系，重新设计一版「inline contentEditable 风格」的 BlockEditor。
下面我给一份「中文整体改造计划」，分成：总体思路 → 结构层改造 → 交互和视觉规则 → 技术实现要点 → 分阶段落地。

一、总体思路：流文档壳层 + 块级语义 + 行内编辑

用一句话概括目标：

在 DOM 和数据层保持 Block（段落、标题、Todo、图片…）的聚合边界，但在视觉和交互上让用户感知到的是「一整页连续文档」，任何编辑都像在一个大 contentEditable 里打字。

核心原则：

DOM 始终是「一列 block 容器」，不使用 overlay、modal、portal 作为主要编辑载体。
每个 block 的「view / edit」使用同一套布局壳层，仅切换内部元素的可编辑性（input / textarea / contentEditable）和辅助控件显隐。
所有「工具条 / 操作按钮 / 菜单 / slash menu」都贴近文本、且只在局部、短暂出现，不推开文本、不撑高行距。
selection / caret 逻辑局部化：只在需要锚定 UI（slash menu、悬浮工具条）时监听 selectionchange，监听周期和作用域严格收敛。
二、结构层改造：统一 BlockItem 壳层 + InlineEditor 内核

BookEditorRoot 级别
维持现有 useBlocks / useUpdateBlock / useDeleteBlock / useBlockInsertController 端口不变。

把 BookEditorRoot 的主渲染简化为：

外层「纸张容器」：<div className="bookPaper">；
内部就是按顺序 map 出 BlockItem，不再引入多种 layout 模式（段落模式 / grid 模式）。
BlockList 改造为「轻控制器」
职责收敛到：
blocks 顺序渲染；
把 activeBlockId、editingBlockId、slashMenuState 等 UI 状态往下传；
提供键盘事件入口（Enter / Backspace / Up / Down / Slash）。
不再承载「view / edit 切换」的大逻辑，改由 Block 插件自己决定。
新的统一壳层：BlockItem（强约束）
DOM 结构统一为：
<div className="blockItem" data-block-id={block.id}>
  <div className="blockItem-main">
    <BlockPlugin.DisplayOrEditor ... />
  </div>
  <div className="blockItem-actions">... 操作按钮 ...</div>
</div>

要求：

blockItem-main 负责文本和插件主体；
blockItem-actions 绝对定位在右上角，永远不参与主文本布局；
BlockItem 自己不决定「view / edit」，而是从 BlockPlugins 取到给定的 Display / Editor 组合，根据 editingBlockId 决定渲染哪个。
插件接口微调：显式支持「无分裂视图模式」
在 blockPluginsImpl.tsx 上增加一个约定：
interface BlockPlugin {
  kind: BlockKind;
  Display: FC<BlockDisplayProps>;     // 只读视图（用于非编辑态）
  Editor: FC<BlockEditorProps>;       // 编辑态（可与 Display 结构一致）
  prefersInlineShell?: boolean;       // 标记该块适合“同壳层内编辑”
  normalize: (...) => BlockContent;
  createDefaultContent: () => BlockContent;
}

对于 paragraph / heading / todo / callout / quote / code 等文本类 block：

Display 和 Editor 必须共享相同 DOM 结构（同一行高、同一 padding/margin）；
区别只在：contentEditable / textarea 是否可编辑、是否有光标、是否显示 placeholder。

三、交互与视觉规则：让块「隐身」，保持安静

块的「存在感」规则
非编辑状态下：

每个 block 看起来就是一行（或多行）正常文本 / 插图；
不渲染边框、背景色、分隔线等「块容器」视觉元素；
唯一的块级视觉差异是：不同 kind 的基础排版（标题字号、todo 前面有 checkbox、引言有左边线…）。
Hover 时：

只对「当前 hover 行」展示极低对比度的轻量 affordance（右上角淡灰色加号或 ⋯）；
不改变行高、不加底色，只改变右上角小图标的 opacity。
编辑态规则（键盘优先）
点击任意 block 文本 → 对应 block 进入编辑态：

DOM 不变，同一段落仍在原来位置；
显示的是 Editor 版本，但布局骨架与 Display 一致；
若是 paragraph/heading，可以直接使用 contentEditable（内联），或是高度自动的 textarea，但必须保证高度平滑过渡（AutoSize + maxLines）。
Enter / Backspace 规则继承 Plan126：

Enter：在段落 / 标题末尾创建新的 paragraph block，调用 CreateBlockUseCase + 排序逻辑；
Backspace：空段落时删除当前 block，光标合并到前一块。
这些规则在 BlockListController 或 useBlockKeyboardController 中统一实现，不写入 Domain。
工具条与操作按钮（参考 Plan_124）
blockItem-actions 视觉调整：

默认不显示（opacity: 0; pointer-events: none）；
blockItem:hover 或 blockItem--editing 时渐显（opacity: 1），但按钮本身使用浅灰线框 + 透明背景；
删除按钮仅图标为红色线稿，不使用红色背景。
数量策略：

非 active block：只显示一个「+」或 ⋯（打开更多菜单），维持安静；
active block（光标在内）：显示完整 2–3 个操作（如历史/删除），但仍然淡色、右上角。
出现方式：

使用 150–200ms 的 hover 延迟 hook：快速滚动时几乎不会看到任何操作按钮；
只有鼠标停在某一行时，才慢慢浮现。
Slash menu + caret 定位（参考 Plan_123）
只在 slash menu 打开期间挂 selectionchange 监听：

打开 / 菜单时：立即用 Range.getBoundingClientRect() 算一次 caret 坐标；
在菜单打开期间监听 selectionchange，用 requestAnimationFrame 节流更新位置；
菜单关闭时，立刻移除监听器。
位置规则：

Slash menu 永远贴在文本下方（rect.bottom 附近），水平对齐 rect.left；
不改变 block 的 DOM 结构（使用绝对定位在 editor 容器内）。
四、技术实现要点（结合当前 Wordloom 代码）

contentEditable 与 DOM 无冲突策略
不直接把整页设为单个大 contentEditable，而是：

每个文本型 block 内部用一个 contentEditable 区域包裹其文本；
外层 BlockItem 和 BookEditorRoot 都是普通 div，不参与 selection；
通过 data-block-id + rootEl.contains(range.startContainer) 保护「只对当前 block 响应 selectionchange」。
对 React 更新的约束：

编辑中避免每次 keypress 都触发整棵树重渲染：
使用受控 + debounce 或半受控策略（例如 onInput 内部更新 local state，并在 blur / Enter 时提交到服务器）；
或者保持受控，但在 BookEditorRoot 层用 React.memo + key 分区，只重渲染当前 block。
Block 插件改造方向
为 paragraph / heading / quote / callout / code 实现「同布局 view / edit」：
ParagraphDisplay / ParagraphEditor：统一使用 .textBlockShell 样式，编辑态只加一个略淡的 focus 边框或下划线。
HeadingDisplay / HeadingEditor：相同 h1/h2/h3 样式，编辑态不改变字号，只改变 caret 颜色和 placeholder。
Quote/Callout/Code 等：只在边缘增加最小区别（左边线、浅背景），编辑态不要额外多一层容器。
状态集中管理
const [editingBlockId, setEditingBlockId] = useState<string | null>(null);
const [slashMenuState, setSlashMenuState] = useState<{ open: boolean; anchorBlockId?: string; caretRect?: DOMRect }>();


任何块的 onStartEdit → setEditingBlockId(block.id)；onExitEdit → setEditingBlockId(null)。

性能保护
对 blocks 列表进行：
React.memo(BlockItem) + areEqual（只有 content / meta / active 状态变化才重渲染）；
长列表可再接虚拟滚动（但这一点可以放在后一阶段）。
五、分阶段落地计划

Phase 1：壳层统一 + view/edit 结构对齐
统一 BlockItem DOM 结构与 CSS（不改交互，只让所有 block 看起来是流文档）。
确保 paragraph/heading/todo/callout/quote/code 的 Display / Editor 使用相同布局类名。
不引入 contentEditable，只用现有 textarea / inputs，但避免 overlay 和大范围 DOM 重组。
Phase 2：内联编辑体验（contentEditable / micro editor）
选定 1–2 个主力 block（paragraph + heading）先改为 contentEditable 微编辑器：
实现本地 state + blur 提交 + Enter / Backspace 逻辑；
确认与 Plan126 的键盘契约保持一致。
验证：打开/关闭任意段落编辑，页面无明显抖动或 reflow 峰值。
Phase 3：Slash menu 与工具条的「低存在感」重构
按 Plan_123 改 slash menu 的 selectionchange 策略，限定监听周期；
按 Plan_124 改 blockItem-actions 的 CSS、数量规则和 hover delay；
在 VISUAL_RULES.yaml、HEXAGONAL_RULES.yaml 更新对应条目（Plan128+Plan126 对齐）。
Phase 4：完整插件体系迁移与回归测试
为所有富块（todo_list / callout / quote / divider / image / image_gallery / code / custom）补齐：
同壳层 view/edit；
无抖动的编辑体验；
插件级 normalize 逻辑。
对 /admin/books/[bookId] Blocks tab 做一次全流程自测：
创建 / 编辑 / 删除 / 还原；
快速光标移动、频繁打开关闭编辑；
确认 DOM 稳定、无明显闪动。
如果你愿意，下一步我可以先把「Phase 1 + Phase 2 的技术规格」写进一个新的 VISUAL/HEXAGONAL 小节（类似 block_editor_plan128_inline_shell_v2），然后在 modules/book-editor 里挑 paragraph/heading 两个插件做一个最小可运行版本的 inline contentEditable，先跑一轮实际效果。