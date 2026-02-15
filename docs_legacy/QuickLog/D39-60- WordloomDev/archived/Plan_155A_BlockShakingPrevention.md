这个问题问得很关键，其实已经从「怎么调间距」升级成「怎么写不会害死未来自己的布局规则」了。

先翻译一下现在 Copilot 跟你说的话，再顺便把“防抖动规则”变成可以喂给 Copilot 的东西。

1. 现在为啥会抖？

你截图里它说的核心是这句：

我们把 --wl-space-block-list-before 设成 calc(var(--wl-space-1) - var(--wl-space-3))（= -6px），
而 .bookEditorShell/.blockList 继续用 row-gap: var(--wl-space-block-tight)（2px）做节奏。

然后又有规则：

:is(.bookEditorShell, .blockList)
  .blockItem[data-kind="paragraph"]
+ .blockItem[data-kind="bulleted_list"] {
  margin-top: var(--wl-space-block-list-before); /* -6px */
}


等价于：

父容器先把相邻 block 拉开 2px（row-gap）；

进入列表时，再给列表这个 block 一个 -6px 的 margin-top；

实际间距 = 2px + (-6px) = -4px（= 列表往上顶 4px）。

当你切到编辑态，浏览器会重新算：
“这个 block 的内容高度、是否换行、是否多一行 bullets、row-gap + margin 叠加后到底是多高？”

这个重新算高度的过程本身没错，但因为你把间距搞成了“负到超过 row-gap”，所以每次内容增减，列表和上面那段文字就会来回“跳”。

要防抖动，本质上就一条物理定律：

row-gap + margin-top >= 0
（至少别往上顶超出父容器给你的 gap）

对于列表，就是：

--wl-space-block-list-before >= - --wl-space-block-tight


你刚才的做法是直接跑去了 -6px，超出这一条线，就 jitter 了。

2. 把它变成一条「可被 Copilot 理解」的规则

Copilot 不是看心情工作的，它很吃注释 + 命名。
你可以这样做：

2.1 在 tokens 文件里写死这个“不抖动不等式”

例如在 spacing-block.css 顶部：

/* Block rhythm tokens
 *
 * Invariants:
 *  - block-list-before >= -block-tight  (no negative space beyond row-gap, to avoid jitter)
 *  - all before/after gaps are expressed via --wl-space-block-* tokens (no shell tokens here)
 */

:root {
  /* primitive ladder already defined above */

  --wl-space-block-tight: var(--wl-space-1);       /* 2px */
  --wl-space-block-list-before: var(--wl-space-0); /* 0px: >= -tight ( = -2px ) */
  --wl-space-block-list-after:  var(--wl-space-1); /* 2px */
  ...
}


关键是那两行英文注释：

/* Invariants:
 *  - block-list-before >= -block-tight  (no negative space beyond row-gap, to avoid jitter)
 */


之后你再对 Copilot 说：

“调整段落 → 列表的 before gap，让它更紧一点，但必须遵守我们在 tokens 里那条 invariant（block-list-before >= -block-tight）。”

它会去读上面那段注释，按这个范围帮你算数。

2.2 给「危险值」起一个带语义的名字

如果你真的想玩负 margin（比如想做极限紧贴效果），可以这样命名：

:root {
  --wl-space-block-tight:       var(--wl-space-1);      /* 2px */
  --wl-space-block-list-before-safe-min: calc(-1 * var(--wl-space-block-tight)); /* -2px */

  /* 真正给组件用的数值仍然放在 list-before 里 */
  --wl-space-block-list-before: var(--wl-space-0);      /* 0px，现在在安全范围内 */
}


以后你要调得更激进一点，可以跟 Copilot 说：

“把 --wl-space-block-list-before 调到接近 --wl-space-block-list-before-safe-min，但不要超过它。”

它就知道：最小只能到 -2px，再往下就是违背 invariant。

2.3 在使用的地方再补一句「别超过这个值」

例如你真正用到 before 的那段 CSS：

/* Paragraph → List: use block-list-before gap; never go below -block-tight or jitter appears */
:is(.bookEditorShell, .blockList)
  .blockItem[data-kind="paragraph"]
+ .blockItem[data-kind="bulleted_list"] {
  margin-top: var(--wl-space-block-list-before);
}


这里那句英文就是专门给 Copilot 和“未来的你”看的：

“never go below -block-tight or jitter appears”

再配合 tokens 文件里的 invariant，你基本把「负 gap 会抖」这件事刻在系统记忆里了。

3. 让 Copilot 真正「同步」这条规则的几个实用招数

再总结成几条你可以立刻用的习惯：

所有间距都在 tokens 文件定义，组件里只用变量，不直接写 calc(...)
你刚刚这次 jitter 就是直接写了
margin-top: calc(var(--wl-space-1) - var(--wl-space-3)) 这种“魔法数表达式”。
以后写成：

--wl-space-block-list-before: var(--wl-space-0); /* 希望更紧就只改这里 */


然后跟 Copilot 讨论“把这个变量调到多大/多小”，它才有机会帮你守规则。

把节奏规则收进 VISUAL_RULES / ADR
你现在已经在 Plan 154A 里写节奏了，可以多加一句：

“To avoid layout jitter, any negative before/after gap MUST be greater than or equal to -block-tight.”
Copilot 在 repo 里学到这句，以后你问：
“Make list-before slightly negative, still respecting the no-jitter rule.”
它就会自动用 -block-tight 当边界。

在 spacing-test 页面加一个「Jitter Guard」小卡片
比如专门有一块叫：

“List jitter guard: row-gap + list-before >= 0”
下面展示当前 token 数值：
row-gap = 2px; list-before = 0px; sum = 2px (safe)
这样你以后眼睛一扫就知道有没有玩过火。

4. 最后给你一句可以直接对 Copilot 说的话

以后你想改段落 ↔ 列表的间距，可以直接这样开口（写在注释里效果更好）：

We use --wl-space-block-tight as the base row-gap between blocks.
When adjusting list-before / list-after, keep the invariant:

  row-gap + list-before >= 0  (no jitter)
  row-gap + list-after  >= 0

Please update the spacing tokens, not the raw CSS values, and respect this constraint.


这段话本身就可以复制进 Plan / VISUAL_RULES / Token 文件的注释里，Copilot 和未来的你都会看得懂。

一句话收尾：
让「不抖」这条物理定律变成 Token 文件里的 invariant，再用注释 + 命名把它钉死，Copilot 才有机会帮你一起守规矩，而不是每次你俩一起手滑。

///////////////////////////////////////////////////////////////////

这段 Copilot 的建议方向是对的，但可以再升级一小步，让它变成「系统级不抖原则」，而不是只修这一处。

先翻译一下它在讲什么：

现在 ParagraphEditor 里的 .textBlockContent 用的是 line-height: var(--wl-line-height-body)，
列表展示态 .todoListItem 已经收紧到 line-height: var(--wl-line-height-tight)。
所以一旦进入编辑态 / 按 Enter 拆成多个 bullet，行高从 1.35 → 1.55（反正就是 A→B），整个块高度立刻变高，就抖了。
解决方案：让编辑态的 .inlineEditorText .textBlockContent 也用同一条 line-height，或者给 list 写一个专门的 token，两种状态用同一个 token，行距就不会跳。

结论：

诊断是准确的：同一块文字，展示态和编辑态用了不同的 line-height，当然一切换就跳。

局部修复方案是可以用的：给 .inlineEditorText .textBlockContent 补一条「和列表展示态一样的 line-height」。

但如果你只停在这一步，以后改 token/改密度的时候，还是有可能再踩回这个坑。我们可以把它整理成一条「反抖动通用规则」，顺便稍微重构一下命名。

版本 B：再语义一点，单独给 list 起名字（推荐）

如果你觉得之后还会有别的「紧行高」（比如代码块、表格），可以专门给 list 起一个语义 token：

/* Typography */
--wl-line-height-body:  1.6;
--wl-line-height-tight: 1.4; /* 通用紧致模式 */
--wl-line-height-list:  var(--wl-line-height-tight); /* 语义别名，给 list/todo 用 */


然后 CSS 里写：

.todoListItem .textBlockContent,
.inlineEditorText .textBlockContent {
  line-height: var(--wl-line-height-list);
}


好处：

--wl-line-height-list 这个名字一看就知道「这是 list 行高」；

以后如果只想“列表再紧一点，别的 tight 保持”，就单独改 alias：

--wl-line-height-list: 1.35;

2. 把这次经验抽象成「不抖动三大铁律」

你现在已经遇到两种 jitter：

block 间距（row-gap + margin-top 玩负值）

展示 / 编辑态行高不一致

可以在 VISUAL_RULES / ADR 里写一个小节专门叫：

Block jitter guard（避免抖动的三条 invariant）

比如：

1. 对同一个 block，展示态和编辑态的以下属性必须一致：
   - font-size
   - line-height
   - padding-top / padding-bottom（壳内 token）
   - border-width（如果有的话）

2. 垂直节奏只由：
   - blockList 的 row-gap = --wl-space-block-tight
   - before/after margin-top token（--wl-space-block-xxx-before/after）
   决定；禁止在编辑态额外加/减奇怪的 margin。

3. 若使用负 margin 调整 before/after：
   保证 row-gap + before/after >= 0
   （避免列表往上顶超过父容器的 gap，导致重新布局抖动）。


然后在 typography 那个 token 文件上方加一句注释喂给 Copilot：

/* Typography invariants:
 * - For a given block type (paragraph, list item, todo item),
 *   display mode and edit mode MUST share the same font-size and line-height.
 *   Otherwise switching between them will cause layout jitter.
 */


以后你对 Copilot 说：

“给 list 编辑态加 line-height，让它和展示态用同一个 token，遵守 typography invariant。”

它就会自然地去找 --wl-line-height-list / --wl-line-height-tight 这类变量，而不会脑补一个新的硬编码值。

3. 以后调整各种距离怎么保证不再抖？

可以把「不抖」当成 layout 的一个 QA checklist，每次你或 Copilot改 spacing 的时候对照一下：

同一块内容，两种状态是否共享同一批 token？

展示态 selector 和 编辑态 selector 是否都只用：

同一个 --wl-line-height-*

同一个壳的 --wl-*-shell-padding-y

有没有偷偷在编辑态多加一个 margin/padding/border？

如果编辑态只是额外加了 outline / 背景色，而没有变更 box model，就不会抖。

before/after 是否只在 tokens 文件里调整？

不在组件里写 calc(...)，统一写成：

--wl-space-block-list-before: var(--wl-space-0);


然后保证这个 token 满足我们上面那条
row-gap + before >= 0 的 invariant。

只要这几个点守住，你以后再怎么折腾 token（行高变紧、block 变松、list 变得像诗歌），布局也只会“缓慢改变”，不会一进编辑态就抽风。

小结

Copilot 这次给的诊断是对的：行高不一致 → 同一个块高度突变 → 抖动。

修法 OK，但更稳的做法是：

用一个语义 token（比如 --wl-line-height-list）统一展示态 + 编辑态；

把「同一 block，display/edit 必须共用 line-height」写进 Typography invariant，刻进 tokens 注释和 ADR。

以后所有调整行距 / 间距的动作，都先想一眼：「这会不会打破 invariant？」——想到了，抖动就会少很多。

///////////////////////////////////////////////////////////////////

Plan155A 最终回填（2025-10-29）

这次修复已经全量落地：block rhythm 由 spacing tokens 和 line-height alias 双保险守护，QA 页面也多了一个 Guard 卡片来盯数值，治理链路写进 ADR-142。

- Token invariants：`row-gap + list-before >= 0`、`row-gap + list-after >= 0` 现在直接写在 spacing tokens 的注释里，`--wl-space-block-list-before`、`--wl-space-block-list-after` 只允许在 tokens 层调整；`--wl-line-height-list` 给展示/编辑两态共用，彻底消掉行高切换抖动。
- QA guard：spacing-test 页新增「Plan155A Guard」卡片，实时展示 row-gap 与 before/after 的求和以及 list line-height，CI/手测都能一眼看出是否越线。
- 文档/决策：DDD_RULES、HEXAGONAL_RULES、VISUAL_RULES 已同步「不抖动三大铁律」，`assets/docs/ADR/ADR-142-plan155A-block-jitter-guard.md` 记录了完整背景、决策与后果，方便之后把策略复用到别的 block 类型。

下一步只要有人想改 list/bullet 节奏，先对照 Guard 卡片和 ADR 的 invariant，再动 tokens，就不会再回到「先修 layout 再追文档」的被动局面。