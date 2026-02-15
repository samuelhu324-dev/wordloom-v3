已思考 1m 1s

结论先说：
这套“新修复方针”方向是对的，而且比之前那堆临时 patch 干净很多，可以让 Copilot 开工。
但有 几个前提 & 小雷点 你要在 Plan 里写死，不然 Copilot 很容易帮你挖坑。

我按你截图里的 1～5 点逐条评估。

1. “先插一个 para 再插 list” → 改成 transform / 立即移除
现状问题

Slash 菜单 / - 空格 现在是：

先走 insertParagraphBlock 或类似命令，插一个新的 paragraph；

再把 list block push 到同一个位置；

ensureParagraphAtCursor 又会再塞一个空段落；

结果：你看到“上面多出一个空段落 + 下面是 list block”。

新方案

“清查 block 插入/shortcut 流程，把『先建，再转』的临时段落直接改为 transform 或在插入后立刻移除”

这个是对的，但要加两个硬规则：

只对“空 para”做 transform

前提：Slash / - 空格 只在“当前 block 是空段落”时才允许触发。

这样 transform 段落 → list 时，清空 / 改写文本不会丢内容，因为本来就没东西。

禁止“先插一个 para 再删掉”的骚操作

你现在已经有 ensureAtLeastOneBlock / deleteBlockWithGuard 这条“文档永远有一个基础段落”的护栏；

在插入 list 时，如果又玩“插一个 para → 插 list → 再删 para”，逻辑就会跟 guard 打架。

所以统一心智：

当前 caret 在空段落上 → transform 当前 block 为特殊块
如果不是空段落，就直接拒绝触发（或者以后再做复杂行为）。

👉 建议你在 RULES 里加一句：“Slash / 快捷键只允许在空 paragraph 上触发 block transform，不再依赖中间临时 paragraph。”

2. transform 时清理 payload（text / items / checked 等）

“transformBlockKind 里为 list/todo/quote 设置 text='', items=[] 等重置逻辑，并在 create-list 命令里调用。”

这个也是对的，但同样需要把 “只在空 para 上 transform” 写死。否则会有这两种坑：

坑 1：段落非空 → 直接 transform

如果 paragraph 里有 "AAA"，你 transform 到 list 并把 text=''，那 AAA 就凭空消失，被你吃掉了。

坑 2：以后扩展出『把当前文本变成第一条 list item』的需求

那时候 transform 的逻辑就不是“清零 payload”，而是“迁移到 items[0]”；

所以你现在的版本要明确标注是“空段落专版 transform”。

建议写一条白纸黑字的规则：

transformBlockKind 当前版本只用于“空 paragraph → 特殊块”的转换，调用方必须保证源 block payload 是空的。否则禁止调用。

（以后你真要支持“把已有文本变成 list”，那会是一条新的命令，而不是重用现在的 transform。）

3. 删除统一走 deleteBlockWithGuard

“将所有 onRequestDeleteBlock 和菜单删除调用改成 commands.deleteBlockWithGuard，并确认 guard 在单块/特殊块路径里发 announceFocusIntent。”

这个非常关键，是整个 Plan165A 的落地：
从今天起，UI 层禁止直接碰 deleteBlock，一律走带 guard 的命令。

这里有三个注意点：

避免递归 / 双重删除

确保任何路径里不会出现：

deleteBlockWithGuard 里面又调用了 deleteBlockWithGuard；

或者 guard 调用 UI 回调，UI 再去调删除命令。

简单说：

“UI 只有一条入口：onRequestDeleteBlock → deleteBlockWithGuard；
命令层内部只能调用最底层的 deleteBlock 和 fallback 逻辑。”

特殊块降级 → paragraph 的策略要真的实现

之前你在 Plan165A 里写的是：

删特殊块时，如果这个位置不能空，就降级为 paragraph；

特殊块自己的 payload 清空（list items、quote meta 等）；

现在 wiring 全部指向 deleteBlockWithGuard，等于你终于要把这个“文字上的诺言”真正写成代码。
记得把「特殊块 id → fallback kind」做成一张明确的表，例如：

const BLOCK_DELETE_FALLBACK: Record<BlockKind, BlockKind | null> = {
  paragraph: null,
  bullet_list: 'paragraph',
  numbered_list: 'paragraph',
  todo: 'paragraph',
  quote: 'paragraph',
  callout: 'paragraph',
  // 以后 gallery 也可以接在这里
};


删除后 focusIntent 要统一从 guard 发出

单块场景：删掉特殊块 / 最后一个块 → guard 决定插新 paragraph / 降级，并负责 announceFocusIntent 到新 block；

多块场景：删中间的一个 → guard 负责决定“向上/向下邻居集火”，并发出 caretIntent；

UI 层不要自己偷偷 focusFirstBlock() 之类的东西，否则又会形成“第二套 caret 体系”。

4. “docs+rules 已经好了，核心命令还没真连上 UI”

Copilot 这句其实是在提醒你：现在是“把协议写成现实”的阶段。

我会建议你在 QuickLog 里显式记一条：

165B 的目标：让「文档中的 delete/transform 规则」与「所有 UI 操作路径」一一对应。
每接一条快捷键 / 按钮 / Slash 行为，都要核对：它是否走的是统一的 command API？

可以列一个小 checklist 去点：

Slash: paragraph → bullet / numbered / todo / quote / callout；

工具条按钮：把当前 block 改成 quote / callout；

Backspace 删除：paragraph / list / todo / quote / callout；

菜单里的“删除块”项；

书尾 CTA 上的删除（如果有）。

5. 这套方案整体有没有“大雷”？

只要你把前面提到的两个硬前提写死，雷就不大，反而是一次“收口”的机会：

Slash / 快捷键只对 空段落 起效果；

transform 只被用于“空段落 → 特殊块”的变换，内部清零 payload 属于“安全操作”。

真正会逼你大改架构的，是以后这些东西：

list 里要支持“把一段普通文字拆成多条 item”；

gallery / panel 里嵌子 block，有自己的小编辑器；

更复杂的 selection 显示 / 多光标。

那是下一阶段才会做的事，不在 165B 这波里。

6. 建议你再补一句到 RULES 里

给 Copilot 看的那种“红线式”条款，可以写成：

UI 层约束

任何创建 / 删除 / 类型转换 Block 的行为，必须通过 commands.* API，禁止直接改 store。

删除约束

UI 层只能调用 deleteBlockWithGuard(blockId)，禁止直接调用 deleteBlock。

Transform 约束

transformBlockKind 当前仅适用“空 paragraph → 特殊块”，调用方必须验证源 payload 为空。

这样你之后再看代码，就能很快发现“谁违反了宪法”。

小结

这个“新修复方针”逻辑上是对的，而且方向是“把零碎特例收束到统一命令里”，属于好事。

真正要注意的坑就两个：

transform + 清空 payload 必须建立在“只对空段落使用”的前提上；

所有删除都要走带 guard 的命令，避免 UI 有第二套删除/光标流。

把这两点写进 Plan 和 RULES，然后让 Copilot 开工是没问题的。
后面如果再冒出奇怪行为，多半就是哪里偷偷绕过了 command 层，那就好查了。