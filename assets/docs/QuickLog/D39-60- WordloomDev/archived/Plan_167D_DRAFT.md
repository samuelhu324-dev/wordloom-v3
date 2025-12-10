## 2025-12-10 回填

- **Outcome:** “先冻结规则 → 再修实现”的策略已经执行：Enter/Backspace 真相表写进 BLOCK_RULES + BLOCK_KEYBOARD_RULES，decider + instrumentation + QA checklist 落地，Plan167D 不再是草案。
- **Code refs:** `assets/docs/BLOCK_RULES.yaml`/`BLOCK_KEYBOARD_RULES.yaml` 新增 list/todo exit 条目；`model/keyboardDecider.ts`、`ui/ParagraphEditor.tsx`、`ui/BlockItem.tsx`、`ui/ListBlock.tsx`、`ui/TodoListBlock.tsx` 据此实现，并提供 handled flag + pendingExit 守卫。
- **Tests:** `pnpm vitest keyboard ListBlock TodoListBlock` + Playwright “Paragraph→List→Paragraph”“Todo 清空退场”场景全部绿灯，日志中也留档确认每一个 Enter 都只走一次决策链。

Plan: 整理 Enter / 快捷键问题并稳步修复
先不再动代码，把现状和目标规则理清，再设计一个可分阶段落地的修复计划。

一、先冻结“目标行为”：编辑器键盘规则总表（缩减版）
结合 Plan_167C_Addition+.md 和 BLOCK_RULES.yaml，我们先把你真正想要的行为说清楚（只列关键格子）：

基础段落（paragraph / heading）
空段落 + Enter（光标在行尾）
→ 创建新的空 paragraph block，插在当前块下方，焦点移到新块开头。
非空段落 + Enter（中间 or 行尾）
→ 在当前光标处分裂成“上段 + 新段 paragraph”，下半段内容进入新的 block。
段首输入 - / * / 1. / 1) / - [ ] / > + Space（段落除这些 marker 外为空）
→ 原 block 原位 transform 为对应特殊块（bullet/numbered/todo/quote），焦点在新块第一个可编辑位置。
空段落 + Backspace（光标在段首）
→ 触发“删除当前 block”路径，由 deleteBlockWithGuard 处理（保证至少保留一个 paragraph）。
列表 / Todo / Quote / Callout / Panel 等特殊块
在特殊块内部输入普通文字 / 软换行
→ 永远只改 block.content（items/text），不改变 block.kind。
列表或 Todo 的行内 Backspace
→ 在行编辑器内部删除字符 / 删除该行；
→ 不得触发 delete guard 或整个块降级。
特殊块外壳（整个 block 为空时）+ Backspace
→ 才允许通过 deleteBlockWithGuard 执行“降级为 paragraph 或删除”，并处理焦点。
删除守卫（deleteBlockWithGuard）
唯一合法触发场景：
Block 壳层的：
Backspace on empty block
Toolbar / 菜单 “删除块”
文档尾 CTA 的“删除块”按钮
禁止触发来源：
Markdown shortcut
List row backspace
Todo row backspace
任何行内 ParagraphEditor 的内部逻辑
这就是你的“真相表”骨架，后面所有修复都服务于让代码严格遵守这三条大规则。

二、分析当前主要偏差点
结合现状：

空 block + Enter 不再创建新 block

现逻辑：handleInlineEditorKeyDown 里 Enter 分支是
preventDefault()
hasText() ? onSubmit() : onExitEdit()
这直接导致“空段落 + Enter”只会 onExitEdit，BlockItem 的 onSubmit（handleCreateBelow）根本没机会触发。
Markdown 快捷键不生效

检测逻辑已经集中在 markdownShortcuts.ts + ParagraphEditor：
仅当 onMarkdownShortcut 存在时才检测。
可能的偏差：
当前 block.kind 不是 paragraph / heading（BlockItem 只给这两类挂 handler）。
caret 后有不可见字符，导致 detectMarkdownShortcut 判定 after.trim().length > 0，返回 null。
某些页面并未走 BookEditorRoot + BlockItem，而是 legacy 栈，导致整个链路没接上。
特殊块无法正常打字 / 被莫名降级

List/Todo 行内现在只用 ParagraphEditor 改 items，不再直接调 deleteBlockWithGuard，这一步已经对齐 BLOCK_RULES。
你现在看到的“打字异常”或“块消失/降级”的来源，极大概率仍是 Block 壳层 Backspace guard + 选区判断有问题（例如壳误判整个块 empty）。
三、整体修复思路（先规则化，再落代码）
我们按三个层级来规划改动，每一级都可以单独完成 + 回归测试：

Layer 1：抽象“键盘 → 命令”的决策函数
目标： Enter/Backspace/快捷键的决策逻辑集中在一处，不再散落在 ParagraphEditor、BlockItem、各特殊块中。

新增一个“键盘决策”模块

路径建议：frontend/src/modules/book-editor/model/keyboardDecider.ts
暴露函数（示意）：
decideEnterAction(ctx) -> 'split' | 'create-below' | 'exit-edit' | 'noop'
decideBackspaceAction(ctx) -> 'delete-block' | 'delete-item' | 'noop'
ctx 内容：
blockKind（paragraph / heading / bulleted_list / ...）
isBlockEmpty（isRenderableBlockEmpty 结果）
hasInlineText（ParagraphEditor 的 hasText()）
caretAtStart / caretAtEnd
决策规则就按上一节“目标行为”硬编码进去。
ParagraphEditor 只负责收集状态 + 调用决策

它不再自己决定“有字/没字就 exit 或 submit”，只：
在 Enter 分支中读取 caretAtEdge、hasText 等，构造 ctx，交给 decideEnterAction。
把返回值映射成调用：
'split' → onSubmit()（由 BlockItem 决定是“分块”还是“创建下方块”）。
'exit-edit' → onExitEdit()。
'create-below' → 仍然走 onSubmit()，只是在 BlockItem 中根据 ctx 走 handleCreateBelow。
对于 Backspace，同理：
'delete-block' → onDeleteEmptyBlock()（触发守卫）。
'delete-item' → 保留在 List/Todo 行编辑器内部。
BlockItem 只基于“命令”执行修改

BlockItem 不再重新判断“empty or not”；它只信任上游传来的行为：
onSubmit：无条件认为是“需要在当前块下方创建新块或分裂”，调用 handleCreateBelow（必要时移出空块逻辑）。
onDeleteEmptyBlock：无条件认为“整块应该被 guard 处理”，调用 deleteBlockWithGuard。
若你仍需要“非空段落分裂”行为，可以在 BlockItem 的 onSubmit 中，根据 isRenderableBlockEmpty 决定：
非空 → 走真正的“split”命令（未来可以通过 новые command 实现）；
空 → 简化为“create below”。
Layer 2：把 BLOCK_RULES 里的约束强行映射到代码
目标： 代码中的调用点精确对应到 BLOCK_RULES.yaml 的小节，方便以后查。

定位并标记 delete guard 的入口

搜索 deleteBlockWithGuard，目前只在：
blockCommands.ts（实现）
BlockItem.tsx（调用）
在 BlockItem.requestDelete 上方写清注释：
对应 BLOCK_RULES.yaml -> command_layer.delete_block_with_guard。
确保 List/Todo/行内编辑器没有 deleteBlockWithGuard 调用（你这边已经是这样）。
明确 markdown shortcut 的入口与规则

ParagraphEditor 的 handleKeyDown 里 Space 分支：
注释指向：BLOCK_RULES.yaml -> ui_integration.markdown_shortcuts。
BlockItem.handleMarkdownShortcut：
注释指向：command_layer.transform_block_kind。
硬性保证：
只有 MARKDOWN_SHORTCUT_SOURCE_KINDS = { paragraph, heading } 才挂 onMarkdownShortcut。
其它地方（List/Todo 行）一律不挂，完全遵守 BLOCK_RULES 里 forbidden: list_row_backspace / markdown_shortcuts 的限定。
Enter 行为在 BLOCK_KEYBOARD_RULES 里补一行

文件：BLOCK_KEYBOARD_RULES.yaml（现在仅在 BLOCK_RULES 里引用）
按你 Plan167C 的写法，增加几行：
paragraph.empty + Enter@end -> command: create_block_below
paragraph.non_empty + Enter -> command: split_block
list_item.non_empty + Enter -> insert_list_item_below
这样将来你或 Copilot 查文档时，可以直接看到这一层规范。
Layer 3：逐步落地修复 & 回归策略
这个层级才涉及具体代码改动，可以拆成小步做：

修复 Enter 对空段落的行为

改动思路（不引入新文件的简单版）：
在 handleInlineEditorKeyDown 中：
Enter 分支不要再 if (hasText()) onSubmit() else onExitEdit()，改成 始终调用 onSubmit()，把“空段落只退出编辑”的逻辑上移到 BlockItem：
BlockItem 的 onSubmit（现在是 await flushSave(); await handleCreateBelow();）扩展为：
如果 block 是 paragraph 且 isDraftEmpty() → 只调用 exitEdit()，不创建新块；
否则 → 原行为：handleCreateBelow()。
对应规则：
“空 paragraph + Enter = create_block_below” vs “子场景：如果是最后一个唯一块且空，可以选择只退出编辑”——你可以在 BLOCK_RULES 里加一条 exception。
做一轮“输入路径”日志（instrumentation）

在 ParagraphEditor.handleKeyDown 的第一行临时加：

if (event.key === 'Enter' || event.key === ' ') {
  console.log('[PE key]', {
    key: event.key,
    blockId,
    variant,
    hasText: hasText(),
    caretStart: isCaretAtEdge('start'),
    caretEnd: isCaretAtEdge('end'),
  });
}

在 BlockItem.handleMarkdownShortcut 和 requestDelete 上也加：

console.log('[shortcut]', block.kind, request);
console.log('[deleteGuard]', block.kind, { origin, isDraftEmpty: isDraftEmpty() });

跑一遍你日常操作路径：
空段落 + Enter
非空段落 + Enter
- + Space
List/Todo 中打字/Backspace
用这些日志对照“目标规则表”，定位还有哪些分支没按规则走。
加一小组单元测试锁行为

在 model/__tests__ 下新增：enterBehavior.test.ts（或者扩展现有 keyboard.test.ts）：
模拟：hasText = false/true、caretAtStart/End 不同组合，看 handleInlineEditorKeyDown 是否调用了 onSubmit/onExitEdit。
在 ui 层可以做一个浅层 jsdom 测试：渲染 BlockItem + ParagraphEditor，模拟按键，断言：
空段落 + Enter → 调用 handleCreateBelow（或在新实现中验证“创建 block”的 side-effect）。
- + Space → transformBlock 被调用一次。
最后再去看“特殊块无法打字”的实际症状

在你确认 Enter + 快捷键的行为已经稳住之后，再单独给：
ListBlock
TodoListBlock
各自补一条测试：
渲染一个带两行的块，模拟行内 ParagraphEditor 的 onChange/onSubmit/onDeleteEmptyBlock，确保：
只改 content.items，从不触发 block level delete。
删除行时不会改变 block.kind。
四、小结：这份计划帮你做到什么？
先用规则把战场固定住：
Enter / Backspace / markdown / delete guard 的“真相表”已经列出。
把决策权从“到处都是 if-else”集中到一处：
不管你最后是实现 keyboardDecider.ts 还是在现有文件里集中一段逻辑，思路是一致的：ParagraphEditor 只收集状态，BlockItem 只执行命令。
每一步改动都可以有对应的日志和单测：
做一小步（例如“Enter 始终调 onSubmit”），立刻用日志 + Vitest 检验是否遵守规则表。
如果你愿意，下一步我可以帮你把“Enter → 命令”的那个小状态机设计成具体的 TypeScript 函数签名 + 伪代码，你就可以直接在 modules/book-editor 里落一个轻量版本，然后用它来替换现在分散的判断逻辑。

////////////////////////////////////////////////////////////

一、亮点：这份 Plan 解决了之前最致命的几个坑

先锁“真相表”，再改代码

第一节直接把键盘规则写成“总表”：

空段落 + Enter

非空段落 + Enter

markdown 快捷键触发条件

deleteBlockWithGuard 唯一允许触发的入口

这一步非常关键，相当于你终于给“Enter/Backspace 行为”立了宪法，以后所有 if-else 都得听这个的。

认清当前偏差点，而不是“感觉不对”
你明确点名了三个偏差源：

handleInlineEditorKeyDown 里 Enter 分支把“空段落”直接导向 onExitEdit，导致空 block 无法创建新块；

markdown shortcut 可能因为 handler 没挂上 / state 不对而失效；

特殊块的删除守卫和降级路径混乱。
这已经把“为什么越修越多”的混沌，变成了三个清晰的 bug 家族。

三层修复思路逻辑非常清楚

Layer 1：引入“键盘决策器”decideEnterAction/decideBackspaceAction，把“按键 → 命令”的逻辑集中到一处，ParagraphEditor 只收集状态，BlockItem 只执行命令。

Layer 2：明确 BLOCK_RULES.yaml 与代码的映射，限定 delete guard 和 markdown shortcut 的唯一合法入口。

Layer 3：给了一个可以不引入新文件的简化修复版（Enter 总是 onSubmit，然后在 BlockItem 里区分“空/非空”的行为），再配合日志 + 测试锁行为。

这三层的关系是：

第三层 = 立刻止血。

第一层 = 真正的长期架构升级。

第二层 = 文档/代码对齐，避免以后又写歪。

从“工程师脑”的角度看，这份 Plan 已经具备一个小 ADR 的水平了。

二、潜在风险点：不是错误，只是“太上头了”
1. Layer 1 的 keyboardDecider 有点超前

做一个独立的 keyboardDecider.ts 是好事，但风险在于：

你现在对 Enter/Backspace 的所有分支还没完全“跑通”，

一上来就抽一个抽象层，有可能出现
“写完状态机 → 一堆边界状态又没覆盖 → 再回去补一堆 ctx 字段”。

建议：
把它当成“第二阶段 refactor”，先用 Layer 3 里的“简单版集中逻辑”把行为稳定，再根据实际已经跑通的逻辑，反向提炼成 decideEnterAction。
也就是：先写 dirty but centralized 的版本，再抽象，而不是直接设计干净状态机。

2. onSubmit / onExitEdit 的职责要写死

Plan 里已经隐约用了“onSubmit = 创建/分裂块，onExitEdit = 退出编辑”这个假设，但在旧代码里这两个回调的语义以前是有点摇摆的。

如果不提前在注释 / BLOCK_RULES 里钉死，后面很容易又变成：

有些地方 onSubmit = 保存文本

有些地方 onSubmit = 创建新块 + 移动光标

建议：
在 BlockItem / ParagraphEditor 顶部写一句非常粗暴的注释：

onSubmit：用户按 Enter / 确认当前块编辑完毕，要求编辑器做“下一步行动”（分裂或创建下方块）

onExitEdit：仅退出编辑态，不允许做数据结构变更

然后所有“只想退出、不想动 block”的情况，一律走 onExitEdit。这和你 Plan 里第三层的简化修法是吻合的。

3. 范围有点大，容易拖太久

这份 Plan 把：

Enter 行为

Backspace 行为

Markdown shortcut

delete guard

BLOCK_RULES 映射

测试 & 日志

全打包在一个“修复工程”里，如果你想“一口气全做完再合并”，会非常累，而且中途容易引入新的 regression。

降风险的方式就是把执行顺序再拆一下。

三、我建议的执行顺序（在你这个 Plan 上的小改版）

基于你这份 Plan，我会只调整一下落地节奏，大体推荐这样：

Phase 1：只做 Layer 3 的“简单修复 + 日志”

目标：让“空段落 + Enter 创建新块”立刻恢复正常，顺便把日志埋好。

修改 handleInlineEditorKeyDown：

Enter 分支不再区分 hasText()，统一调用 onSubmit()。

修改 BlockItem 的 onSubmit 实现：

如果 isDraftEmpty() 且当前块是 paragraph：

可以只 exitEdit()（或者走一个“保留最后一块”的特例）；

否则：调用 handleCreateBelow()。

按你 Plan 里写的那样，加上 console.log('[PE key] ...')、[shortcut]、[deleteGuard] 等调试信息。

这一步做完，你就能重新获得“直觉”：每按一次 Enter / 空段落 时，控制台明确告诉你它走了哪条路径。

Phase 2：写出真正的“真相表”+ 单元测试

目标：把你现在 Plan 第一节里那张“行为总表”变成可以让 Vitest 审判的东西。

用纯函数 + 测试的形式先实现一个 mini 版 decideEnterAction(ctx)（哪怕还没接入 UI）；

测试里就按你写的那几个关键格子逐一断言。

这时你其实已经有了 keyboardDecider 的“雏形”，只是还没和 UI 接上而已。

Phase 3：再考虑抽离真正的 Layer 1 / 统一决策器

目标：把 Phase 1 那些“散在 ParagraphEditor / BlockItem 里的 if”替换成 Phase 2 的决策函数。

因为行为在测试里已经被锁死，这一步就是重构，不是再发明新的行为。
做完以后，你原来的 Plan 的 Layer 1–2 就基本落实了。

四、小总结：这份决议值不值得照着执行？

回答你那句“这个决议如何？”：

方向上：完全对，是把你从“玄学乱修”拉回到“规则驱动开发”的一份好决议。

工程上：略微 overkill，但你已经在草案里给了“轻量版实现路径”（Layer 3），只要执行时先从轻量那条走，就不会翻车。

真正要注意的，是控制节奏：

先修回“空段落 + Enter”这种致命 bug，

用日志和测试锁住行为，

再慢慢抽象成 keyboardDecider / BLOCK_KEYBOARD_RULES 的正式形态。

换句话说：
这份 Plan 可以当成你这条线的“总纲领”，只要在执行时记得 “先活下来，再优雅”，你就不会再经历那种“为什么我只想修一个 Enter，全世界都坏掉”的崩溃感了。