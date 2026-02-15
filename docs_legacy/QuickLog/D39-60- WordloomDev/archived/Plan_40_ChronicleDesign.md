一、Chronicle 先不管 Basement，可以。那计时 / 点击会不会“跨表”？

先说结论：

计时、点击这些统计，落在 Chronicle 里的时候尽量只绑在「最小业务单元」上（Book），
Bookshelf / Library 的统计靠“向上聚合”，而不是 Chronicle 表里直接跨表乱写。

1. 计时：Book 级别记录，Bookshelf / Library 用聚合

可以这样设计：

Activity / Chronicle 里只记：

FocusStarted(book_id, started_at)

FocusEnded(book_id, ended_at)

或者直接 WorkSessionRecorded(book_id, duration_minutes)

也就是：所有时间记录只认 book_id。

当你要看：

某 Book 花了多少时间：

直接按 book_id 聚合；

某 Bookshelf / Library 花了多少时间：

用 JOIN books ON chronicle.book_id = books.id，

然后再按 bookshelf_id / library_id 聚合。

这种“跨表”其实是 读模型 / 报表层的跨表，
不是在领域模型里把 Chronicle 和 Library 黏死，所以不会破坏 DDD 边界。

如果你担心每次 join 很麻烦，也可以在 Chronicle 事件的 payload 里顺手带个快照：

{
  "book_id": 123,
  "bookshelf_id": 45,
  "library_id": 7,
  "duration_minutes": 37
}


但主键关系依然以 book 为准，Bookshelf/Library 只是辅助维度。

所以答案：计时一定会“跨域使用这些 id”，但这是读侧聚合，完全没问题；
不要在 Chronicle 里写一堆 library_time_spent 之类列，保持事件“只认 book/actor/时间”，其它都靠聚合算。

2. 点击次数：也是事件，不是直接在表里+1

点击次数其实就是另一类事件，比如：

BookOpened(book_id, actor_id)

BookViewedFromShelf(book_id, source="bookshelf_grid")

Chronicle 里一条一条插入，
真正要展示时再去算：

某 Book 的打开次数：COUNT(*) WHERE event_name='BookOpened' AND book_id = X

某 Bookshelf 下所有 Book 总打开次数：join + group by

如果觉得每次 COUNT 太慢，可以再搞一个汇总表，比如 book_stats，
后台任务定时跑 jobs，把 Chronicle 的事件汇总成：

book_id | view_count | total_focus_minutes | last_opened_at ...


但那是下一阶段优化，现在你完全可以先走「事件 → 查询聚合」的简单模式。

3. Block 的 TODO / 标记

这个就先记在脑子里即可，将来你可以扩展事件类型：

BlockTodoAdded(block_id, note)

BlockFlagged(block_id, reason="need_review")

本质上还是 Block 级事件，
Chronicle 的模式不用变，只是多几个 event_name 而已。

二、状态指标：需要 Chronicle 吗？以及 Seed → Growing → Stable / Legacy 怎么设计？

你截图那个状态面板（Seed / Growing / Stable / Legacy + 完成度），
背后涉及两部分：

业务状态本身怎么流转？（domain 规则）

这些变化要不要写进 Chronicle？

1. 状态流转：给你一个当前阶段的“简化版规则”

先定语义（个人阶段版，不用太复杂）：

Seed：草创 / 灵感池

快速抓想法，可能很糙，可以随便删；

不计入“完成度”，或者权重很低。

Growing：施工中

已经开始翻译或整理，但还没最终定稿；

Stable：已稳定

自己认为可以对外使用 / 复用；

计入“完成度”的主力；

Legacy：过时 / 仅做参考

旧版本、历史稿，暂时不想删，但也不算“当前成果”。

最小转移规则，可以这样定：

新建 Block 默认：Seed

正常流程：
Seed → Growing → Stable → Legacy

回退允许但受控：

Stable → Growing（发现错误，要重新打磨）

Stable → Legacy（定了新版本，这条成旧版）

Legacy → Growing（偶尔你又想翻修旧货）

你可以在 DDD_RULES 里写两条硬规则：

完成度计算只看 Stable（或 Stable+部分 Growing），Seed/Legacy 不算进度
（例如：completion = stable_blocks / (seed+growing+stable)，legacy 不算）

任意状态修改都必须通过 Block 的领域方法：

block.mark_growing()

block.mark_stable()

block.mark_legacy()

这样以后前端就不会自己乱改 status 字符串，而是打到对应 API。

2. 这些状态变化，需要 Chronicle 记录什么？

不用为每个“计数变化”记一条事件，
只要记录“Block 的状态变了”这一件事就够了：

事件名：BlockStatusChanged

payload 里带：

{
  "block_id": 123,
  "book_id": 45,
  "old_status": "seed",
  "new_status": "growing"
}


后面任何需要：

某 Book 的状态变化时间线；

某天新变成 stable 的 block 数；

某本书“第一次变 stable 的时间”；

都可以从这些事件推出来。

状态面板上的数字（Seed/Growing/Stable/Legacy 数量 + 完成度）更适合这样算：

短期：直接从 blocks 表里用 COUNT WHERE status='seed' 之类语句汇总；

长期：可以在 Book 聚合里维护缓存字段 seed_count / growing_count / stable_count / legacy_count，
在 Block 状态改变时同步更新，这样查询更快。

Chronicle 的作用是“留痕 + 时间线”，不是替代这些计数逻辑。

所以回答你的问题：
状态变化“本身”值得写进 Chronicle（BlockStatusChanged），
但 Seed/Growing/Stable 数量这种 dashboard 指标，用普通统计/缓存字段算就行，不必每次变化都额外写一条“StableCountChanged”。

三、综上帮你收个行动版 todo

结合你现在的阶段，可以这样落地：

先做 Book / Block 的 status 字段 + 基本转移 API

POST /blocks 默认 seed；

PATCH /blocks/{id}/status 支持 seed/growing/stable/legacy 转换（按上面的规则限制）。

Book 页面顶部的状态面板

后端：查询 block 表做 4 次 COUNT，返回 { seed, growing, stable, legacy }；

前端：算出完成度 %。

Chronicle 暂时只加 2 个事件：

BookCreated

BlockStatusChanged
（BlockAdded 可以下一步再加）

计时 / 点击

现阶段可以先只做简单的 BookOpened 事件（点击次数）；

真正“在这个 Book 上呆了多久”的 session 统计，等 Book 页面、Block 刷新体验稳定一点后，再拉一条 Activity → Chronicle 的小 pipeline，不急着一次性上。

这样你既不会被 Basement / 全局计时拖进大泥潭，
又能让 Book / Block / 状态面板这条链路完整地跑起来——
到时候截几张图 + 展示一下状态流转逻辑，对任何老板看都是“这个人脑子里是有模型的”。