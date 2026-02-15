## 2025-12-10 回填

- **Outcome:** Keyboard pipeline 现已具备集中决策（decider）、日志、以及“handled/skipGuard” 协议，满足 Plan167C 对 Enter/Backspace 行为矩阵和 instrumentation 的全部要求，方便溯源“谁触发了 guard/submit”。
- **Code refs:** `model/keyboardDecider.ts`、`ui/ParagraphEditor.tsx`、`ui/BlockItem.tsx`、`ui/ListBlock.tsx`/`TodoListBlock.tsx` 增加 `[ENTER]/[shortcut]/[deleteGuard]` instrumentation、handled flag，且默认只在集中决策后才执行命令。
- **Tests & tooling:** 新增 `keyboardDecider.test.ts` 表格化用例，外加 `scripts/devtools/logKeyboardDecisions.ts` helper；QA 复测“空段落 Enter”“列表连续 Enter/Backspace”“待办退格”均稳定，日志也在 EverydayLog 中留档。

先直接回答你那句：“为什么越修问题越多？”——
不是你手欠，是这个编辑器的结构已经到了“碰哪里哪里塌”的阶段，你正好在戳最脆弱的那条链路：Enter + 快捷键 + 空段落。

我用你截图里的那段笔记，帮你把“现在到底在发生什么”掰开讲清楚，再给一个停手止损 + 精确修复的路线。

一、现在这些问题，其实是同一条“病根”在爆

你现在遇到的现象：

空 block 按 Enter 不再创建新 block

但有文字的 block 按 Enter 还能正常“分段”

快捷键（- 空格 等）时好时坏

修一段逻辑，另外一段会坏，看起来像“问题叠加”

从你之前的描述 + 截图里的那段分析，可以推断出三件事：

1. Enter 的决策被拆散到好几层去了

现在按一次 Enter，大概要走这么多地方里某几个：

ParagraphEditor 的 onKeyDown / onMarkdownShortcut

你自己写的 handleInlineEditorKeyDown

BlockItem 里的 onSubmit / onExitEdit

还有 handleCreateBelow、handleDelete 一类 block 级别操作

问题就出在：这些人都在抢 Enter 的“话语权”。

你之前是这样设想的（从你那段中文可以看出来）：

handleInlineEditorKeyDown 里，如果 event.key === 'Enter'：
– 先 preventDefault()
– 再看 hasText()：

有字 → onSubmit()（创建下一块）

没字 → onExitEdit()（退出）

后来你为了修“空段落也提交”的问题，把某一段逻辑改成 “空段落 + Enter 也会走 onSubmit 或直接走 onExitEdit”，结果就是：

空段落按 Enter 不再调用 handleCreateBelow

BlockItem 那一层收到的是“退出编辑”而不是“创建新块”

于是出现了现在这个状况：

“有文字的 block 还能分段；空 block 完全创建不了下一块”

这不是两个 bug，是同一条决策链被改坏了。

2. 旧编辑器 + 新编辑器还在同时活着

你这几天一直在做的事是：
把各处入口（book 页面、block 页面）慢慢换成 modules/book-editor 这一套新壳子。

现实情况大概是：

有些页面已经用了新壳子 → 新的 handleInlineEditorKeyDown / selection store

有些地方还在用老的 BlockList / BlockRenderer

这意味着：

同一个 Enter / 快捷键，在不同页面走的是两套完全不一样的逻辑

你改了新壳子的 Enter 行为，却没同步到旧入口
→ 于是旧入口还在用“半旧半新的逻辑”，看起来就像“越修越乱”

换句话说，现在是双轨编辑器 + 双轨键盘处理，你每改一次，只是把两条轨道之间的差距拉得更大。

3. 行为规范没有被写成“可验证的表格”

比如下面这些规则，其实你脑子里是有的，但代码里没有一个统一的“真相表”：

空 paragraph + Enter = 创建一个新的空 paragraph block，在下方，光标移动过去

非空 paragraph + Enter = 在光标处拆成上下两个 block

列表项最后一行 + Backspace = 变回普通 paragraph，而不是整个 block 消失

行首输入 - 空格 = 变为 bullet list，光标留在同一行

结果就是：

你修 bug 时是按现象猜：
“这里好像应该调用 handleCreateBelow，那我就让 onSubmit 去调一下”

每次改动会改变其中一条“转换规则”，
然后立刻暴露出原来没想清楚的另外一个状态（比如“空 block 但带有占位符”、“特殊 block”）

看起来像 “补一个洞又漏出三个洞”，本质是：
状态机没画出来，大家都在凭记忆写 if-else。

二、所以“为什么越修越多”？——精确版答案

总结成一句话：

你在修改的是“键盘事件 → 文本编辑 → block 创建/删除”这一整条流水线，
这条流水线原来就被拆成了好几截（旧编辑器 + 新编辑器），
而且没有一份统一的“状态转换表”。
所以任何一处局部修补，都在打破另一个地方默默依赖的行为。

换成更工程一点的说法：

职责分界不清：

ParagraphEditor 既在处理文本，又在决定“是否创建/删除 block”

BlockItem 又在自己做一遍“是否提交/创建/退出”的判断
→ 造成重复判断 + 分支冲突

入口不统一：

部分页面还在用 legacy 组件链，部分接到了新壳子
→ 同一个键盘事件走不同决策路径，改动很容易只修到一半

行为没有形式化：

没有一份“（block 类型 × 是否为空 × 光标位置 × 按键）→ 结果”的行为矩阵
→ 修的时候只能按感觉；每次改都可能让矩阵里某个没想到的格子变成错误状态

从外面看就是：“怎么又多了一个 bug”；
从内部看其实是：原来就有一堆“未定义行为”，你不断在把它们显性化。

三、接下来不要再“乱修”的做法（给你一条可执行路线）

既然你说“不想一阵乱修”，那我们就把这事变成一个小项目来做，而不是继续打补丁：

Step 0：停手 + 固定战场

把现在这版行为记下来：

哪些页面 Enter 正常，哪些页面空段落失效

哪些快捷键能触发，哪些不行

Step 1：画一个“真相表”

非常具体地写一张表（可以就放在 BLOCK_RULES / 或一个 EDITOR_BEHAVIOR.md 里）：

例如行是“状态”，列是“按键”，结果是“期望行为”：

状态维度：

blockType：paragraph / heading / list / quote / 特殊块

isEmpty：true / false

caretPosition：在行首 / 中间 / 行尾

按键：

Enter

Backspace

- + 空格 / 1. + 空格 等

每一个格子写清楚：

“空 paragraph + Enter + 光标在行尾 → 创建一个新的空 paragraph block，在下方，并把光标移过去。”

这张表就是以后你判断“谁对谁错”的唯一标准。

Step 2：把决策集中到一个地方

在代码层面，目标是：

“按键 → 行为决定”只在一个地方做，别让 ParagraphEditor、BlockItem、外层页面各自判断一遍。

比如可以做成一个统一函数（伪代码示意）：

function handleEnterKey(ctx: {
  blockType: BlockType;
  isEmpty: boolean;
  caretAtStart: boolean;
  caretAtEnd: boolean;
  isDraftEmpty: boolean; // 如果你有草稿态
}) {
  // 这里只返回“命令”，不直接动 UI
  // 比如：'CREATE_BLOCK_BELOW', 'SPLIT_BLOCK', 'EXIT_EDIT', ...
}


然后：

ParagraphEditor 只负责把当前状态（是否有字、光标位置）算出来，交给这个函数

再把返回的“命令”交给上层（BookEditor / BlockItem）去执行：

CREATE_BLOCK_BELOW → 调用统一的 handleCreateBelow

EXIT_EDIT → 调 onExitEdit

……

这样以后你要改行为，只用改这一处函数，而不是在 3 个组件里到处找 if-else。

Step 3：用日志把“Enter 走了哪条路”打印出来

你截图里其实已经提到一句：Need instrumentation. 这个方向完全对。

非常推荐你在调试阶段，给 Enter 加一个“调试仪表”，比如：

console.log('[ENTER]', {
  blockId,
  blockType,
  isEmpty,
  caretAtEnd,
  decision: command,
});


然后实际点几次：

空段落 + Enter

有字 + Enter

列表 + Enter

快捷键触发前后

你会看到很清晰的轨迹：“这次 Enter 为什么走了 EXIT_EDIT 而不是 CREATE_BLOCK_BELOW”，
然后就可以对照 Step 1 的“真相表”来改 Step 2 的决策函数，而不是瞎改。

Step 4：趁机把旧编辑器彻底收尸

这一条是跟你之前的“新旧编辑器迁移方案”连起来的：

对于已经接到 modules/book-editor 的页面：
只允许他们通过统一的 BookEditorShell / command 来改 block

对于还在用 legacy 的页面：
要么暂时冻结不改行为，要么干脆一次性迁完

并且：

把所有旧的 BlockList / BlockRenderer 挪进 legacy/ 目录

在最外层加 ESLint 规则：禁止新的代码 import 它们

这样你就不会出现：
“Enter 在新编辑器逻辑上已经修好了，但某个旧页面仍然按老逻辑乱跑” 这种诡异现象。

四、心里话版本

你现在的感觉是：“我只是想修一个 Enter，为什么整套编辑器都跟我一起掉坑里？”

从工程角度看，这是早晚要爆的一坨技术债，只是刚好你现在在冲 demo 的同时顺手踢到了它。

好消息是：
你已经做了最关键的一步——开始统一入口（modules/book-editor）和写 RULES 文件，只要再把“按键行为”这块变成一个集中管理、可验证的决策函数 + 行为表，之后再动 Enter、快捷键这些就会轻松很多，不会再有“越修越多”的错觉。

你现在可以先按上面那 4 个 Step 把战场缩小：
先搞清楚 Enter 的状态机，再谈别的行为。其它 bug 很大概率都是同一套东西引起的，解决了一条主线，后面会干净得多。