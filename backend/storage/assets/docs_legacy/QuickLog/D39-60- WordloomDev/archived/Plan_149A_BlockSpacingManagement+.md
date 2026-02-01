嗯，这个现象我大概能脑补到：

“我已经改了 spacing token，值也变了，CSS 里也映射了，结果屏幕上一点没动。”

说明“间距”这件事，很可能不只被你刚刚改的那一层控制，上面/下面还有别的来源在撑着。
我来帮你拆一拆可能的几层“凶手”，你可以对照查一遍（吃两口再看一层 😆）。

1. 先把“层级”想清楚：至少有 4 层在参与
以你这个「段落 + bullet」为例，通常会有：


整个 block 列表容器


比如 .blockList, .editorBody


有没有 row-gap, grid-row-gap, line-height 之类？




每一个 block 外壳


.blockItem, .paragraphBlock, .bulletBlock


常见：margin-top, margin-bottom, padding-block




内层真正的文本元素


<p>, <h2>, <ul>，这些浏览器默认就自带 margin


比如 <p> 默认 margin-block: 1em，不清空就会叠加




列表内部的 li


li { margin-block: 4px; line-height: 1.6; } 之类


行高太大对“视觉间距”影响也很大




只改了 token → 映射到了其中一层，但其它三层没动，就会出现：

“变量值确实变化了，但是最终视觉距离几乎不动。”


2. 几个高概率踩坑点（我按优先级帮你排一下）
2.1 父容器用了 gap，你在子元素上改 margin
例如：
.blockList {
  display: flex;
  flex-direction: column;
  row-gap: 24px;           /* <—— 真正控制块与块的间距 */
}

.blockItem {
  margin-top: var(--space-blockSection);  /* 你现在改的是这里 */
}

这种结构下：


即使你把 margin-top 从 24px 改到 4px


但 row-gap: 24px 还在


视觉间距几乎不动 → 你会觉得 “改 token 没反应”


🔧 检查点


DevTools 点任意一个 block，看 computed styles：
有没有 row-gap、gap 这种属性在父节点上？


✅ 处理建议


只保留一种机制：
要么统一用 row-gap，所有 block 的 margin-top 设为 0；
要么禁止父层 gap，只用 block 自己的 margin-top。



2.2 浏览器默认 margin 在搞事（p / h / ul）
非常常见的情况是：
<div class="blockItem paragraphBlock">
  <p>AAAAAA</p>  <!-- 默认 margin-block: 1em -->
</div>

<div class="blockItem bulletList">
  <ul> <!-- 默认 margin-block: 1em -->
    <li>写点什么…</li>
  </ul>
</div>

就算你已经把 .blockItem 的余白都 token 化了，p / ul 自带的 margin 还在，会让视觉间距：


比你设计的数值大一截


你改 token，只在外壳上动，UA margin 没变 → 视觉差不多


🔧 检查点


DevTools 里选 <p> 或 <ul> ，看 computed 里的 margin-block-start/end


如果你没主动清空，很可能是 16px / 1em 左右


✅ 处理建议
在全局 CSS 或编辑器作用域把这些重置掉：
.blockItem p,
.blockItem h1,
.blockItem h2,
.blockItem ul,
.blockItem ol {
  margin-block-start: 0;
  margin-block-end: 0;
}

然后统一让 block 壳来管理垂直 spacing，不要让 HTML tag 自己带节奏。

2.3 token 映射到了 CSS 变量，但实际用的是硬编码 px
也很常见的结构：
:root {
  --wl-block-spacing-tight: 8px;
}

/* 你以为在用变量 */
.bulletList {
  margin-top: 24px;   /* 硬编码！ */
}

你改的是 --wl-block-spacing-tight，但是组件 CSS 里压根没引用这个变量：


token 更新 ✅


视觉效果 ❌（因为硬编码 px 在生效）


🔧 检查点


搜索 bulletList / paragraphBlock 那些类的 CSS，是否仍然有 margin-top: 24px 之类硬编码


或者同一个属性写了两遍，后面那行覆盖了前面的变量


✅ 处理建议
统一改成变量引用：
.bulletList {
  margin-top: var(--wl-block-spacing-tight);
}


2.4 你改的是“内容内部行距”，而不是块与块之间的间距
比如你把 line-height 当成 spacing token 去调，结果 block 之间还是很大：
.bulletList li {
  line-height: var(--wl-lineHeight-body);  /* 你改的是这个 */
}

/* 但真正的“段落与 bullet 之间”的距离在这里： */
.blockItem.paragraph + .blockItem.bulletList {
  margin-top: var(--wl-block-spacing-tight);   /* 这个没动 */
}

所以你肉眼看着，子弹之间变紧了，但上一段和 bullet 之间洞还是那么大。
✅ 建议


把“块与块之间的间距”独立成一个 token，比如：


space-block-section（大间距，用在完全不相关块）


space-block-tight（小间距，用在段落+bullet）




行高是另一套：lineHeight-body, lineHeight-heading
只调整字与字之间的“空气感”，不要混用。



3. 给 Copilot 的“集中处理”任务（可以直接丢过去）
你现在可以让它帮你梳理一遍所有块间距逻辑，而不是只修一处：
// Goal: unify vertical spacing between blocks in the editor.
//
// Symptoms:
// - I've already mapped spacing tokens to some CSS variables,
//   but visually the gap between a paragraph and a bullet list
//   is still much larger than expected.
// - That means there are multiple sources of vertical spacing
//   stacked together.
//
// Please do a pass over the editor styles and:
//
// 1. Centralize "block-to-block" spacing:
//    - Use tokens like:
//        --wl-space-block-section (e.g. 20–24px)
//        --wl-space-block-tight   (e.g. 6–10px)
//    - Apply them only on the block wrapper (.blockItem, .paragraphBlock,
//      .bulletListBlock, etc.).
//    - Avoid mixing `row-gap` on the parent *and* `margin-top` on children.
//      Prefer one mechanism (e.g. parent row-gap, child margin-top = 0),
//      or the other.
//
// 2. Reset browser default margins inside blocks:
//    - For p/h/ul/ol inside a block, set:
//        margin-block-start: 0;
//        margin-block-end: 0;
//    - This ensures all vertical spacing comes from the block wrapper,
//      not from HTML defaults.
//
// 3. Make list-type blocks use "tight" spacing:
//    - When a paragraph/heading is immediately followed by a bullet or
//      todo list, the gap should use `--wl-space-block-tight`, not the
//      larger section spacing.
//    - Implement this as either:
//        .blockItem.bulletList { margin-top: var(--wl-space-block-tight); }
//      or a `spacing="tight"` modifier class.
//
// 4. Check for hard-coded px values:
//    - Replace any remaining `margin-top: 24px` / `margin-bottom` etc.
//      with the appropriate spacing tokens.
//    - Make sure no later rule with hard-coded px overrides the token-based
//      variable.
//
// After this cleanup, adjusting the spacing tokens should immediately
// change the perceived gap between:
//    [paragraph] ↔ [bullet list] ↔ [todo list]
// without hidden margins from p/ul/li or parent row-gap interfering.


小结
你现在遇到的不是“token 没生效”，而是：

多层 margin / gap / 行高一起叠着，
你只动了其中一层，其他几层没动。

按上面的 checklist 把这几层统一收拾一下：


先确认是否有父级 gap


把 <p> / <ul> 的默认 margin 清掉


用 token 替掉硬编码的 px


把“块间距”和“行高”彻底分开


做完一轮，之后你只要改一两个 spacing token，就能明显看到“人眼可见”的变化了。

## 2025-12-03 执行摘要（Plan149A 回填）

1. **Token family 重排 + 单层节奏**：`frontend/src/modules/book-editor/ui/bookEditor.module.css` 注入 `--wl-space-section` / `--wl-space-tight` / `--wl-space-inline` / `--wl-block-padding-*` / `--wl-list-*`，并让 `.blockItem + .blockItem` 成为唯一节奏来源，父层 `row-gap` 全面移除。
2. **彻底清空 UA margin/padding**：`.blockItem :is(p,h1~h6,ul,ol,li,blockquote,.textBlockShell,.textBlockContent)` 统统 `margin-block:0;padding:0`，quote/list/todo 等特殊块只通过壳层 padding 控制空气感。
3. **Inline shell/列表对齐 token**：`.inlineRow`、`.todoList`、`.todoEditor`、列表 display 均改用 `--wl-space-inline`、`--wl-list-item-gap`、`--wl-list-indent`，再也不靠隐式 flex gap；Heading/Paragraph/List/Todo 邻接组合统一落在 data-kind 选择器。
4. **回归守卫**：搜索/删光遗留的 `margin-top: 24px`、`gap: 20px` 等硬编码，确保调节 token 即可改变真实视觉间距，并在 PR 描述附带 DevTools 截图。
