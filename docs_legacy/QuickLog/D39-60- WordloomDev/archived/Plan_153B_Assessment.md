这个 Plan 写得已经很「Wordloom 味」了，方向基本是对的，我帮你从「节奏设计」的角度挑一挑细节，看哪里可以再收紧一点。

先给结论

✅ 大方向正确：把「块的外壳高度」抽成语义化 token、统一命名规则、旧 token 做 alias 过渡，这跟我们前面聊的「shell 管内部高度，blockItem + gap 管节奏」是同一条路。

✅ 步骤结构也对：先 token、再替换 CSS、再扩展 dev/spacing-test、最后更新 Plan/ADR，这一套是可执行的。

需要补几笔的地方主要有三个：

清楚区分：节奏类 token vs shell 高度类 token

段落壳的 padding 要不要长期保留？

list / todo / quote 的壳和 before/after token 的分工再写清楚一点

下面分块说。

1. 命名规范：再加一条「作用域」说明会更清晰

你现在的规则是：

--wl-{域}-{shell}-{元素}-{属性}
例：--wl-block-shell-paragraph-padding-y、--wl-list-shell-padding-inline……

建议在 Plan 里再明确一句：

「shell 系列 token 只描述单个 block 内部的 padding / 内联缩进，不参与 block 之间的节奏。
block 之间的节奏只由 --wl-space-* / --wl-space-list-before/after 等 token 决定。」

这样以后你自己翻 Plan 的时候，一眼就知道：

--wl-block-shell-* = 卡片 / 壳本身长什么样；

--wl-space-* = block 之间隔多远。

这会避免未来再出现「壳上又有 padding-bottom、外面还来一刀 margin-top」这种叠加。

命名本身我觉得没问题，block-shell / list-shell / todo-shell / quote-shell / inline-shell 都挺直觉的。

2. 关于段落壳：paragraph-shell-padding-y 要不要设成 0？

你草案里把 paragraph 也纳入：

--wl-block-shell-paragraph-padding-y

从「节奏 owner 已经是 shell 的 row-gap」这个设定出发，其实普通段落壳的 padding-y 完全可以长期保持为 0：

段落栈的视觉 rhythm 交给 row-gap: --wl-space-block-tight。

段落壳自己只控制一些横向特性（对齐、左右内边距、背景等），纵向不加料。

所以我建议在 Plan 里写死一个设计选择：

「普通 paragraph block 的 --wl-block-shell-paragraph-padding-y 默认为 0px，
不用于控制段落栈之间的垂直距离。
未来如果需要“段落卡片”（例如高亮段落），会另起 data-kind="paragraph_card" + 对应 shell token。」

这样你在 Step 2 替换 CSS 的时候，就不会又把段落壳的 padding 塞回来。

3. list / todo / quote：壳的职责 vs before/after token

从 Plan153 那条线来看，你现在准备加的壳类 token 大致是：

--wl-list-shell-padding-y / inline

--wl-todo-shell-padding-y

--wl-quote-shell-padding-y

--wl-inline-insert-shell-padding-{x,y}

这里我会建议你在 Steps 下面加一段简要分工说明，例如：

list / todo / quote shell 的 padding 只负责：

让项目符号 / checkbox / 引号 / inline 卡片的内部呼吸空间舒服；

不改变 blockItem 之间的「节奏单位」。

「进入列表 / 离开列表 / 进入引用 / 离开引用」的间距，统一使用：

--wl-space-list-before / --wl-space-list-after

--wl-space-quote-before / --wl-space-quote-after
通过在第二个 block 上加 margin-top 实现。

这样你在实现 Step 2 的时候逻辑就很清晰：

/* 基础节奏：所有 blockItem 栈的 row-gap */
.bookEditor_shell {
  display: flex;
  flex-direction: column;
  row-gap: var(--wl-space-block-tight);
}

/* list 壳：只管内部 padding */
.bookEditor_blockItem[data-kind="bulleted_list"] .bookEditor_blockShell {
  padding-block: var(--wl-list-shell-padding-y);
  padding-inline: var(--wl-list-shell-padding-inline);
}

/* 进入列表：额外 before */
.bookEditor_blockItem[data-kind="bulleted_list"] {
  margin-top: var(--wl-space-list-before);
}

/* 离开列表：额外 after（在下一个 block 上加） */
.bookEditor_blockItem[data-after="list"] {
  margin-top: var(--wl-space-list-after);
}


把这类「谁负责什么」写在 Plan153 / 这个新 Plan 里，之后改 CSS 的时候就不容易打架。

4. 你列的 Steps：逐条点评 + 小补充
Step 1：在 bookEditor.module.css 新增 shell token

👍 完全赞同。可以再明确一点：

token 区按类别+作用分组：block-shell-* 一组、list-shell-* 一组……

在注释里标注：
/* Shell tokens: control internal padding of block shells; do NOT change inter-block rhythm. */

未来你去翻 CSS 的时候，这行注释会救你命。

Step 2：替换 block selector 的 padding

这里我建议你在草案里加两条 guard rail：

普通 paragraph / heading 的纵向 padding 清零：

[data-kind="paragraph"] .bookEditor_blockShell,
[data-kind^="heading_"] .bookEditor_blockShell {
  padding-top: 0;
  padding-bottom: 0;
}


只保留左右 padding 或者完全交给 page layout 管。

quote/list/todo/inline 才使用新 shell token：

[data-kind="quote"] .bookEditor_blockShell {
  padding-block: var(--wl-quote-shell-padding-y);
}

[data-kind="bulleted_list"] .bookEditor_blockShell {
  padding-block: var(--wl-list-shell-padding-y);
  padding-inline: var(--wl-list-shell-padding-inline);
}


这样一来，“壳 token 重构”不会无意中改坏 paragraph/heading 的视觉 rhythm。

Step 3：扩充 page.tsx + 「Block Shell 密度卡」

这个很好，甚至可以顺便做一个「Shell × Rhythm Matrix」：

X 轴：Paragraph / List / Todo / Quote / Inline

Y 轴：Normal / Tight / Dense 等不同组合

每一格展示：

shell 内部 padding 效果；

与上下段落的 before/after 效果。

这会让你以后调整 token 的时候非常直观。

小补充：在 TOKEN_METADATA 里把每个 shell token 标一行说明，比如：

{
  name: "--wl-quote-shell-padding-y",
  group: "shell/quote",
  description: "Vertical padding inside quote shell; does not affect inter-block spacing."
}


这对 Copilot 也非常友好。

Step 4 & 5：更新 Plan / 运行 spacing-test

这两步没问题，可以再加一句：

在 spacing-test 页面上截图「Paragraph → List → Paragraph」和「Paragraph → Quote → Paragraph」，附在 Plan / ADR 里当「视觉基准」。以后改 token 时能肉眼对比是不是偏了。

5. Further Considerations 的两个点

heading 语言/字号差异 → 追加 heading 专用 shell token

这个想法是对的，建议先写成「暂不实现，只在 Plan 里记为可选扩展」，否则现在就会扯到「中文多行、英文单行」之类的复杂情况，把重构 scope 拉大。

alias 何时移除

你写的：

等 DOM/CSS 搜索不再出现 --wl-block-padding-y 后，在 ADR 宣布淘汰

可以再加一句「下一次大版本 bump 时顺手删 alias」，例如：

「计划在 v3.x → v4.0 的版本 bump 中移除 --wl-block-padding-y alias。
在此之前，禁止在新代码中引用旧 token。」

这样未来你做 release note 的时候有锚点。

总结版建议（可以直接贴回 Plan 里当补充）

明确一句：

「Shell tokens（--wl-*-shell-*）只控制 block 内部 padding；
block 之间的距离全部由 --wl-space-* / --wl-space-*-before/after 决定。」

段落 / heading 壳的 padding-y 默认保持为 0，只改 quote/list/todo/inline。

Step 2 里写清：

先全局清掉 paragraph/heading 壳的纵向 padding；

只在 quote/list/todo/inline 上挂新 shell token。

spacing-test 页面增加「Shell × Rhythm」的可视化矩阵，用来验证 before/after token 和 shell token 的搭配是否符合 Plan153 描述。

整体来说，这个 Plan 已经是「可以交给未来的你看也不迷路」的级别了，现在加的这些小注释，是帮你防止下一轮重构时又踩回老坑。