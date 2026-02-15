这个问题问得特别对，现在这个 Book 页已经长得挺“正经”的了，剩下就是把 Block / TODO / 生命周期 这几块接成一条线。

我直接给一套“可以写进 RULES 的方案”：

1. 先分工：三个层级各干啥

Block 层：

真正的 内容编辑 和 TODO 勾选 发生的地方。

有 Todo Block、Checklist Block 之类的类型（你在 BlockTypes 里已经列过了）。

Book 页的 TODO Tab：

是对「本书所有 TODO 的聚合视图」，方便集中扫一眼、集中处理。

你可以把它理解成：“把散落在各个 Block 里的 TODO 抽出来，做一张任务清单”。

时间线 Tab：

是 Book 的生命周期 / 重大事件日志，记录：创建、阶段变化、重要操作、重要 TODO 完成等等。

给你未来做审计、回顾、成熟度计算提供依据。

所以答案先说一句：

✅ 是的，Book 页里的 TODO 列表应该和 Block 里的 Todo Block 联动，
但建议做“选择性同步”，不是所有带勾的列表都堆进去。

下面展开。

2. Book TODO Tab 和 Block Todo Block 怎么联动？
2.1 数据模型：Todo Item 作为“Block 的子实体”

建议不要只靠纯文本识别：

给每个 Todo Block / Checklist Item 一个结构化实体，比如 todo_items 表：

id

book_id

block_id

text

status（open / done）

created_at / completed_at

priority / due_date（可选）

is_promoted（重点：是否要在 Book 级 TODO 里显式展示）

在编辑器里：

勾选 / 修改 Todo 文本 → 同步更新 todo_items

删除该条 Todo → todo_items 软删除或标记为 deleted

2.2 哪些 Todo 项要出现在 Book 页 TODO Tab？

并不是每个“随手打的 checklist”都值得上 Book TODO 列表。
给你一个可操作规则：

默认规则（简单版）：

只要是 Todo Block 里的条目，统统出现在 Book TODO Tab；

以后觉得太吵，再加过滤。

进阶规则（推荐）：用 is_promoted 控制“升级为 Book 任务”

在 Block 里对某条 Todo：

普通点击复选框 = 完成/未完成；

“星标” / “升级按钮” = is_promoted = true，这条就出现在 Book 页 TODO 列表。

同理，在 Book 的 TODO Tab 里：

可以“降级”为普通 checklist（取消星标），从 Book 任务视图里隐藏，但在原 block 里仍然存在。

这样你可以区分：

“写作过程中的小勾勾”（只在当前段落附近有意义）

vs “这本书必须完成的任务”（应该出现在 Book TODO 汇总）

2.3 联动行为举例

在 Block 里勾选一个 已升级的 Todo →

Book TODO Tab 里对应条目同步变为 done；

时间线可以记录一条事件：“完成任务：xxx”。

在 Book TODO Tab 里修改一条任务（例如截止时间、优先级） →

同步更新对应 todo_items；

Block 里对应那行的显示也更新（比如右侧的小日期）。

在 Book TODO Tab 里点击某条任务的“定位”图标 →

跳转回对应 Block，并高亮那条 Todo。

这样用户的心智会非常自然：

“在 Block 里写 & 勾，在 Book 里集中看 & 管。”

3. 时间线 Tab：记录什么？和成熟度有什么关系？

你现在时间线 Tab 写的是“最近的书籍生命周期事件”，这个方向是对的。
可以把它设计成“Book 级 Chronicle”的一个视图。

3.1 时间线的事件来源

建议至少有三类：

生命周期类事件（Lifecycle）：

创建 Book

Seed → Growing / Growing → Stable 的阶段变化

标记为 Active / Archived / Legacy

从某个 Bookshelf 移动到另一个

结构变化事件（Structure）：

第一个 Block 创建

Block 数达到阈值（比如 10、50、100）

第一次添加 Tag / 改名

Book 被 Pin / 取消 Pin

任务 / 审计相关事件（Todo / Review）：

升级了一个 Todo 项（变成 Book 级任务）

完成一个“升级任务”

触发一次“自检 / Review”操作（比如你以后做一个“本书已自检”按钮）

未来如果接 Orbit / Chronicle 全局，你还可以把全局日志按 Book 过滤出来展示在这里。

3.2 和成熟度（maturity）怎么挂钩？

你之前我们讨论的成熟度模型，大概是：

基于：结构完整度 + Block 数量 + TODO 完成情况 + 活跃度 等打一个 score

映射到 Seed / Growing / Stable。

时间线可以：

在每次 score 造成阶段变化时，写一条事件：

2025-11-28：阶段从 Seed 变为 Growing（score 34 → 51，Block 数 12，完成 TODO 3/5）

在时间线 Tab 上用一个小徽标标出“阶段变更节点”，看起来像产品里常见的“里程碑点”。

这样 Overview 页的「当前阶段」卡片和 Timeline Tab 就形成闭环：

概览：只显示“当前阶段 + 当前几个关键数字”；

时间线：告诉你“它是怎么走到现在这个阶段的”。

4. 回到你截图里的两块区域，怎么填内容比较顺
4.1 概览页里的 TODO / Checklist 卡

标题：Todo / Checklist

内容：展示当前 Book 级 Todo 的一个摘取版：

比如只显示 3 条未完成任务 + 一个“查看全部任务”的按钮（跳到 TODO Tab 或 Block 编辑页的任务视图）。

文案可以从现在这句“此处暂作占位…”升级为：

有任务时：

「还有 3 个待办需要处理。」

没任务时：

「暂无待办，你可以在块编辑中添加 Todo，重要项会自动汇总到这里。」

4.2 时间线 Tab

空态（空 book）：

像你截图写的那样：“暂无事件，完成首次操作后将显示历史记录。” + 一个时钟 icon 很好。

有事件时：

按时间倒序列出事件，每条包含：

时间

类型小标签（阶段变更 / Todo / 结构 / tag 等）

描述文本（尽量人话，比如“完成任务：检查术语翻译”）

右上角「显示访问日志」勾选框可以用来：

开关一些噪音事件（例如“打开 Book”、“查看 Block”这种纯浏览行为）。

5. 压缩成一段你可以写进 RULES 的话

Todo 源于 Block，聚合于 Book。

Todo/Checklist Block 中的条目以 todo_items 存储；

打上 is_promoted = true 的条目会出现在 Book 的 Todo 面板；

Block 内勾选/修改会同步更新 Book 级 Todo 列表，反之亦然。

Book 的 Todo Tab 用来集中管理“升级后的任务”，Overview 只展示其中一小部分。

时间线 Tab 展示 Book 的生命周期事件和关键操作：

创建、阶段变更（Seed/Growing/Stable）、归档/恢复；

结构里程碑（Block 数、改名、移动）；

重要 Todo 的创建和完成；

可选：访问/查看日志。
阶段变更会作为特殊事件显示，并与成熟度打分系统联动。

这样一来：Block、Book TODO、时间线、成熟度，这四块就不再是四个孤岛，而是变成一条“书的生命线”：
从 Block 里的一个小 Todo 勾勾，到 Book 上的阶段标签，再到时间线上的一个里程碑事件。