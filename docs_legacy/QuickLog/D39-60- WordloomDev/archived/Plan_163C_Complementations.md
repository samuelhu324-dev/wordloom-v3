先给结论：

这套“新旧协议统一”的方案是对的，而且是足够狠的一刀。

如果你真的把文案里说的几件事都做到——尤其是彻底封死所有 window.getSelection().set* 调用——那种「鼠标点完 → 程序又把 caret 拖回预设行」的扫射，是可以在你自己的代码里完全灭掉的。

是的，我会建议你把这些规则正式写进 RULES/ADR，再配合一点代码级的护栏（lint / 封装），这样后面不容易“回潮”。

我分几块说清楚。

1. 为什么现在还会扫射？

你这段诊断其实已经说透了，我帮你用一句话收口：

现在有两套“谁有权改 caret”机制：

新协议：focusIntentStore + queueRowFocus（只在键盘流里改一次 caret）；

旧协议：selectionStore.requestSelectionEdge 直接 window.getSelection().removeAllRanges() + setBaseAndExtent()。

两套互相不知道对方存在，所以鼠标刚选好的位置，在某些异步命令/回调里又被旧协议生效了一次，于是你看到“先回到第一行再跳回来”的闪屏。

只要旧协议还在，逻辑上确实永远存在“某个角落又偷偷 setSelection 一次”的风险。

2. 这套解法本身靠不靠谱？

你写的 1–4 条其实就是：统一权力来源 + 杀掉影子政府。逐条看：

① 把 selectionStore 改成只读

删/封所有直接操作 selection 的 API（requestSelectionEdge、focusAtEdge 这类）。

只保留“监听浏览器 selection 变化并缓存”的功能。

👉 这一步等于宣告：

“选区的真相只有浏览器知道，selectionStore 只做日志，不再当总理。”

这是必要条件，不做这步你永远有第二个总理在暗中发号施令。

② 统一 focusIntent => queueRowFocus

所有“程序想改 caret”的场景——Enter 新行 / Delete fallback / Tab 改缩进 / 上下箭头换块——统统走
announceFocusIntent({ kind: 'keyboard', blockId, row })。

子编辑器只在捕捉到 命中自己的 keyboard intent 时，调用 queueRowFocus / focusAtEdge，并且这两个内部也不再动 window.getSelection()，只做 .focus() + 行级定位。

消费成功后立刻 clearFocusIntent()。

👉 这样“谁有资格发 reloc 指令”“谁执行一次”都变成单通道，结构上是干净的。

③ mount/update 时补一遍“鞭尸”检查

Paragraph/List/Todo mount/update 时捞一下 focusIntentStore，只要有 keyboard intent 命中自己还没被清，就立即消费并清零。

👉 这解决的是 React 更新顺序和异步的问题：
即使某个 editor 晚一点挂载，只要 intent 还在，就会在它自己的 useEffect 里补上那次跳转，不会因为渲染顺序不同又额外设 selection。

④ RULES + lint 封死后路

“任何代码不得再调用 window.getSelection().set*；若要定位 caret，必须写 keyboard intent → 对应 editor queueRowFocus。”

这一步是“在法律里写死”，再用 lint 做警察。

综合来看，这四步连在一起确实构成一套自洽的协议，不是缝缝补补。逻辑上它可以完全杜绝“程序在鼠标之后再偷偷改一次 selection”的情况。

3. 会不会还有漏网之鱼？

能想到的剩余风险点主要是两类：

你自己明知故犯

有人后来在别的模块里直接上：

window.getSelection()?.setBaseAndExtent(...)


这个只能靠 lint + code review 抓。
⇒ 所以你方案第 4 点（lint / RULES）非常关键。

不在这条链上的“特殊行为”

例如：

以后你要做“拖选多行高亮某一块”，这是非 caret 场景，可能确实需要程序去控制 selection 的范围；

或者你用到第三方富文本库，里面自己玩 selection。

这些场景可以在 RULES 里开一个白名单出口：

“只有在 非插入点 caret 的语义里（例如多行选区高亮）可以调用专门封装的 selectionTools.highlightRange()，
但该工具函数禁止在 block-editor 正文编辑路径中使用。”

简而言之：

对“正文插入点 caret”这一个问题域，按你这套协议来，是可以做到 100% 自己不打自己的；

真正不可控的是浏览器自身行为（用户自己拉选、双击、拖拽），但那正是我们说的“鼠标流由浏览器主导”，不属于“扫射 bug”。

4. 要不要写进 RULES？要，怎么写更清楚？

建议你在 RULES / ADR 里加一条专门的“小节”，标题就叫：

Caret 归属协议（Plan163A/B）

里面写几条“法律条文”式的句子，给未来的你 / Copilot 看：

单一真相

浏览器 Selection 是 caret 的唯一真相来源；任何逻辑想改变 caret，必须通过 focusIntentStore & queueRowFocus，不得直接写 window.getSelection().set*。

鼠标 vs 键盘职责

鼠标流：只允许更新 pointer intent 和 selectionStore 的读缓存，不允许调用任何改 selection 的 API。

键盘流：只有 keyboard intent 可以触发一次 queueRowFocus；消费后必须 clearFocusIntent。

selectionStore 的角色

selectionStore 只负责监听 selection 变化并缓存；它没有任何设置 selection 的权力。

扩展点 / 例外说明

若未来需要“多行高亮”等非 caret 行为，必须通过单独的 helper 模块实现，并在 RULES 中登记为例外，不得在 block-editor 正文编辑路径中直接使用。

工具约束

Lint 规则：在 frontend/src/modules/book-editor/** 下禁止 window.getSelection().set* / setSelectionRange / removeAllRanges 等调用，统一改用 intent + focus API。

这样一来：

文档里有原则，

代码里有封装 + lint，

Plan163A/B 里有实现步骤，

三层叠起来，后面再次出现“光标扫射”，几乎可以肯定是有人违规用 API——很好查。

5. 小结

你图里的这套“旧协议 vs 新协议 → 统一为 focusIntent + 只读 selectionStore”的方案，是合理且足够强的。

只要你真的把所有 direct setSelection 通道关死，并且所有“程序驱动的 caret 跳转”都统一走 keyboard intent → queueRowFocus，那种你现在看到的扫射现象，在你自己的实现里是可以干干净净消失的。

是的，我非常建议你把这些条款写进 RULES/ADR，再加一点 lint，把它变成“系统法律”而不是单次修 bug 的笔记。

之后如果再看到光标乱飞，那就不是“协议设计的锅”，而是“有人违反了协议”，排查会简单很多。