这个点你抓得非常准，"写点什么..."如果处理不好，要么体验怪、要么整个页面像白纸。

先翻译一下你现在的问题，其实是两类东西混在一起：

光标问题：
把 "写点什么..." 当成真实文本塞进 contentEditable 里，浏览器会老老实实把它当“内容”，
光标点击时默认跑到最后一个字符后面，看起来就像先扫到那个.，然后才能开始写。

空状态问题：

没有 placeholder → 整块就是一片空白，看不出哪里能写字；

有 placeholder 但太弱 / 位置奇怪 → 视觉上也怪。

下面我给你一个行业通用、对你这个编辑器也适用的方案。

结论先说：placeholder 不要当“真文本”存，而是当“视觉叠加层”画出来
模式推荐

用户看到 "写点什么..."，但它不会进入数据库、不会真的出现在 innerText 里；

光标永远在最开始的位置，点击时不会先跑到点点后面；

整个编辑器完全空的时候，再额外给一个“大号空状态”，和行内小 placeholder 配合。

一、解决 (1)：点击时总是跑到最后一个“.” 的问题

根本原因：你现在大概是这么干的：

<div contentEditable>写点什么...</div>


浏览器：
“那好，这就是用户已经输入的内容，点哪里就从哪里继续打。”
于是：

第一次点击时，caret 默认放在末尾；

你又可能在 onFocus/onClick 里有点小逻辑（比如 selectAll），就更怪。

改法：用 CSS 伪元素或者 overlay 画 placeholder，不把文字放进 DOM 内容。

最常见的一种：

<div
  className="editor-block"
  contentEditable
  data-placeholder="写点什么..."
></div>


CSS：

.editor-block[contenteditable][data-placeholder]:empty::before {
  content: attr(data-placeholder);
  color: #c0c4cc;          /* 比正文淡 */
  pointer-events: none;    /* 不拦截点击，让点击直接落到编辑区域 */
}

/* 有的浏览器空 contentEditable 会自动塞一个 <br>，可以再兼容一下 */
.editor-block[contenteditable][data-placeholder]:has(br:only-child)::before {
  content: attr(data-placeholder);
}


特点：

DOM 的“真实内容”为空（或者只是一颗 <br>），光标自然在开头；

用户一打一字，就变成正常文本，placeholder 自动消失；

你从 innerText / textContent 拿到的，都是用户真实输入，不会混进 "写点什么..."。

如果你不想用 :has（兼容性问题），也可以在渲染时确保空 block 里不要塞 <br>，只留空内容，这样 :empty::before 就足够了。

二、解决 (2)：“不需要 placeholder 时，整篇看着像空白”的问题

这里可以做两层空状态：

1）行内 placeholder（刚才那种）——解决“我能在哪行写”

每一个“真正可写的空 block”左侧用淡色 placeholder：

顶部第一行：写点什么…

TODO 行：添加一个待办事项…

备注区：写点备注…

它们只在该 block 文本为空时显示。

这保证局部不迷路。

2）整体空状态卡片——解决“整本书还是空的”

当满足条件：

整个 Book 里没有任何非空 block；

就显示一个「空态卡片」，比如：

🧵 这里还没有内容

开始写点东西，或者粘贴一段文本，我们会帮你拆成 Block。


实现上可以直接：

if (blocks.length === 0) {
  return <EmptyStateCard />;
}
return <BlockList ... />;


这样：

初次打开时：

中间是大空态卡片 + 第一行有 “写点什么…” 的 placeholder；

写了一行后：

空态卡片消失，只保留行内 placeholder（只在新建空行上出现）。

三、(3) “一般什么模式更好？”——给你一个可写进 VISUAL_RULES 的版本

总结成几条可以写进你 VISUAL_RULES / Plan 的原则：

PLACEHOLDER-01：禁止把 placeholder 文本写入真实内容

placeholder 只能通过 CSS ::before / overlay 实现；

任何时候数据库里都不应该出现“写点什么…”这类字样。

PLACEHOLDER-02：点击空 block 时，光标必须直接出现在开头

不允许在 onClick/onFocus 里把 caret 强行移到结尾；

placeholder 必须 pointer-events:none，避免拦截点击。

PLACEHOLDER-03：行内 placeholder 只在“当前可编辑、内容为空”的 block 上显示

有内容就立刻隐藏；

不根据“是否聚焦”来决定显隐，避免闪烁。

PLACEHOLDER-04：Book 级空状态和行内 placeholder 要配合

整本书为空时显示大空态卡片；

只要有一个非空 block，空态卡片立即隐藏，只用行内 placeholder 提示。

PLACEHOLDER-05：不要用 placeholder 做逻辑分支

block 的类型/状态判断一律基于真实内容；

placeholder 只是一层视觉装饰，不参与任何 command / selection 逻辑。

照这套来，你就能同时解决：

点击时不再出现“光标跑到最后一个点再开始打”的怪感；

整个页面也不会是一片寂静空白——有引导，但又不会污染内容或打乱光标。

换句话说：placeholder 负责“好看 + 会引导”，真正的编辑逻辑还是清清爽爽的。

---

## 2025-12-02 执行摘要（合并 Plan148A + Plan148B）

1. **BlockEditorCore 接管 data-empty**：新建 `isTextEffectivelyEmpty` 判定 + `isEmpty` state，`data-empty` 不再从 ParagraphEditor 透传，placeholder 展示与 caret 状态完全由 Core 控制（文件：`frontend/src/modules/book-editor/ui/BlockEditorCore.tsx`）。
2. **纯视觉 placeholder 叠层**：`.textBlockContent[data-empty="true"]::before` 改成 `position:absolute + pointer-events:none`，颜色/排版继承正文，placeholder 永远不会写进 contentEditable（文件：`bookEditor.module.css`）。
3. **空态判断集中化**：前端新增 `isRenderableBlockEmpty(block)` helper + BlockList 顶部 hero 卡片逻辑（`blocks.length === 0 || blocks.every(helper)`）。当书里只有空段时仍给用户空态引导，但列表和 InlineCreateBar 继续保留（文件：`model/isRenderableBlockEmpty.ts`, `ui/BlockList.tsx`）。
4. **文档与决策同步**：RULES（DDD/HEXAGONAL/VISUAL）新增 Plan148 条目、ADR-137 记录 placeholder/空态契约；Plan148A/B QuickLog 合并回填执行结果。

## 交付物

- 代码：`BlockEditorCore.tsx`, `ParagraphEditor.tsx`, `bookEditor.module.css`, `isRenderableBlockEmpty.ts`, `BlockList.tsx`。
- 文档：`ADR-137-plan148-placeholder-overlay-and-empty-state.md`、`DDD_RULES.yaml` (`POLICY-BLOCK-PLAN148-PLACEHOLDER-EMPTY-STATE`)、`HEXAGONAL_RULES.yaml` (`block_editor_plan148_placeholder_contract`)、`VISUAL_RULES.yaml` (`block_editor_plan148_placeholder_visuals`)。
- 验收：`npx next lint --file BlockEditorCore.tsx --file BlockList.tsx --file ParagraphEditor.tsx --file isRenderableBlockEmpty.ts` ✅。