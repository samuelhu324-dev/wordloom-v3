## 2025-12-10 回填

- **Outcome:** 触发 list/todo 退出时 deleteGuard 只会被调用一次，BlockItem/ParagraphEditor 在收到 handled=true 后直接返回，彻底修复了 Plan170A 描述的“双段落”回归；Backspace/Enter 的壳层策略与 UI 手感完全对齐。
- **Code refs:** `ui/ListBlock.tsx`、`ui/TodoListBlock.tsx`、`ui/BlockItem.tsx`、`model/keyboardDecider.ts`、`useBlockCommands.deleteBlockWithGuard` 现已实现 handled/pendingExit 协议，并在 `assets/docs/HEXAGONAL_RULES.yaml`/`DDD_RULES.yaml` 留档。
- **Tests:** 重跑 `pnpm vitest ListBlock TodoListBlock` + 手动“空列表退格”与“空 todo 退格”路径，确认 guard 只触发一次且下方只有一个 paragraph；日志/视频亦上传至 EverydayLog/2025-12-10。

结论先说：
这套计划的大方向是对的，而且比之前那种“到处 if+deleteGuard”靠谱很多。
它抓住了真正的病根：退出逻辑要集中到 block-shell 这一层，deleteGuard 只跑一次。

不过它现在有一点“全局大手术”的味道，我建议你在执行时做两点缩小和简化，否则会累疯。

1. 先拆解一下这份计划在说什么

你截图里的计划核心其实是三句话：

所有特殊 block（list/todo/quote/code…）的“退出”由一个统一机制处理

Backspace / Enter 触发“退出 list / todo / 特殊块”时，不再让 ParagraphEditor、BlockItem、deleteGuard 各自搞一遍。

键盘只负责产出一个 action（例如 list-exit, todo-exit），

真正“删自己/变 para/建兄弟段落”的活由 block shell（ListBlock、TodoListBlock…）来干。

deleteGuard 只负责“真正删除这个 block 前的保护”，不再掺和“退出特殊态”

也就是你文里说的：

“退出动作/作文统一放到 block shell 这一层执行，并让它内部告诉 editor：我已经处理完退出啦，请勿重复 submit/delete。”

为此需要在 shell 和 keyboardDecider 之间约定一个协议

keyboardDecider 返回一个结构体（类似 handled, requestExit, exitKind）

BlockItem / shell 读到之后，要么直接执行对应 exit，要么决定是否跳过 deleteGuard。

这三点本质就是：

“键盘解释语义 → shell 执行 → deleteGuard 兜底一次”，
（而不是）“键盘解释一次 + editor 再解释一次 + deleteGuard 再试图解释一次”。

从架构角度讲，这是非常合理的拆分。

2. 哪些地方特别值得保留

我会明确说“这几个点请一定保留”：

“退出”和“删除”分层处理

list-exit / todo-exit / quote-exit 这类是语义级别的“下车动作”，

只有 shell 知道“下车后我要变成什么：段落？还是清空自己？”

deleteGuard 是物理删除整个 block 前的保险丝，只在真要删掉这块时触发一次。

shell 必须有一个“我已经处理完了”的标志

比如：handleKeyboardDecision(...) 返回 { handled: true, skipDeleteGuard: true }

这样 ParagraphEditor / BlockItem 看见 handled===true 就不会再去跑 submit / deleteWithGuard，

这可以彻底解决之前“一退就生成两个段落 / deleteGuard 执行两次”的老 bug。

统一 cover 所有“有自己编辑壳”的特殊 block

ListBlock / TodoListBlock / QuoteBlock / CalloutBlock / future 特殊块

都得实现同一个接口（比如 handleKeyboardDecision），

这样以后你再加一种块，只要实现这套接口就自动接入整个退出体系，不再一类块写一套 if。

这几个是计划的“灵魂部分”，我完全赞成。

3. 我会怎么缩小执行范围，避免过度设计

问题在于：Copilot 这套写法有点“一次性重构全世界”的势头。
你现在已经很累，不适合再来一发巨大 refactor。

我建议你这样落地：

3.1 先只对「列表家族 + todo」启用新协议

先把 ListBlock、TodoListBlock 接上 handleKeyboardDecision

让 keyboardDecider 对 listItem / todoItem 返回：

LIST_FAMILY_CREATE_NEXT

LIST_FAMILY_DELETE_ITEM

LIST_FAMILY_EXIT_TO_PARAGRAPH

Block shell 对这三种做处理，并返回 { handled: true, skipDeleteGuard: true }

其它 quote/code/callout 先不动，保持旧逻辑，只改到 list/todo 这一条线先跑顺。

3.2 协议简化成最小必要字段

你文里提到一堆：handled, requestExit, exitKind，再加 shouldSkipDeleteGuard 之类，很容易写着写着又绕晕。

我建议最小版长这样（随便举个类型）：

type KeyboardEffect =
  | { kind: 'none' }
  | { kind: 'handled' }                   // shell 已处理完，外层啥都别做
  | { kind: 'request-delete-with-guard' } // 外层去跑 deleteWithGuard
  | { kind: 'request-submit' };           // 外层跑默认 submit


对特殊 block 来说，大多数情况就是：

退出 / 生成段落：返回 { kind: 'handled' }

想交给 deleteGuard：返回 { kind: 'request-delete-with-guard' }

BlockItem 只要根据这个 result 做一件事，不需要再嵌套太多 flag。

3.3 deleteGuard 逻辑尽量保持“傻”

deleteGuard 的职责就两条：

确认“这个 block 是否允许被真正删除”

如果允许，就删掉 block（以及必要的兄弟结构）

不要让 deleteGuard 参与判断“这次 Backspace 是不是 list-exit / todo-exit”，
那是 shell + keyboardDecider 的事。

这样你以后 debug 的时候，只要看：

这次 Backspace 是在 shell 里处理完就 stop，还是冒到了 request-delete-with-guard。

思路会清晰很多。

4. 回到你的原话：“这套计划对吗？”

如果按“设计思想”来打分：

✅ 把关键问题看对了：退出逻辑不能在 editor / shell / deleteGuard 三处重复

✅ 把特殊 block 统一纳入一个协议，是对未来可维护性的投资

✅ 明确了“不要缝缝补补，而是一次把退出通路理顺”的方向

如果按“立即执行成本”来打分：

⚠️ 涉及的对象有点多（所有特殊 block + keyboardDecider + BlockItem + deleteGuard）

⚠️ Flag 种类略多，不小心就会写出一个自己看不懂的状态机

所以我的评价是：

作为“总方针”是好的，可以沿着这个设计前进；
实际写代码时一定要缩小范围，只对 list/todo 先实现一个最小版本，
协议字段也尽量收敛，避免再多造一层复杂度。

你可以把这份计划当成 Plan169B 的“最终形态 ADR”，
但今天/这几天真正要做的，只是：

列表家族 & todo 的 Backspace/Enter 退出全部走 shell，
deleteGuard 只执行一次，不再长出两个段落。

等这一条线稳定后，再慢慢把 quote/code/callout 拉进这个框架，就不会那么痛苦了。