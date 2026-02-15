对，你现在遇到的最大问题其实不是“这个 px 调一下没效果”，而是：
同一类间距压根没有被同一套 token 管着，有的在 blockItem 上、
有的在 p / h1 / li 默认 margin 里，有的又写死在 todo / list 专用样式里。

所以我们先把“所有间距相关的 token 名单”定出来，你后面就可以按表排查：
凡是编辑器里的 margin / padding / gap / line-height，没有用到这些变量的，
都属于“漏网之鱼”。

下面这套表是给 块编辑器 用的 token 设计（可以放在 :root 或编辑器根节点上）：

1. 基础间距刻度（primitive scale）
:root {
  /* 基础单位：2px/4px/8px 梯度 */
  --wl-space-0: 0px;
  --wl-space-1: 2px;
  --wl-space-2: 4px;
  --wl-space-3: 8px;
  --wl-space-4: 12px;
  --wl-space-5: 16px;
  --wl-space-6: 20px;
}


这几个只当“原材料”，不要直接在组件里乱用，而是再起语义别名。

2. 块与块之间的垂直间距
:root {
  /* 正常 section 间距：段落之间、段落 ↔ list、段落 ↔ quote */
  --wl-space-block-section: var(--wl-space-3);   /* 8px */

  /* 紧凑模式：比如段落 ↔ bullet list 视为同一段叙述 */
  --wl-space-block-tight:   var(--wl-space-2);   /* 4px */

  /* section 顶部 / 底部 padding（块内部的“呼吸感”） */
  --wl-block-padding-y:     var(--wl-space-2);   /* 4px */

  /* 编辑器最外层与卡片边框的内边距 */
  --wl-editor-padding-y:    var(--wl-space-4);   /* 12px */
}


要做的事：

.bookEditor_blockItem 上的 margin-top / margin-bottom → 用 --wl-space-block-section 或 --wl-space-block-tight。

块内部的 padding-top / padding-bottom → 统一用 --wl-block-padding-y。

所有 p / h1~h4 / ul / li / blockquote 的 浏览器默认 margin-top/bottom 一律清 0，
否则就会出现“绿框没变、字的位置却在晃”的叠叠乐。

3. 行高 / 文本内行间距（段内）
:root {
  --wl-line-height-body:   1.6;
  --wl-line-height-tight:  1.4; /* 需要更紧密的块：todo / list / quote 内部 */
}


普通段落文本：line-height: var(--wl-line-height-body);

todo / list / 引用内：line-height: var(--wl-line-height-tight);
这样可以在 不调 block 间隔 的前提下，把一坨 todo 看起来更紧凑。

4. 列表 / bullet 专用 token
:root {
  /* 列表内容相对正文的缩进 */
  --wl-list-indent:        20px;

  /* 同一个 ul/ol 里 li 与 li 之间的垂直 gap */
  --wl-list-item-gap:      var(--wl-space-2);   /* 4px */

  /* 列表块与前后段落之间，是按“紧凑”还是“正常 section” */
  --wl-space-list-before:  var(--wl-space-block-tight);
  --wl-space-list-after:   var(--wl-space-block-tight);
}


要做的事：

ul, ol 外层：margin-block: 0; padding-inline-start: var(--wl-list-indent);

li + li：用 margin-top: var(--wl-list-item-gap);，别再写死 4px。

列表这个 blockItem 的上下间隔：用 --wl-space-list-before/after，
而不是直接 8px/4px。

5. Todo block 专用 token
:root {
  /* checkbox 和 文本 的左右间距 */
  --wl-todo-checkbox-gap:  var(--wl-space-2);   /* 4px */

  /* todo 行与行之间（同一 todo 块内部） */
  --wl-todo-item-gap:      var(--wl-space-1);   /* 2px 或 4px 看你偏好 */

  /* todo 块与上下普通段落之间（外部） */
  --wl-space-todo-before:  var(--wl-space-block-tight);
  --wl-space-todo-after:   var(--wl-space-block-tight);
}


实现时：

label 或 .todoItem：display:flex; align-items:flex-start; column-gap: var(--wl-todo-checkbox-gap);

.todoItem + .todoItem：margin-top: var(--wl-todo-item-gap);

todo 的 .blockItem 外层：用 --wl-space-todo-before/after 控制。

6. 引用（Quote / Callout）专用 token
:root {
  /* 引用块左边的竖线缩进 / 内边距 */
  --wl-quote-border-gap:   var(--wl-space-2);  /* 4px */
  --wl-quote-padding-y:    var(--wl-space-2);  /* 上下内边距 */

  /* 引用块与前后块之间的间距 */
  --wl-space-quote-before: var(--wl-space-block-section);
  --wl-space-quote-after:  var(--wl-space-block-section);
}

7. 统一排查 checklist（你可以照着在 CSS 里搜）

在 bookEditor.module.css / 相关组件里，对下面几种写法逐一排查：

所有 margin-top / margin-bottom / margin-block / padding-* 上的裸 px 数字：

如果是块与块之间：→ 换成 --wl-space-block-section / tight / todo-before / list-before 等。

如果是块内部的“行距感”：→ 换成 --wl-block-padding-y、--wl-list-item-gap 等。

所有 ul / ol / li / p / h1~h4 / blockquote 默认 margin：一律清零，
然后只用 .blockItem + token 管理垂直间距。

所有 line-height: 1.xx：

段落：var(--wl-line-height-body)

todo/list/quote：var(--wl-line-height-tight)

你现在可以：

把上面这套 token 直接贴进 VISUAL_RULES.yaml 或 variables.css。

在编辑器 CSS 里全局搜 margin:, padding:, line-height, 一个个对照表替换。

替完之后再用 devtools 看：绿色外框只剩下一套 margin / padding，
而且所有数值都能追溯到上述 token，就说明“叠叠乐”基本清完了。

等你把这些都 token 化之后，再调“段落 ↔ 列表紧一点”、“todo 再密一点”，
就完全是改两三个变量的事，不会再出现“我改了 4px 但肉眼没变化”的灵异现象了。

---

## 2025-12-03 落实记录

1. **Primitive + 语义 token 已落地**：`frontend/src/modules/book-editor/ui/bookEditor.module.css` 在编辑器根节点注入 `--wl-space-0..6` 与全部语义别名（block-section/tight、list/todo/quote before|after、line-height、list-indent、todo-gap、quote-padding）。旧名 `--wl-space-section/tight` 通过 alias 过渡（见 VISUAL_RULES `block_editor_vertical_rhythm`）。
2. **UA margin / 行距统一清零**：`.blockItem :is(p,h1~h6,ul,ol,li,blockquote,.textBlockShell,.textBlockContent)` 全部 `margin-block:0;padding:0`，段落/列表/待办内部 line-height 分别指向 `var(--wl-line-height-body|tight)`，消除了裸 `1.xx`。
3. **列表 / Todo / Quote spacing token 化**：`li + li`、`.todoRow + .todoRow`、`ul/ol` 缩进、引用 padding 均只引用 doc 中列出的 token，没有残留 `px`。VS Code 全局搜索 `bookEditor.module.css` 的 `margin:`/`padding:`/`line-height` 时，命中要么是 token，要么是 0。
4. **邻接规则驱动 block 间距**：`.blockItem + .blockItem` 以及 `[data-kind]` 邻接组合已经覆盖段落/标题/列表/待办/引用，分别绑定 `--wl-space-block-section`、`--wl-space-block-tight`、`--wl-space-list-*`、`--wl-space-todo-*`、`--wl-space-quote-*`。
5. **Spacing Sandbox 校验**：`frontend/src/app/dev/spacing-test/page.tsx` 复用同一 CSS，展示“Heading→Paragraph”“Paragraph→List”“Quote Divider”“Todo Stack”四张卡片，TOKEN_METADATA 列出 Plan152A 全体 token，QA 通过 `/dev/spacing-test` 即可校验。
6. **规则同步**：VISUAL_RULES / DDD_RULES / HEXAGONAL_RULES 已追加 Plan152 token 表、alias 策略与 Sandbox 必选流程；Plan152 相关变更若未附截图会在评审阶段被拒绝。

> 下次自检：运行 VS Code 搜索 `margin-top: [0-9]`、`line-height: 1.`、`padding: [0-9]px`，如在 `bookEditor.module.css` 中仍能找到，视为 Plan152A 回归，需要立即映射到上述 token。