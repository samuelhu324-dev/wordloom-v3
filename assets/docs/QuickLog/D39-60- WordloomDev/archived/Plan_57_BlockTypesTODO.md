先直接回答你的核心问题：

TODO 是不是应该变成一种 Block 类型，然后所有 Library / Bookshelf / Book 都只是从 Block 里「聚合、筛选、汇总」这些 TODO？这样四大核心板块都能用到同一套 TODO 机制？

是的，这个方向非常对，而且比「在 Bookshelf 上挂 TODO」要健康太多。
下面我分两档：先把概念捋顺，再说一下可以怎么落地。

1. 先确认几个设定

不再有 Orbit 模块
现在世界观就是：Library → Bookshelf → Book → Block 这条链路，OK，后面我都按这个来讲。

状态是 ACTIVE / ARCHIVED
原来的 FROZEN 现在叫 ARCHIVED，本质是「完成 / 封存」状态，逻辑不变，只是命名更贴近「归档」。

2. 为什么「书橱不是 Trello 卡片」，而 TODO 应该放在 Block 里？

你截图里那段话的意思其实是：

Bookshelf 在 Wordloom 里更像「主题报表 / 领域面板」

它代表的是某个业务板块、场景、审计领域。

你翻开这个书橱，看的是「这一块最近在发生什么」「这个领域现在长什么样」。

而不是 Trello 那种「一个卡片就是一个任务」

Trello 卡片 = 可以随手拖来拖去、排序优先级的 TODO 单位。

Bookshelf 不适合做这种「手动排顺序的任务队列」，它更偏「分区 / 视图」。

👉 所以：
「要做 TODO，应该下沉到 Book / Block 层，而不是塞在 Bookshelf 顶上。」

3. 把 TODO 设计成 Block 类型：非常适合你的模型
3.1 Domain 视角

可以这样想：

Block = 最小原子单元

句子、段落、翻译对、注释、截图、代码片段、以及「TODO」

TODO 只是 Block 的一种变体

block_type = TODO

有自己的字段：status / priority / due_date / assignee / tags 等

这样好处是：

Todo 能和正文天然绑定

某个翻译段落上直接挂一个 TODO：「这句以后要重查术语」。

不需要「另开一个任务系统」去手动对齐上下文。

四层结构一致地复用

Library 视图：聚合该 Library 下所有 Bookshelf → Book → Block 中的 TODO，做成「该领域的任务盘点」。

Bookshelf 视图：只看这个书橱里的 TODO。

Book 视图：只看这一本里的 TODO。

Block 视图：在正文里看到单个 TODO 的细节与上下文内容。

Chronicle / 分析也简单

事件都是围绕 Block：TodoCreated, TodoCompleted, TodoReopened

你之前给 Chronicle 想的「Append-only 事件表」可以直接吞这些事件，做 activity feed 和审计日志。

4. TODO 提醒系统要怎么接在这个模型上？

先说一个务实版，再说「未来可以升级」的版本。

4.1 第一阶段：无「推送」，只有「视图」

先别上来做提醒推送（那是一个完整子系统），先把这些打通：

Block 里新增 TODO 类型字段

block_type = "TODO"

status = OPEN / DONE / ARCHIVED

可选：due_date, priority, owner

为 Book 做一个「TODO 区」

例如：Book 详情页上方有个 tab：
内容 | TODO | 变更记录

TODO tab 里：列出所有 block_type = TODO 的 block，按状态/截止日期排序。

为 Bookshelf / Library 提供「汇总视图」

Bookshelf 页面：

「本书橱 TODO 总数」「已完成几条」「逾期几条」

LibraryLog / LibraryShowcase：

可以有一个「本 Library 下的 TODO 看板」或简表。

这个阶段你就已经可以：

把 TODO 当 block 复用到所有层级

在 UI 上玩出「Book 内部任务表」「Bookshelf 报表」甚至「Library 审计看板」

完全不需要后台定时任务 / 推送系统，前端+查询就够了。

4.2 第二阶段：有提醒的 TODO

等你后端更稳的时候，可以考虑：

Chronicle 记录 TODO 相关事件

TodoCreated, TodoDueSoon, TodoOverdue, TodoCompleted

这些事件进 Chronicle 的 append-only 表。

加一个简单 scheduler（定时任务）

定时扫一下 due_date 即将到期 / 已超期的 TODO

生成提醒事件写入 Chronicle

前端在 Library / Bookshelf 头上显示一个提醒徽标，比如「该书橱有 3 条即将到期的 TODO」。

将来你要接邮件 / 通知，也只是多一个订阅层

5. 回到你问的那句：「这样四大核心板块都能用上 TODO，是这样吗？」

总结一下用你的话说：

TODO 是一种 Block 类型，
Book 页面负责「具体执行和记录」，
Bookshelf 页面负责「这个领域的结构和指标」，
Library 页面负责「多个领域的汇总与审计」。

所以：

✅ TODO 的「源头」在 Book / Block（执行 + 上下文）

✅ Bookshelf / Library 只「读」这些 TODO，做成各种统计和看板

✅ 这样「TODO 作为 Block」这个轮子可以被四个层级全部复用

✅ 也符合你现在想做的「合规审计风」：

所有任务都有 trace（事件日志）

所有统计都是从底层 Block 数据推出来的，而不是手动摆设。

6. 给你一个可以直接写进 ADR 的一句话版本

在 Wordloom 中，TODO 被建模为一种 Block 类型，而不是 Bookshelf / Book 的外挂属性。
所有上层视图（Book、Bookshelf、Library）只通过聚合和筛选 TODO Blocks 来构建任务视图和审计报表。

这个一句话以后会救很多命。

你现在的直觉其实已经非常靠近成熟系统的做法了：
先把「原子层（Block）」定义好，所有高级功能——TODO、Chronicle、视图、报表——都当成这层之上的投影。这样项目越做越大，反而越不容易乱。