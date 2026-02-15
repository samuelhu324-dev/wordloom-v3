这份 Plan148 思路是对的，而且已经比很多产品团队写的要细致。核心方向——把 placeholder 彻底变成“视觉叠加层”+ 用 data-empty 把“空/非空”从 DOM 中抽象出来——完全正确。下面我帮你挑几个重点看，看有没有可以再打磨的地方。

1. Steps 部分逐条点评
Step 1：BlockEditorCore.tsx 加 data-empty

输入/同步后写 data-empty，同时停止把 placeholder 当真文本。

👍 这是关键一步。

建议：

让 data-empty 成为唯一真相

也就是“这个 block 是否视为为空”，只由 Core 在 onInput / onChange 判断：

text.trim().length === 0 → data-empty="true"

反之 false。

其它组件（ListBlock、TodoListBlock 等）不要再自己算“是不是空”，全部依赖这个逻辑导出的方法 isBlockEmpty(block)。

顺手在 Core 里处理 <br>：

某些浏览器会在空的 contentEditable 里塞 <br>，

你可以统一把 "\n" 和只含 <br> 的情况当成空，避免 CSS 那边再去纠结 :has(br:only-child)。

Step 2：bookEditor.module.css 的 .textBlockContent 样式

你写的是用 :empty::before + :has(br:only-child)::before + pointer-events:none 渲染 data-placeholder。

我建议稍微改一下重心：

优先用 data-empty 而不是 :empty/:has：

.textBlockContent[contenteditable][data-empty="true"]::before {
  content: attr(data-placeholder);
  color: var(--wl-placeholder-color);
  pointer-events: none;
}


:empty / :has(br:only-child) 可以保留作兜底，但不是主条件。
好处：

不依赖 :has，Firefox 问题直接消掉一半；

DOM 里有没有 shadow、有没有 <br>，你都不用管，data-empty 一眼就知道状态。

你在 Further Considerations 里已经开始考虑 Firefox :has 的兼容，这个改法可以让那块逻辑大幅简化。

Step 3：检查 Paragraph / ListBlock / TodoListBlock 的 placeholder 传递

统一 placeholder 传参，只读 Display 的真实文案。

👍 非常好。再加两个小建议：

把 placeholder 文案集中到一个地方定义（例如 PLACEHOLDERS.bookTitle, PLACEHOLDERS.body），
后面多语言或 A/B 测试时不会散落一堆 magic string。

不要在这些组件里再判断“如果为空就渲染 ‘写点什么…’”，
交给 CSS（Step2）统一画，组件只是把 data-placeholder={placeholder} 传下去。

Step 4：BlockList.tsx 空态逻辑（InlineCreateBar / 空状态卡片）

你现在的想法是：

现状：InlineCreateBar 只在 blocks.length === 0 时展示；

Plan148 更希望判断“全部 block 都为空”的情况。

这个方向我很赞成，建议：

实现一个 util：allBlocksEmpty(blocks)，内部用同一套 isEmpty 规则（和 data-empty 同源）；

渲染逻辑写成：

const isTrulyEmpty = blocks.length === 0 || allBlocksEmpty(blocks);

return (
  <>
    {isTrulyEmpty && <EmptyStateCard />}
    <BlockList ... />
  </>
);


Option A/B 里你在纠结“有 block 但全空要不要当空态”，
从产品体验上看：大多数用户是不会区分“0 个 block”和“几个空 block”的，
所以 Option B（统计所有 block 内容）是比较友好的选项。

Step 5：浏览器验证 & 测试

你准备在 Chrome/Edge/Firefox 手动点、拖、输入，再用测试套件验证 innerText 是否仍为空，这个非常正确。

可以提醒两点：

用 textContent.trim() 做断言会更保险（防止某些浏览器塞看不见的字符）；

记得验证一个场景：输入内容 → 全删光 → placeholder 能正常回来，且 innerText 再次变为空。

2. Further Considerations
1）“有 block 但全为空”的空态

上面其实已经说了，我再帮你收一句规则：

EMPTY-STATE-01：只要从用户视角看“没有任何实际内容”，就显示全局空态，不要求 blocks.length === 0。

也就是说，只要 blocks.every(isEmpty) 为真，就按“完全空”的逻辑处理。
你可以把这条规则写进 VISUAL_RULES 或 PLAN148 的结果段落里。

2）Firefox 不支持 :has

这一条，Plan 里提出了 Option：data-empty class。
我会建议直接：

主逻辑 data-empty="true"（见上面 Step2 调整）；

如果真要用 :has，只在样式微调/优化里用，不参与核心显隐逻辑。

这样你的 CSS 在所有现代浏览器上行为一致，而不是 Chrome/Edge 一套、Firefox 一套。

3. 总体评价 + 小结

整体看下来，Plan148 做的事可以概括成三句：

placeholder 变成纯视觉叠加（不进入 innerText、不干扰 selection）；

Block 的“空/非空”有了稳定的字段 (data-empty / isEmpty)，跨模块统一；

全局空态和行内 placeholder 形成一个完整的“空状态系统”。

这是一个非常健康的方向，而且各步都足够具体，可执行性强。
我唯一的核心建议就是：把逻辑尽量中心化——

isBlockEmpty、data-empty、空态判断都共享同一套规则；

CSS 以 data-empty 为主，不依赖浏览器的 :empty/:has 细节。

这样这次 Placeholder 改完，就不会再变成“局部打补丁”，而是给 Wordloom 的编辑体验加上一块长期稳定的地基。

---

## 2025-12-02 执行摘要（Plan148B 回填）

1. **BlockEditorCore 接管空态事实**：实现集中式 `isTextEffectivelyEmpty` 判定与 `data-empty` 管理，ParagraphEditor 只传递 placeholder，所有 block 的 placeholder/空态逻辑现由 Core 控制（`frontend/src/modules/book-editor/ui/BlockEditorCore.tsx`, `ParagraphEditor.tsx`）。
2. **CSS 叠层 placeholder**：`.textBlockContent[data-empty="true"]::before` 改成绝对定位、pointer-events:none 的纯视觉蒙层，placeholder 彻底与 DOM/innerText 解耦（`frontend/src/modules/book-editor/ui/bookEditor.module.css`）。
3. **空书检测共享 helper**：新增 `model/isRenderableBlockEmpty.ts` 并在 `BlockList.tsx` 中使用 `blocks.every(isRenderableBlockEmpty)` 驱动 hero 空态卡片，让“多个空 block”与“0 个 block”享受一致的 onboarding 流程。
4. **规则与决策同步**：新增 `ADR-137-plan148-placeholder-overlay-and-empty-state.md`，并在 `DDD_RULES.yaml`、`HEXAGONAL_RULES.yaml`、`VISUAL_RULES.yaml` 记录 Plan148 协议；QuickLog Plan148A/B 归档本条执行摘要，保持设计/实现一致。
5. **验证**：`npx next lint --file BlockEditorCore.tsx --file BlockList.tsx --file ParagraphEditor.tsx --file model/isRenderableBlockEmpty.ts` 通过，placeholder overlay 与空态逻辑 lint clean。