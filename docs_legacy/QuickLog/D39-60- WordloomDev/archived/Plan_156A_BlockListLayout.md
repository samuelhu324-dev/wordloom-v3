先说结论：

默认行为应该长得像你截图里后面的那串 list（正常块间距）。
像前面这种“诗歌式紧贴”的 list，不适合作为默认，只能当一个很小众的特殊样式。

下面我分三块说：现在为什么会出现这两种效果、这种“诗歌 list”有没有用、Wordloom 里 list 快捷键应该怎么设计。

一、为什么会出现（1）和（2）两种完全不一样的 list？

从你描述看：

（1）是：在已有 list 后直接按 Enter，让编辑器自己“续写”出来的内容
→ 很紧，看起来像上一行的延长，整块像诗歌/歌词。

（2）是：光标在空段落开头，输入 - 然后 Enter 触发的自动列表
→ 前后有一丢丢 block 间距，看着像「独立的列表块」。

本质上是两套逻辑在打架：

「续写同一段」逻辑
编辑器认为：你还在同一个 narrative chunk 里，只是换了句式/结构，所以只给你行级别的间距（line-height）。

「新块」逻辑
触发 - → list，是在开一个新的 block，前后都会吃 --wl-space-block-list-before/after 那些 token，看起来更像「一段话下面跟了一段列表」。

所以你当前的 token/规则应该是类似：

Enter 在某些情况下走了“同段落紧凑模式”（只用 line-height / block-tight）

- + Enter 走的是“列表块模式”（附带 list-before/after）

效果就是：用户心里觉得是“同一个动作 —— 生成列表”，
引擎心里却分了两种不同物理：行 vs 块，于是视觉变成两种风格。

二、（1）这种“诗歌 list”有没有适用场景？

有，但很小众，而且语义不一定应该叫 list。

可能的场景：

引用里的“分行强调”：
例如一个台词 / 诗句分三行，每行前面加短横线：

— A
— B
— C
比较像排版上的修辞，而不是机器眼里的 <ul><li>…</li></ul>。

极度紧凑的「行级 bullet」：
有些人会写：

优先级：
· 紧急
· 重要
· 次要
希望子弹行几乎和普通文本齐平，看起来像一段话内部的节拍，而不是整个版面结构的块。

但问题是：
一旦你把它当真正 list 来对待（统计、导出、转 markdown、做翻译对齐），这类“诗歌形态”反而会搞事，因为它的视觉行为像段落，但语义行为是列表。

所以更合理的做法是：

MVP 里 不要给它独立路径；

以后如果真有需求，可以做成一种「样式变体」：

叫 “紧凑列表 / 行内列表 / Poem bullets” 之类；

和普通 list 共用同一个语义（都是 <li>），但 spacing preset 不一样；

严格通过样式切换进入，不通过模糊的 Enter 分支进入。

现在这种「按 Enter 随机获得诗歌版」的方式，更像是bug/未决行为，不是 feature。

三、Wordloom 里 list 快捷键应该怎么设计更靠谱？

可以参考 Word / Notion / Google Docs 的行业习惯，但结合你的“block+token 节奏系统”，整理成一套清晰心智模型：

1. 行内 vs 块内 vs 块间：三层节奏分工

行内（soft break）

按 Shift+Enter：在同一个 list item 里换行。

用 line-height 和少量 item-gap 控制，不改变 block 间距。

适合一条长句、诗歌、歌词。

item 之间（list 内部）

按 Enter：新建同级 list item，使用 --wl-list-item-gap。

视觉上：比段落行距略大一点，但明显是“同一个列表”的一部分。

block 之间（列表整体 vs 上下段落）

列表整体前后的节奏：
使用 --wl-space-block-list-before / --wl-space-block-list-after。

Paragraph → List / List → Paragraph 无论通过哪种输入方式，都应该吃同一组 token，不要一会紧一会松。

2. 快捷键和自动语法建议

输入类：

行首输入 - + 空格：变成无序列表，立刻应用「列表块」的 before/after 间距。

1. + 空格：有序列表。

- [ ] + 空格：todo 列表。

Enter：

在非空 list item 内：新建 item。

在空 item 内再次 Enter：退出列表，变成普通段落（行业通用）。

结构类：

Tab / Shift+Tab：缩进 / 反缩进，变子列表 / 回到父级。

Ctrl+/ 或工具栏切换：把选中 block 转成列表或段落。

密度 / 风格（可以以后再加）：

不建议一开始就搞「诗歌 list」的快捷键。

如果以后真需要，可以做：

在样式面板里有一个「列表密度：normal / compact / poem」；

或者在 block 上加 data-density="compact"，然后 spacing tokens 切另一套；

但快捷键仍然是 - + 空格，只是密度 preset 不同，而不是完全不同路径。

四、对你现在这个具体画面怎么判断？

你说：

（3）我个人感觉用户习惯会倾向于（2）……
（4）但是（1）这种间距有适用场景吗？

我的建议是：

短期（当前版本）：把（1）当成 bug/未定义行为处理

无论是按 Enter 续 list，还是 - + Enter 新建 list，
→ 生成的列表块前后应该使用同一组 --wl-space-block-list-before/after；
→ 视觉上统一成你现在觉得“正常”的那种版本（2）。

也就是：统一语义 + 统一 token，不要让「生成路径」决定 spacing。

长期（有朝一日做高级样式）：可以考虑抽象出「紧凑列表/诗歌列表」

当用户明确选择这种样式时，把 block 标记为 data-list-style="poem"；

spacing 走另一套 tokens：
--wl-space-block-list-before-poem、--wl-list-item-gap-poem 等；

但即便如此，输入路径仍然是同一套快捷键，只多了一个样式层，而不是完全不同物理。

小结一句话

默认：让所有 list 路径（Enter 续写也好、-+Enter 也好）都走同一套“正常块间距”的 physics，这是对绝大多数用户、绝大多数文档最安全的选择。

“诗歌那种紧贴 list”有存在价值，但应该是一个显式的样式选择，而不是靠「某种神秘按键路径」触发的隐藏模式。

技术上，把所有 spacing 收进 --wl-space-block-*/--wl-list-item-gap 这批 token，保证不同创建路径只改内容、不改 physics，你的 jitter 和“诗歌错杀”问题就会少很多。

///////////////////////////////////////////////////////////////////

Plan156A 落地计划（2025-12-03）

1. 盘点所有列表入口
	- 枚举 `- + 空格`、`1. + 空格`、`- [ ] + 空格`、工具栏按钮、已有列表里按 Enter 续写、从段落切换成列表的转换函数。
	- 标记每个入口当前是否只应用 line-height（行级延伸）或已经吃到 `--wl-space-block-list-before/after`（块级物理）。

2. 固化 tokens 与 invariant 注释
	- spacing tokens 文件中直接写明：`row-gap + list-before >= 0`、`row-gap + list-after >= 0`、`list item gap` 只能通过 `--wl-list-item-gap` 调整。
	- 把“所有列表创建路径共享同一套 list-before/after + item-gap，不允许因为输入方式不同而改变 block 间距”写进注释与 VISUAL_RULES/ADR。

3. 改造编辑逻辑，统一走列表块物理
	- 不论是自动语法还是 Enter 续写，最终都调用同一个 `createListBlock`（或等价方法），由它给 block 标记 `data-kind="bulleted_list"|"numbered_list"|"todo_list"` 并套用统一 spacing。
	- `Enter` 在非空 list item 中只新增一个 item，退出列表由“空 item + Enter”触发；中途不再切到“诗歌模式”。

4. 明确软换行和块换行的分工
	- `Shift+Enter` = 同一 `li` 内的软换行，仅受 `line-height` 支配。
	- `Enter` = 新建 item；若当前 item 为空则退出列表，转回段落，并自动使用段落 block tokens。

5. 诗歌列表作为未来样式钩子
	- 当前版本不暴露入口，只在样式层预留 `data-list-style="poem"`/`data-density="compact"` 以及 `--wl-space-block-list-before-poem` 等命名。
	- 未来若要启用，只能通过显式样式切换，不走隐晦的键盘分支。

6. 给 Copilot 的提示
	- 在 Plan/QuickLog 末尾写清：
	  - “复制 Plan156A：统一列表创建路径，所有列表块的 spacing 只由 tokens 决定。”
	  - “Shift+Enter 仅用于软换行，Enter 仅用于新 item/退出列表。”
	  - “任何尝试创建紧贴列表时，先确认是否应该用未来的 `data-list-style="poem"`，MVP 默认禁止。”

做到以上 6 步，列表再怎么创建/续写都只会改变内容，不会再因为输入路径不同而摇摆在两套 spacing 之间，后续要复刻或回滚时也只需要改 tokens 与 Guard 逻辑，不必再追踪隐形分支。