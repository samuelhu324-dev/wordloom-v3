## 2025-12-10 回填

- **Outcome:** TODO 行级 Backspace 现已与 list 共用统一规则：非空只删字符，空行会删除该 item，只有当 `allItemsEmpty=true` 时才触发 todo-exit → deleteBlockWithGuard，从而满足 Plan169A 的“待办退格不再卡死”目标。
- **Code refs:** `keyboardDecider.ts`（todo ctx + todo-remove/todo-exit）、`ui/TodoListBlock.tsx`（handleKeyboardDecision/pendingExit）、`useBlockCommands.deleteBlockWithGuard`（只被壳层调用）以及 `BLOCK_RULES`/`HEXAGONAL_RULES` 新增的 todo exit 约束已更新。
- **Tests:** `pnpm vitest frontend/src/modules/book-editor/ui/__tests__/TodoListBlock.test.tsx` 覆盖“空/非空 Backspace”“整块空退出”场景，手测 QA 也确认单条空 todo Backspace 会直接降级为 paragraph。

先给你一个直接结论：

是的，TODO 的退出规则最好跟普通 list 保持同一套“大原则”，
但可以在“按什么键触发”上稍微细一点。

具体可以设计成：
“当整块 todo 都是空项时，最后一个空项再 Enter / Backspace → 退回成段落（或删除 todo 块）”。
这样和你现在 list 的“整块为空才触发退出护栏”逻辑是统一的。

下面把你两个截图说的东西拆开讲一下。

1️⃣ 现在 list 的退出模式（截图 1）

你现在的行为是：

在有内容的 list 末尾不断按 Enter：
→ 一直创建新的 list item ✅

只有当整块列表都为空时，连续 Enter 才会按“护栏规则”退出到段落。

这个设计的“潜台词”是：

只要列表里有非空内容，就默认用户还在继续写条目，
不轻易把 block 变回 paragraph，防止误退。

等用户把所有条目都清空以后，再连续 Enter，才触发“退出列表”。

这是一种比较“保守”的退出策略，本质是：

“listBlock 什么时候死？——只有在“整个 block 对用户来说都没内容了”的时候。”

这个思路是自洽的。

2️⃣ 刚才说的 TODO 退出策略（截图 2）

之前我们讨论 todo 的时候，你那段规则是：

keyboardDecider：只有在 context.hasSiblings === true 时走 todo-remove-item
→ 有兄弟就删当前 todo；

若只剩一条 todo，就退回 block 级 deleteGuard（保持至少一个空项），
结果就是：在最后一个空 todo 上按 Backspace，看起来“啥也没发生”。

我刚才的建议是：

对“只有一条且为空”的 todo，
不要再交给 deleteGuard 拦截，而是明确判定为 todo-exit（或 remove+delete block），
也就是“退回为段落 / 删除 todo 块”。

这跟你 list 的“整块为空才退出”其实是同一类判断，只是写法不一样：

“只有一条且为空” ⇔ “整块 todo 都是空的”

3️⃣ 要不要让 TODO 和 list 完全一致？

从用户脑子里的模型来看：

bullet list / numbered list / todo list
本质上都是“一条条 item 组成的列表块”，
只不过 todo 多了个勾选框。

如果：

list：整块空 + 连续 Enter → 退出成 paragraph

todo：整块空 + 连续 Backspace/Enter 还退不出去

用户会非常困惑：“为啥两个长得一样的东西，键盘行为完全不一样？”

建议的统一规则（我比较推荐）：

对 所有“列表类 block”（bullet / number / todo）统一：

有任何非空条目时

Enter 在末尾：继续生成新的 item

Backspace 在空的中间项：删除这一行，光标移动到上一/下一行

不触发布局级退出

整块列表都为空时（所有 item 的文本都只剩空白 / \n）

在最后一个空项上：

连续 Enter → 护栏判定通过，整个 listBlock 退出成 paragraph

或 Backspace 触发同样的退出（看你要不要给 Backspace 也开这个出口）

在实现里：

list / todo 共用同一个 keyboardDecider 分支，

差别只体现在渲染（有无 checkbox）和命令名上，

退出动作都是 LIST_FAMILY_EXIT_TO_PARAGRAPH 这一类命令。

这样：

你现在的 list 行为无需推翻，只是把 todo 的“最后一条空项”也纳入同样的“整块为空 → 退出”逻辑；

代码上也更干净：

list & todo 共享 isListFamily 的 exit 分支

todo 不会再出现“最后一条空项按 Backspace / Enter 没反应”的智障体验；

你问的那句具体话：

“比如说最后一个空的 todo 会退回为 para？”

在这套统一规则下答案是：

是的——当整块 todo 都是空的时候，最后一个空 todo 再 Enter/Backspace，就退回为 paragraph；

如果还有别的 todo 条目有内容，就先删条目，不直接把整个块变 para。

这样，list 和 todo 的退出节奏在“关键节点”上是一致的，
用户不会在两个看起来一样的块之间重新学习两套奇怪的键盘套路，你的 keyboardDecider 分支也能写得非常薄。