好，先总结一下你现在的状态：

你已经把 blockItem 上的 padding-block 删掉了 ✅

文本壳子（bookEditor_textBlockContent、list 里的 todoText）在真实页和测试页里 margin / padding 都是 0 ✅

说明「行内内容」这层已经对齐了，接下来只剩下**“block 和 block 之间的节奏”**要定下来。

第一步：选一个“节奏 owner”

从你截图 1 看，现在挂 tokens 的这条规则长这样（大概）：

/* 现在这个节点上： */
display: flex;
flex-direction: column;
gap: var(--wl-space-5);         /* 16px */
padding-block: var(--wl-editor-padding-y); /* 你已经关掉了 */
--wl-space-0: 0px;
--wl-space-1: 2px;
--wl-space-2: 4px;
...
--wl-space-block-tight: var(--wl-space-2);
--wl-space-list-before: var(--wl-space-3);
--wl-space-list-after: var(--wl-space-3);
...


接下来建议把「谁控制垂直节奏」定死：

让包着所有 bookEditor_blockItem 的那一层（editor shell）做唯一的“节奏 owner”

假设这层叫 .bookEditor_shell，你可以这样写：

/* 编辑器外壳：统一垂直节奏 */
.bookEditor_shell {
  display: flex;
  flex-direction: column;

  /* 基础节奏：紧凑 token */
  row-gap: var(--wl-space-block-tight);  /* 比如 2px 或 4px */

  /* tokens 继续放在这层没问题 */
}


关键点：把 gap: var(--wl-space-5) 改成用 --wl-space-block-tight，或者你想要当“基础间距”的 token。
这一步做完，你会发现段落堆叠的距离立刻跟测试页接近很多。

第二步：确保 block 自己不再乱加 margin / padding

为了避免“多一刀”，先把通用 block 的垂直 margin 清掉：

.bookEditor_blockItem {
  margin-top: 0;
  margin-bottom: 0;
  padding-top: 0;
  padding-bottom: 0;
}


现在规则是：

shell 用 row-gap = --wl-space-block-tight 做「基础 2px/4px」；

普通段落栈：block 和 block 之间就只有这一个 gap。

这样一来：

真实页选中同一个 bookEditor_blockItem，Computed 里看到的就是：

margin-top: 0

padding-top: 0

父级有 row-gap: 2px/4px

测试页如果也用同一个 shell 组件 / 同一套 CSS，就会完全一致。

第三步：用 token 给“特殊组合”加料（list / quote）

现在轮到你那堆 --wl-space-list-before、--wl-space-list-after 上场了。做法是：

“基础节奏”仍然是 shell 的 row-gap = --wl-space-block-tight。

遇到需要「更大一点的间距」的地方，在“第二个 block”上加额外的 margin-top，用对应 token。

例如：

/* 段落 → 列表：列表前面多一点空隙 */
.bookEditor_blockItem[data-kind="bulleted_list"],
.bookEditor_blockItem[data-kind="numbered_list"] {
  margin-top: var(--wl-space-list-before); /* 例如 space-3 = 8px */
}

/* 列表 → 段落：从列表出来再多一点空隙
   这个类可以在渲染时加上去，例如检测「前一个节点是 list」 */
.bookEditor_blockItem[data-after="list"] {
  margin-top: var(--wl-space-list-after);
}

/* 段落 ↔ quote 卡片：section 级别的间距 */
.bookEditor_blockItem[data-kind="quote"] {
  margin-top: var(--wl-space-quote-before);
}

.bookEditor_blockItem[data-after="quote"] {
  margin-top: var(--wl-space-quote-after);
}


这样一来：

普通段落堆叠：只吃 row-gap = --wl-space-block-tight，和测试页文案里那句
“Paragraph-to-paragraph adjacency collapses to the tight token (2px)” 一致。

进入 / 走出列表 / quote：row-gap + 一点 margin-top，视觉上就会像你测试页那组 demo。

第四步：对照测试页做一次“仪式感自检”

在测试页的「Paragraph → List → Paragraph」那一段：

点第一个 list 的 bookEditor_blockItem[data-kind="bulleted_list"]，看 margin-top 是不是等于 --wl-space-list-before。

点 list 后面的 paragraph，看 margin-top 是不是等于 --wl-space-list-after。

在真实编辑器里：

做一模一样的结构（段落 → 列表 → 段落）。

同样点 list block / list 后面的 paragraph，看 Computed 数值是否完全相同。

如果两边数值一致，但视觉上还是差一点，那就是测试页和真实页用的字体 / line-height / zoom 不一样，那就另开一局；但从你现在的截图来看，字体 / line-height 已经是一致的，差的就是上面这几刀 CSS。

小结一下接下来的具体动作

把挂 tokens 的那条规则里的 gap: var(--wl-space-5) 改成
row-gap: var(--wl-space-block-tight)（或者你想用的那个 token）。

给 .bookEditor_blockItem 清掉 margin-block、padding-block。

用 margin-top + 各种 --wl-space-* 实现：

段落 → 列表 / 列表 → 段落；

段落 ↔ quote；
（需要的话，用 data-after="list" / data-after="quote" 之类的标记辅助。）

做完这三步，你再对比真实页和 spacing 测试页，基本就是同一个“物理定律宇宙”了，之后就只剩下微调 token 数值这种快乐的调参活儿。

---

## Plan153 统一执行计划（A + B 合并版）

> 目标：用一组语义化 shell token 管理“块壳高度”，同时让 block 间距仍由 `--wl-space-*` 节奏 token 掌控。

### 命名与作用域

- 统一格式：`--wl-{域}-{shell}-{元素}-{属性}`，示例：`--wl-block-shell-paragraph-padding-y`。
- Shell token **只**描述单个 block 内部的 padding / inline 缩进；block 与 block 之间的距离仍由 `--wl-space-block-tight`、`--wl-space-list-before/after`、`--wl-space-quote-before/after` 管理。
- 普通 paragraph / heading 的 shell padding-y 恒为 `0px`；若未来需要“段落卡片”，另起 `data-kind` + 专用 token。

### 令牌清单（首批）

| 作用域 | Token | 说明 |
| --- | --- | --- |
| block | `--wl-block-shell-paragraph-padding-y` | 段落壳垂直 padding，默认 0，防止壳与节奏重叠 |
| block | `--wl-block-shell-heading-padding-top` / `bottom` | 允许标题在章节开头/结尾做非对称缓冲 |
| list | `--wl-list-shell-padding-y` | 列表壳内垂直呼吸，搭配 before/after 形成桥接 |
| list | `--wl-list-shell-padding-inline` | 取代写死的 `padding-left`，和 `--wl-list-indent` 同步 |
| todo | `--wl-todo-shell-padding-y` | 待办壳内部的纵向 buffer，与 todo row gap 区分 |
| quote | `--wl-quote-shell-padding-y` | 引用壳内部 padding，仍让 before/after 控制上下距离 |
| inline | `--wl-inline-insert-shell-padding-x/y` | 行内插入条/Slash 菜单的壳空间 |
| inline | `--wl-inline-list-shell-gap-y` | 行内列表（quick todo）之间的纵向 gap |

所有旧 token（`--wl-block-padding-y`、`--wl-block-padding-y-dense`）暂时 alias 到对应新 token，待 DOM/CSS 搜不到旧名再删除。

### 实施步骤

1. **Token 定义 + 分组**：在 `bookEditor.module.css` 的 token 区新增上表 token，并以注释明确 “Shell tokens: control block internals only”。
2. **CSS 替换**：
  - `.bookEditor_shell` 用 `row-gap: var(--wl-space-block-tight)` 作为唯一基础节奏； `.bookEditor_blockItem` 的 margin/padding 清零。
  - Paragraph/heading 壳纵向 padding 归零；list/todo/quote/inline 按照新 token 设置 `padding-block`/`padding-inline`。
  - 进入/离开 list/quote 时仅在“第二个块”上挂 `--wl-space-list-before/after`、`--wl-space-quote-before/after`，不要让 shell token 扩散到节奏层。
3. **Spacing Test 更新**：
  - `TOKEN_METADATA` 中新增上述 shell token，并注明「仅作用于 block 内部」。
  - 新增 “Shell × Rhythm Matrix” 卡片：段落 / 列表 / todo / quote / inline 依次渲染，展示 shell padding 与 before/after 配合的实际视觉。
4. **规则 / 文档 / ADR**：
  - VISUAL_RULES：记录“shell token = 内部高度，space token = 节奏”原则与 QA SOP。
  - DDD_RULES / HEXAGONAL_RULES：强调该迭代完全属于 UI adapter，不得新增 Domain 字段，Block use case 仍只交付 block 列表。
  - 新增 ADR-140，记录命名、alias 退出条件、Spacing Test 快照要求。
5. **验证 & 退出机制**：
  - 每次调 token 必须刷新 `/dev/spacing-test` 并截图“Paragraph → List → Paragraph”与“Paragraph → Quote → Paragraph”。
  - 当 repo 中再无 `--wl-block-padding-y` / `--wl-block-padding-y-dense` 使用时，在下一次版本 bump（v3 → v4）中删 alias。

### 风险提示 & 兜底

- 如果段落 ↔ 列表仍觉得“距离大”，先确认是否有人误把 shell padding 当作节奏在加；若需要更细腻的桥接，优先调整 `--wl-space-list-before/after`。
- inline shell token 会被 BlockList/InlineCreateBar 复用，记得在 BlockList CSS 中同步替换，否则 spacing-test 会出现“真实页面跟 sandbox 不同调”的问题。
- 若未来要支持不同语言字号的 heading，可以追加 `--wl-block-shell-heading-lg-padding-*` 作为扩展，但当前 Plan 不执行，只在 ADR 里登记为 Potential Follow-up。

---

## Plan154B 评审补强要点（巩固 Plan154A）

1. **Step 1：命名语法开箱即懂**
  在 token 区块最上方用注释写死四条规则：`--wl-space-0..6` 只当刻度、`--wl-space-block-*` 负责节奏、`--wl-*-shell-*` 只管壳内部、任何未遵守前三条的名字（如 `--wl-block-padding-y`）都属于 Legacy。打开文件即能看到命名语法，方便人和 Copilot 一眼辨别可用范围。

2. **Step 2：节奏前缀统一为 `--wl-space-block-*`**
  所有 block 间距都收敛到 `--wl-space-block-tight/section`、`--wl-space-block-list-before/after`、`--wl-space-block-todo-before/after`、`--wl-space-block-quote-before/after`。`--wl-space-*` 但不带 block- 的名字保留给 Primitive 梯子或其他系统，避免 inline spacing 与 block spacing 混名。

3. **Step 3：结构层级写死**
  约定 `bookEditorShell > blockList > blockItem`。`bookEditorShell` 只处理外壳 padding（`--wl-editor-padding-y`），`blockList` 是唯一节奏 owner（`row-gap: var(--wl-space-block-tight)`），`blockItem` 禁止新增 margin/padding，所有内部 breathing 都交给 `.blockItemMain`。

4. **Step 4：Shell 永不参与块间距**
  `--wl-*-shell-*` 只能出现于 `.blockItemMain` 或更内层组件；任何 block-level 选择器若引用 shell token 即视为违规，会与节奏系统打架。引用 shell token 的地方必须马上改成节奏 token 或内部 padding。

5. **Step 5：Paragraph Stack 只吃 Tight**
  段落 / 标题之间的纯文本栈仅依赖 `row-gap = --wl-space-block-tight`。若未来需要更紧密的组合，新增 `--wl-space-block-stack` 明确说明用途，禁止重复叠加 `margin-top: var(--wl-space-block-tight)`。

6. **Step 6：Legacy alias + Lint 双保险**
  ADR 中列出黑名单：`--wl-block-padding-y`、`--wl-block-padding-y-dense`、`--wl-space-section`、`--wl-space-inline` 等。一旦 diff 中出现这些名字，lint / CI 直接拒绝。当前阶段保留 alias 指向新 token，但禁止在新代码中引用。

7. **Step 7：Inline / Todo 三层分层**
  - `--wl-space-block-*`：todo block 与其他 block 之间的节奏。
  - `--wl-todo-shell-*`：todo 壳内部 padding。
  - `--wl-todo-item-gap`：todo 行与行的间距。
  Inline 组件遵循同样的「block vs shell vs row」三层命名，防止 spacing-test 和真实页面出现不同频率。

8. **Step 8：Spacing Test 表达式统一**
  每个卡片都用 `Rhythm: <token> / Shell: <token>` 的格式展示现役 token，QA 可以直接对照真实编辑器的 Computed Value。Spacing 测试必须至少包含 Paragraph→List→Paragraph、Paragraph→Quote→Paragraph、Paragraph→Todo→Paragraph 三段。

9. **Step 9：数值决策落地**
  - `--wl-space-block-tight = 2px`（`var(--wl-space-1)`），对应 row-gap。
  - List / Todo：`before = 0px`、`after = 2px`（row-gap 2px + after 2px，总视觉 4px）。
  - Quote：保持 section 级 8px，必要时 micro 调整在 `--wl-space-block-quote-*` 内完成。

以上补强要求全部落实在 `bookEditor.module.css` 与 QuickLog 文档中，并在 spacing-test / ADR 中备案，保证 Plan154A 从「建议」升级为具备 lint + 测试兜底的执行规范。