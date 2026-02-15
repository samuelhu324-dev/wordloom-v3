这个间距问题，本质上跟刚才那个“光标乱跳”是一个家族：同一块东西，被好几层 DOM + 默认样式一起拉扯，你改一层，另外两层继续生效，所以“怎么改都没用”。

我先说一套长期能用的解决办法，不是今天改一下、明天又炸的那种。

1. 先搞清楚：是谁在制造这条“巨大空隙”

你这个截图里，一般会有几层结构（大概是这样）：

<div class="BlockRow">           ← 一行 block（段落 / 列表）
  <ul>
    <li>
      <div class="TextBlockShell">
        <div contenteditable>AAAA</div>
      </div>
    </li>
  </ul>
</div>
<div class="BlockRow">
  ...
</div>


视觉上那一条“大空隙”，往往是这些东西叠加出来的：

.BlockRow 自己的 margin-bottom

ul / li 的浏览器默认 margin-block

.TextBlockShell 自己的 margin-bottom / padding-bottom，外加 border-bottom

下一行 .BlockRow 的 margin-top（加上 margin 折叠）

你只改了其中一个（比如改了 .TextBlockShell 的 margin），另外两三个在那儿悄悄生效，就会觉得“为什么我动它没反应”。

2. 定个规矩：只有一层 DOM 可以控制纵向间距

一劳永逸的做法是：

编辑器里，“每一行 block 之间的空隙，只允许由最外层 .BlockRow 控制”。
其它所有东西（p / ul / li / TextBlockShell）一律清掉上下 margin。

可以直接这么做：

/* 1. 统一：block 行之间的间距 */
.BlockRow + .BlockRow {
  margin-top: 0.5rem;   /* 这里是“标准段落间距”的唯一来源 */
}

/* 2. 清掉内部元素的默认 margin，防止叠加 + 折叠 */
.BlockRow p,
.BlockRow ul,
.BlockRow li,
.BlockRow .TextBlockShell {
  margin-block: 0;
}

/* 如果你有 border-bottom 的那条线，也放在 BlockRow 上 */
.BlockRow--withDivider {
  border-bottom: 1px solid var(--divider-color);
  padding-bottom: 0.25rem;    /* 线和文字之间留一点点 */
}


这样所有 block 之间的距离 =

上一个 .BlockRow 的 padding-bottom + 它自己的 border + 下一个 .BlockRow 的 margin-top（或者直接只用 margin-top）。

你要缩、要放，只改 .BlockRow + .BlockRow { margin-top: ... } 一处就够了。

3. 子弹列表单独的“内部节奏”

接下来只调列表内部的节奏，而不影响行与行之间：

/* 控制列表内部缩进，而不是靠 margin */
.BlockRow ul {
  padding-left: 1.5rem;
}

/* 列表项之间的小间距（只在列表内部生效） */
.BlockRow li + li {
  margin-top: 0.15rem;
}

/* 彻底禁止 li 里面再有多余 margin */
.BlockRow li p {
  margin-block: 0;
}


这样效果是：

段落之间：统一 0.5rem 左右的行距；

同一个 bullet list 里的项目：只用 li + li { margin-top: 0.15rem; } 控制，很紧凑；

不会出现“列表上面一坨大空隙，下面一坨大空隙”的情况。

4. 为什么你之前“反复改都没用”

通常会有几个典型坑：

改错 CSS 文件 / module

你现在有旧版 BlockRenderer 的 css + 新 book-editor 的 module；

DevTools 里看生效的是 BlockRenderer.module.css，结果你改的是 BookEditor.module.css，当然没用。

标准动作：在浏览器里选中那条空隙 → 看 Computed → 找出真正生效的 margin/border/padding 和对应文件，再改那一份。

margin 折叠让你误判

<p> 的 margin-bottom 会和父级 <li> / <div> 的 margin-top 折叠，

你把 li 的 margin 改成 0，看起来好像没什么变化，其实是 p 的 margin 接管了。

所以最安全的策略就是：所有 block 内部元素 margin-block 全清掉。

同一类型 block 有两种 DOM 结构

普通段落：BlockRow > TextBlockShell > contentEditable

bullet：BlockRow > ul > li > TextBlockShell > contentEditable

你只给第一种结构写了间距，第二种结构还吃着浏览器默认间距；这就是“段落看着正常，一插 bullet 就乱”的经典原因。

5. 顺手给你一套“编辑器纵向节奏规则”

你可以直接写进 VISUAL_RULES 里，这样以后就不用乱改：

VERTICAL-01：段落 / 列表 / 标题等所有 block，都挂在统一的 .BlockRow 上；

VERTICAL-02：只有 .BlockRow + .BlockRow { margin-top } 可以控制行距；

VERTICAL-03：.BlockRow 内部的 p / ul / li / h1...h6 / TextBlockShell 必须 margin-block: 0；

VERTICAL-04：如果需要分割线，只允许 .BlockRow 本身加 border-bottom + padding-bottom，其它地方禁止画线；

VERTICAL-05：列表内部的条目间距只允许由 li + li { margin-top } 决定。

照这套来，你以后遇到任何“间距怪异”的情况，直接问自己一句：

现在是不是又有别的元素在偷着加 margin / padding / border？

然后去那一层清掉，就不会再陷入“今天猛改 5 个地方，只是刚好抵消了”的魔幻循环了。

///////////////////////////////////////////////////////////////////////////////

Plan: 统一 Block 间距规则 + 文档落地（Plan143 落实）
目标：把“段落/列表等块之间的垂直间距”从现在的多层 DOM+默认样式拉扯，收敛成一套可控、可追踪的规则，并同步到规则库与 ADR，后续所有实现按这套来，不再随机改 CSS。

Steps
提炼 Plan143 规则，形成 VERTICAL 系列规范

从 Plan_143_BlockSpacing++.md 抽取 5 条核心原则（“只允许一层 DOM 控制间距”“内部元素 margin-block:0”“列表内部用 li+li 控制节奏”等），整理为 VERTICAL-01 ~ VERTICAL-05，并用中文清晰描述适用范围（Block 编辑器/富文本区域）。
把 VERTICAL 规则写入三份规则库

在 VISUAL_RULES.yaml 中新增一个 block_editor_vertical_rhythm 段，挂上 adr_reference: "ADR-134-block-editor-vertical-spacing.md"，列出 VERTICAL-01~`VERTICAL-05` 及说明、典型 DOM 结构示例。
在 HEXAGONAL_RULES.yaml 的前端/适配器部分补充一小节 “UI 布局作为 Adapter 约束”，注明：Block 垂直间距属于 UI 适配层策略，不得反向渗透到领域模型/后端（例如禁止把“行距”当字段存进实体）。
在 DDD_RULES.yaml（如果有；若文件名不同则在对应 DDD 规则文件）中补一句 Domain 边界：Block 领域模型只关心语义块序列，不关心视觉距离，前端必须通过 VISUAL_RULES 控制布局。
对 Block 编辑器 DOM 层做“唯一间距层”梳理

明确 legacy 块编辑栈使用的“行容器”组件（当前是 BlockList.tsx 下的 BlockItem + .blockItem + .list，等价于 Plan143 中的 .BlockRow）。
在 BlockList.module.css 中正式把 .blockItem 视作唯一的纵向间距控制层：
继续使用  .list > .blockItem + .blockItem { margin-top: var(--block-gap-*) } 作为基础行距。
允许通过 data-kind 组合微调特例（如段落↔bullet 压缩为 0），但禁止在更内层元素再设置垂直 margin 撑高度。
清理内部节点的默认 margin / padding / border-bottom

在 BlockList.module.css 中新增一组“内部归零”规则，对应 Plan143 的 .BlockRow 内部清零：
选择器类似：.blockItem p, .blockItem ul, .blockItem li, .blockItem .textBlockShell { margin-block: 0; }；若有 h1–h3 或其他展示标签一并覆盖。
若底部分割线需要存在（例如段落下那条灰线），统一移动到 .blockItem 本身（如 .blockItem[data-kind='paragraph'][data-has-divider='true']），并通过 padding-bottom 控制线与文字距离；内部的 .textBlockShell 不再自带 border-bottom。
检查 BlockRenderer.tsx 对段落/heading 的展示部分是否依赖 <p> 自带 margin；在 CSS 中已经通过 .paragraphTextLine { margin: 0 0 2px 0; } 控制，确保不会再引入隐性 margin 折叠。
统一列表内部“局部节奏”

对 TODO / bullet / numbered list：
若存在 <ul>/<ol>/<li> 结构，则在对应 CSS 中强制 margin: 0; padding-left 控缩进，只允许 li + li { margin-top: x } 决定条目间距。
line-height 固定为 1.4–1.5，避免通过增大行高来“假装间距”，防止与行距规则混在一起。
在规则库中追加一条 VERTICAL-06：列表内部节奏只准通过“相邻条目规则”控制，不得用 block 级 margin 模糊边界。
建立“定位与 Debug 流程”并写入 VISUAL_RULES

增加一个 debug_vertical_spacing 小节，写清楚以后排查步骤：
用 DevTools 点中“看起来是空白的那条带 Focus 高亮的区域”；
在 Computed 里查看真正贡献高度的 margin/padding/border 行，并记录它属于哪一层 DOM；
若不是 .blockItem，一律视为违规，回到对应组件 CSS 移除；
更新到 BlockList.module.css 的唯一 source。
这部分直接复用 Plan143 中“为什么之前你怎么改都没用”的解释，精简成规范条。
编写 ADR-134（Block Editor Vertical Spacing）

在 ADR 下新建 ADR-134-block-editor-vertical-spacing.md：
背景：截图中段落 + 列表之间出现无法解释的大空隙，改多处 CSS 效果互相抵消；与“光标乱跳”属于同一类多层 DOM 干扰问题。
决策：
唯一间距层：由 block 行容器（BlockItem / .blockItem）通过相邻选择器控制；
内部 margin 清零：所有内部文本/列表容器 margin-block:0；
列表节奏：只允许 li + li 控制；
规则同步：以 VERTICAL-01~`VERTICAL-06` 记录在 VISUAL_RULES.yaml；
影响：复杂布局更易维护；修改行距时只需改一处 CSS；测试与无障碍工具的 Focus Outline 不再被“幽灵 margin”拉偏。
状态：Adopted 2025-12-02，并在 VISUAL_RULES.yaml 的 metadata 或 block 编辑器状态中标注 adr_reference: ADR-134。
最后验证与回写 Plan143

在浏览器里用当前问题场景（段落 + bullet + TODO 等）重新检查：
Focus 高亮所在的 DOM 节点高度是否仅来自 .blockItem 的 margin/padding；
橙色间隙是否完全缩到 0（或预期值）。

## 落地结果（2025-12-02）

- ✅ CSS：`frontend/src/features/block/ui/BlockList.module.css` 与 `frontend/src/modules/book-editor/ui/bookEditor.module.css` 现已把 `.blockItem + .blockItem` 作为唯一行距层，并清空内部 `p/h1~h6/ul/ol/li/.textBlockShell` 的 margin 与分割线。
- ✅ 规则：`assets/docs/VISUAL_RULES.yaml` 新增 `block_editor_vertical_rhythm`（VERTICAL-01~06）与调试流程；`assets/docs/HEXAGONAL_RULES.yaml`、`assets/docs/DDD_RULES.yaml` 分别记录 adapter-only 与 domain 禁止项。
- ✅ 决策：ADR-134《Block Editor Vertical Spacing》说明背景 + 决策 + 调试 SOP，后续 spacing 议题须引用该文档。
- 📎 验收：DevTools 选中段落/列表之间空隙，Computed 面板显示唯一高度来源为 `.blockItem`，无额外 UA margin 参与。
Further Considerations
是否同时对新 book-editor 模块（bookEditor.module.css + ParagraphEditor/ListBlock/TodoListBlock）套用同一 VERTICAL 规则，完全统一“旧 BlockRenderer 与新 Editor”的节奏？
间距 token 是否需要抽象为全局 --wl-block-gap-xxs/xs/sm/...，由 VISUAL_RULES.yaml 定义推荐值，避免之后出现多套“不一样的 6px”？