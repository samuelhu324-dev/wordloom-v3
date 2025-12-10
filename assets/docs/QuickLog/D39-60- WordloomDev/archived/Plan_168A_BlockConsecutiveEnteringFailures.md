## 2025-12-10 回填

- **Outcome:** 连续 Enter 不再把列表炸成两段 paragraph：keyboardDecider + ListBlock shell 只在 `allItemsEmpty=true` 且第二次 exit 时才调用 guard，其余场景全部在行级创建/删除 item，Plan168A 指出的回归完全清零。
- **Code refs:** `model/keyboardDecider.ts`（listFamily exit 判定）、`ui/ListBlock.tsx`（pendingExitRef + handled flag）、`ui/BlockItem.tsx`（尊重 handled= true 即不再 submit）以及 `useBlockCommands.deleteBlockWithGuard` 的单入口策略现已合并。
- **Tests:** `ListBlock.test.tsx` 追加 “空列表双 Enter 仅留下一个 paragraph” 断言 + Playwright 行走场景；本地 QA 重复“插入 list → 连续 Enter/Backspace”再也无法复现 Issue。

先把你的两个问题掰开：

（1）连续 Enter 现在会把 list 打碎成两个 para；
（2）Copilot 这套 “把 Enter 权限下放给 ListEditor” 的提议靠谱不？

先说现象：为什么“连续 Enter 把 list 打碎成 para”

典型场景大概是这样的：

你在普通段落里输入：- xxx → 触发 markdown shortcut，变成一个 list item block；

在这个 list item 里按一次 Enter：按规则应该是新建下一条 list item；

接着在空的 list item 上再按一次 Enter：

正常期望：退出列表，把光标移到列表下面的 paragraph；

你现在遇到的是：

列表被拆成两个普通 paragraph block，

有时还会出现“上一条 list item 也被降级成 paragraph”，列表壳子直接碎了。

这本质上是：

列表退出逻辑（“空最后一项 + Enter 退出列表”）

和通用的 paragraph Enter 逻辑（“非空拆 block / 空 block 创建下一个 block”）

在同一帧里都抢着处理一次 Enter，
所以你看到的是“先退出 list，再按 paragraph 的规则硬拆一次”，结果整个 list 被拆成两段普通段落。

再看 Copilot 的方案：它想干嘛？

Copilot 的核心思路其实就一句话：

列表里的 Enter 行为不要再和普通 ParagraphEditor 混在一起，要由 ListEditor 一家说了算。

它拆成三步：

隔离列表的 Enter 行为

给列表项用的 ParagraphEditor 加一个 mode: 'list-item' 或 onEnter 回调：
在这个模式下，ParagraphEditor 不再自己提交/创建 block，而是把 Enter 交给 ListEditor 处理；

这样 ListEditor 可以完全控制“插入新列表项 / 退出列表”，
不会再被 BlockItem / handleEditorSubmit 抢走。

在 ListEditor 里做一个专门的“状态机”

比如有 editing / pending-exit / exiting 等状态，结合：

当前 item 文本是否为空

是否最后一项 isLastItem

是否整条列表都空 allEmpty

来决定：当前这次 Enter 是“新增一项”还是“退出列表”。

加一套 ListEditor 的测试和回归

专门模拟“空列表连续按 Enter”“先输入再清空再 Enter”等路径，

保证以后改动不会搞崩。

翻译成白话：

它是想把 “列表是什么时候结束的” 这件事，从 ParagraphEditor/BlockItem 抽出来，塞到 ListEditor，一个人管完。

这和你刚刚那句“能不能别老缝缝补补，一次性解决 Enter 的问题”其实是同一个方向：
去掉双重监听，集中决策点。

这套提议的优点

我先给它点几个赞，免得 Copilot 太伤心 😂：

直指真正的病根
它已经看出来：

现在 ParagraphEditor → BlockItem 的“创建新 block”策略

和 ListEditor 内部的“在列表里插入/退出”策略
在同一次 Enter 上冲突。
它的解法就是“把 Enter 的控制权搬到 ListEditor”。

对列表这种“特殊 block 类型”做局部集中管理
列表的行为确实比普通段落复杂：

连续 Enter 的退场规则

空列表整个删除 vs 留一个空 item

后续如果有嵌套 list、缩进/反缩进
单靠 ParagraphEditor 的通用逻辑是救不了场的，让 ListEditor 统筹是合理的。

想着配套写测试
这一点非常好：

一旦你给 ListEditor 写上了几条 Enter/Backspace 的关键用例，

之后你再改 keyboard pipeline 时就不会再“改一处，爆一片”了。

风险 & 不足：哪里容易把自己又绕晕

我不会说它“错”，更多是太大一口、容易噎住：

和你刚立起来的“全局 keyboardDecider”有点打架

我们前几轮刚刚说好：

所有按键行为集中到一个 decideEnterAction(ctx) 或类似东西里，

ParagraphEditor 只算状态，BlockItem/EditorShell 执行命令。

Copilot 现在又搞一个“列表专属 Enter 流程”塞到 ListEditor 里，
如果你照单全收，就变成：

一部分 Enter 在全局决策器里走，

一部分 Enter 在 ListEditor 的内部状态机里走，

又出现了两个“真相点” —— 只是之前是 PEditor + BlockItem，现在是 KeyboardDecider + ListEditor。

解决办法不是否定它，而是：
👉 把“列表逻辑”当成 decideEnterAction 的一个分支，而不是再造一个平行系统。
简单讲：ListEditor 只提供上下文（isLastItem/allEmpty），真正决定还是那一个决策函数。

状态机那块有点 overkill

什么 editing / pending-exit / exiting 之类的状态，
在你现在这个规模下，可能暂时用不上这么复杂的 FSM（有限状态机）。

对“连续 Enter”的核心其实就三条判断：

当前 block 是不是 list item？

当前 item 是不是空？

当前 item 是不是列表最后一项？（以及整条列表是不是只剩一个 item？）

这三条就足够覆盖：

非空 list item + Enter → 新建下一个 list item

空的 中间 list item + Enter → 删除当前 item，光标到下一项

空的 最后一个 list item + Enter → 退出列表，创建/切换成 paragraph

所以我会建议：先用粗暴的布尔条件把行为稳定下来，再考虑要不要收成状态机。

ParagraphEditor 加 mode: 'list-item' 会让它变得“知道太多”

这件事可好可坏：

好处：可读性很直观，“这个 editor 是专门给列表用的”；

坏处：以后每新增一个特殊 block（todo item、quote item、callout item），你都可能想加一个 mode，最后 ParagraphEditor 变成 block type 大字典。

一个折中办法是：

ParagraphEditor 不直接知道 “list vs non-list”，

而是知道 “是否把 Enter 交给外部处理”：

比如一个 onSoftEnter / customEnterHandler，

列表就传一个 handler，普通段落就不传（走默认）。

这样 ParagraphEditor 还是保持“通用文本编辑 + 可选 hook”，不直接认 block 类型。

推荐你怎么用这份提议（不被它反噬）

我会这样改写它，让它兼容你现在的总体设计：

1. 在“全局键盘决策器”里加 list 分支，而不是在外面再造一套

伪逻辑：

function decideEnterAction(ctx) {
  if (ctx.blockType === 'listItem') {
    if (!ctx.isEmpty) {
      return 'CREATE_NEXT_LIST_ITEM';
    }
    if (ctx.isEmpty && !ctx.isLastItem) {
      return 'DELETE_THIS_LIST_ITEM';
    }
    if (ctx.isEmpty && ctx.isLastItem) {
      return 'EXIT_LIST_TO_PARAGRAPH';
    }
  }

  // 其他 blockType（paragraph/quote/...）走通用规则
}


这里的 isLastItem / allEmpty 就是 Copilot 说要在 ListEditor 里汇总的那些上下文，
但决策仍旧只在一个地方发生。

2. 让 ListEditor 负责提供上下文，而不是负责“再做一套判断”

ListEditor 提供 getListContext(blockId)，返回：

isLastItem

allEmpty

……你需要的那些聚合状态；

ParagraphEditor → EditorShell 在触发 Enter 时，把这些 context 填进 ctx，丢给 decideEnterAction。

这样就达成你和 Copilot 的“双赢”：

你：只有一个 keyboard 决策器，世界观清晰；

Copilot：ListEditor 仍然是唯一知道“列表整体长什么样”的地方。

3. 用 Copilot 的“测试建议”，但别急着上状态机

它说的这句我非常同意：

写一个针对 ListEditor 的交互单测 / Cypress flow，模拟“空列表连续按 Enter”“先输入再清空再 Enter”等关键路径。

你就照它的几个场景，把 E2E/集测写出来：

- a 回车 → list item1 有内容，生成 list item2 空；

再回车 → item2 空 + last → 退出 list，生成 paragraph；

中间项空回车 → 删除这一项，光标到下一项；

所有项删空 + 再回车 → 可以直接删掉整个列表 block，变成一个空 paragraph（看你想要哪种规范）。

有了这个测试网，你再调 decideEnterAction 和 ListEditor，就不会怕“连续 Enter 又把 list 打爆”。

最后一句人话总结

你现在剩下的这个 bug（连续 Enter 把 list 弄碎）就是典型的**列表退出规则和通用 Enter 规则“连环触发”**导致的；

Copilot 提议的方向是对的：把 Enter 的控制权集中到 ListEditor 一侧，不要再前后端、PEditor、BlockItem 一起乱抢；

但直接照着它那套“ListEditor 自己再玩一套状态机”去做，容易重新制造新的“双真相”，
更稳的做法是：

让 ListEditor 提供列表上下文，

你的全局 decideEnterAction 根据 blockType+上下文做唯一决策，

测试围绕“连续 Enter/退出 list”写好，就能一次性把这条线稳定下来。

这样你既不在缝缝补补，又不会被状态机拖着跑偏，后面加 todo list / checklist 时也只是在 list 分支上再加一点点条件。