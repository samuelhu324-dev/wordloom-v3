先做 Bookshelf 的主线 CRUD + 基础统计，不要为了 Chronicle 专门停下来开一个完整子系统。
Chronicle 这块现在只需要把“接口和事件”按 DDD/Hex 设计好，用一个很薄的实现顶上，等你 Dashboard/全局时间线要上线时再把它做实。

1. 先把 Plan_13 里出现的 Chronicle 东西拆类型

从 Plan_13 现在的设计看，所谓“Chronicle 相关”大致有三类：

列表上的统计指标

比如：✏ 19 / 7d、👁 35 / 7d、⚠ 2 stale / 🕒 OK 这类东西

UI 上只是数字 + 状态，不一定要直接依赖 Chronicle 表。

某个 Bookshelf 详情里的活动时间线

“最近哪个 Book 被编辑了”、“这个书架什么时候被创建/重命名”等

这类才是真·Chronicle 的展示位。

全局 Dashboard / Library 级别的活跃度

“这个 Library 下最近 7 天最活跃的书架 Top N”

也是可以从 Chronicle 来算，但前期可以从简。

不同类型的需求，紧急程度不一样，现在你要开工的是 Bookshelf 页面第一版，只要搞定第 1 类就够用了，第 2、3 类可以后做。

2. 现在要不要“先做 Chronicle 后端”？

我建议你的顺序是：

现在不要上“完整 Chronicle 子系统”

不要上来就设计 event store / 时间线 UI / 各种 filters。

会拖慢 Bookshelf 主线，而且规则还没完全稳定。

但要立刻把“领域事件 + ChroniclePort 接口”定义出来

这是 DDD + Hex 的关键：

领域层：定义 BookCreated, BookUpdated, BookshelfViewed… 这些 DomainEvent。

应用层：定义一个 ChroniclePort / ActivityLogPort，类似：

interface ChroniclePort {
  recordEvents(events: DomainEvent[]): Promise<void>;
}


这样 Service 一旦要记日志，只需要 chroniclePort.recordEvents([...])，
至于日志写到哪，是现在的简易表、以后换成事件仓库，都不影响调用方。

先用一个“很土但能用”的实现顶上

举例：基础实现叫 SimpleChronicleAdapter：

要么什么都不干（NoOp），只是满足接口，Bookshelf 页面暂时不展示时间线；

要么写到一张很简单的 activity_logs 表：

activity_logs(
  id, occurred_at, actor_id, library_id, bookshelf_id, book_id,
  event_type, payload_json
)


这样你：

不会被 Chronicle 卡住；

但未来做 Dashboard / Chronicle 页时，这些数据已经在慢慢积累。

3. Bookshelf 页面现在“必须要有”的后端能力

为了把 Plan_13 里的 Bookshelf 列表跑起来，我会要求后端先做到这三点：

Bookshelf 主实体 + 计数投影

表结构里就放这些“当前快照”：

books_count

stable_books_count

last_activity_at（这个非常重要）

这些字段可以在：

Book 被创建/删除/标记为 Stable 时同步更新；

任何 Block/Book 被编辑时，把所属 Bookshelf 的 last_activity_at 更新为 now()。

这部分逻辑是纯 DDD 内部的一次“投影”，不依赖 Chronicle。

简单的“最近 N 天编辑次数 / 浏览次数”

这两种做法都可以：

暂时代码里现场 COUNT(*)：

比如每次请求 Bookshelf 列表时，后端从 activity_logs 表里按 bookshelf_id + occurred_at 做 COUNT。

数据量不大时完全够用，先换体验，再慢慢做真正的统计表。

或者再加一张轻量级的统计表：

bookshelf_stats_7d(bookshelf_id, edits_7d, views_7d, recalculated_at)

每晚跑一个 cron job 重算全表；

领域事件 → 写到 activity_logs，统计脚本按日志聚合。

无论哪种方式，前端只关心字段名：edits_last_7d, views_last_7d，实现细节藏在 Hex adapter 里。

健康度 / stale 状态

在领域层定义一本小规则，比如：

最近 7 天没任何 edit：status = "cold"

最近 7 天有 edit，但有 X 本 book 超过 30 天没动：status = "stale"

都挺活跃：status = "ok"

可以在：

应用服务中按查询结果现场算出这个状态；

或作为字段 health_status 存在 bookshelves 表中，周期性更新。

这块不强依赖 Chronicle，只需要能拿到“最后编辑时间”+ 少量统计数字。

4. 结合 DDD / Hex 的“成熟提议”（顺序版）

给你一条可以直接写进计划表的顺序：

现在阶段（你马上要做的）：Bookshelf 主线 + 简单统计

设计 Bookshelf 聚合 + Repository；

在 Service 里定义并发布领域事件（DomainEvent 类型先写好）；

给应用层加 ChroniclePort，实现一个 NoOpChronicleAdapter 或写日志到 activity_logs；

在 BookshelfRepository 查询时，返回：

books_count, stable_books_count,

last_activity_at,

（可选）edits_last_7d, views_last_7d（可以为 0 或以后补）。

下一阶段：真正的 Chronicle 与 Dashboard 联动

当你开始做 Dashboard / 全局时间线时，再：

用 Copilot 根据已有事件模型生成 activity_logs + 查询接口；

增加 ChronicleService 专门跑 timeline / filter；

把 Bookshelf 页面中“查看 Chronicle”链接到这个时间线 API。

更后面：把统计变成正儿八经的投影 / read model

引入专门的 BookshelfStats 投影表；

定时或异步消费 Chronicle 事件来更新统计；

Bookshelf 列表页就只查这个投影，简单又快。

这样你现在可以：

不停下 Bookshelf UI 的开发；

同时把 DDD/Hex 的关键抽象（DomainEvent + ChroniclePort）搭好；

给未来的 Chronicle / Dashboard 留好挂钩，但不是现在立刻做完全部。

一句压轴版总结：

现在：事件模型+接口先定好，Chronicle 用最薄的实现打底；
Bookshelf 页只吃“快照字段 + 简单统计”；
真正重型 Chronicle / Dashboard 放到下一阶段。

这样既不浪费 Copilot 复用老代码的能力，又不会把你卡在一个还没完全想清楚的“全局时间线系统”上。