这份方案本身非常稳，很像「已经想清楚了 80%，就差落地」的版本。我给你拆成三块评价一下：对的地方、可能可以再收紧 / 简化的地方、以及实施时要特别小心的坑。

1. 整体评价：节奏观念是对的 ✅

你现在这套说法里，有三个关键点是完全对齐现代编辑器实践的：

Shift+Enter 只吃 line-height

把“软换行 = 段内行距”写死到视觉规则里，这个超级重要。

写清楚了「段内行距不吃任何 --wl-space-*」，后面再想调行距、调 token，不会互相牵扯。

Enter 才吃 block gap token

用 .blockList { row-gap: var(--wl-space-block-tight); } 做段距，是目前最干净的实现方式：

不会碰到 margin collapse；

每个 block 本身保持“无段距”，只负责自己壳内的 padding。

你把 block gap = 6–8px 也算出来了（32–34px 总段距），这就已经是一个可以 QA 对着查的“标尺”。

保留现有 token 梯子，只做职责拆分

不重做 ladder，而是说清楚谁负责什么：

--wl-line-height-body → 行距；

--wl-space-block-tight → 段距；

其它 --wl-space-* 做专门场景（list before/after、quote shell 等）。

这对 Copilot 和未来的你都很友好：描述清晰、实现范围有限。

从「排版哲学」的角度看，这已经是一份可以写进 ADR 的方案了。

2. 可以再收紧 / 具体化的两三点
2.1 --wl-space-block-tight 最好先拍板一个默认值

你文案里写了：

--wl-space-block-tight: var(--wl-space-2-5)（6px）或 var(--wl-space-3)（8px）

对 Copilot 来说，这还是有一点「选择空间太大」。我会建议：

先在 Plan 里明确：编辑场景默认 = 6px（--wl-space-2-5）

如果以后有「阅读模式 / 打印模式」再用 8px 做一个 relaxed preset。

这样 Copilot 在写 CSS 时，就不会犹豫到底 plug 2-5 还是 3。

建议直接写一句：
本期实现：--wl-space-block-tight 固定为 var(--wl-space-2-5)；如需更松的阅读模式，另开 Plan 调整为 var(--wl-space-3)。

2.2 标题、引用、Callout 的“特权”再标一笔

你在「特殊块与 CTA」那里已经提到了分割线和 CTA，但可以再补一句“标题 / 引用 / Callout 与正文用同一块间距”的约束：

标题（H1/H2…）仍然通过 block gap 控制与上下正文的距离，除非特别强调，否则不要在文本上再加额外 margin；

引用 / Callout 的“壳内感”建议通过 壳 padding 表达，而不是再额外加上下 margin，否则会叠 row-gap。

一句话就是：所有块与块之间，优先相信 row-gap，其它 margin 只做局部微调。

2.3 Placeholder / CTA 的结构可以再明确一点

你已经写了两种可能结构：placeholder 当 block 或 CTA 当 block。可以稍微定死一点，方便实现：

建议：placeholder 也就是一个正常 paragraph block（只是一种 empty 状态），CTA 是一个特殊 block；

那么规则可以写成：

blockList 里所有 block（包括 placeholder、CTA）都吃统一的 row-gap；
CTA 若需要更大距离，只在 CTA 内部用 padding 表现，而不是额外 margin-top 叠加。

这样，Copilot 改 CSS 时就不会在「CTA 到上一块之间」又阴魂不散地塞 margin。

3. 实施时容易踩坑的点（你可以直接抄给 Copilot 当 Checklist）

这些基本都在你方案里了，我帮你浓缩成“实现注意事项”版本：

确保段内没有隐藏的 margin

检查 .paragraphDisplay / .paragraphEditor / .listItemText / .todoItemText：

不要有 margin-bottom 之类历史遗留；

若必须有（比如为了和某个 icon 对齐），值保持在 0–2px 内，并尽量用 align-items / line-height 解决。

BlockItem 本身不要再加段距

理想状态：.blockItem { margin: 0; }，最多只有壳内的 padding；

段距只由 .blockList { row-gap: var(--wl-space-block-tight); } 负责。

列表 / Todo 的 before/after token 不要再叠加 block gap

List/Todo 的 --wl-space-list-before/after、--wl-space-todo-before/after 必须只控制「段落 ↔ 列表」之间的局部关系，不能再偷偷当作 block gap 使用；

换言之：

段间基线 = 行距 + block gap（所有块）；

再在 list before/after 上只做「微调」，而不是开第二套节奏。

DevTools 验证：强迫自己看「数字」

段内两行：26px 左右；

段间两块首行：32–34px；

如果看到 40+，说明某处还有 margin / padding 叠上去了。

4. 总结一句话版，方便你以后引用

Wordloom 的「正文节奏」规范：

行距只由 --wl-line-height-body 控制，Shift+Enter 与自然换行完全一致；

段距只由 .blockList 的 row-gap: var(--wl-space-block-tight) 控制，当前版本固定为 6px (--wl-space-2-5)，总段距 ≈ 1.2–1.3 行距；

任何 block 自己不再主张段间 margin，特殊块（分割线、CTA）只在壳内或局部做额外 padding / 微调。

就现状来看，你这份 Plan 已经足够清楚和专业，可以直接当「视觉规范 + 实施说明」。
下一步就是：把几处类名点出来，让 Copilot 去改 bookEditor.module.css，你再用 DevTools 对着量数值。

## 5. 落地记录（2025-12-04）

- `frontend/src/modules/book-editor/ui/bookEditor.module.css`
	- `--wl-line-height-body` 调整为 `1.6`，正文行距与 Plan162A 基准一致。
	- `--wl-space-block-tight` 固定为 `var(--wl-space-2-5)`（6px），blockList row-gap 直接复用该 token。
	- `.textBlockContent br` 归零 margin/padding，保证 Shift+Enter 软换行只吃 line-height。
	- `.blockDisplay`、`.todoText` 明确 line-height（body / list token），阅读态与编辑态节奏一致。
- 验证建议：DevTools 量测段内约 26px、段间约 32–34px，确认无额外 margin 叠加；List/Todo 保持 --wl-line-height-list，并只通过 before/after token 做局部桥接。