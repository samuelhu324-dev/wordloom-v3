1) 什么是「动作上下文」？

你可以把 Chronicle 理解成“审计 / 时间线 / 活动流（activity feed）”体系。它记录的不是“最终状态”，而是发生过的动作。

动作上下文（action context）= 让一条事件具备“可读性 + 可追责性 + 可复盘性”的那堆信息。典型包括：

谁做的：actor_user_id（或 actor / owner）

对哪个对象做的：entity_type + entity_id（book / block / tag…）

做了什么：event_type（BookRenamed / BlockUpdated / TagAdded…）

从什么变成什么：before/after（或 diff）

何时：occurred_at（业务时间）+ created_at（写入时间）

在哪/通过什么：request_id、device/client、ip（可选）

为什么/附注：reason/comment（可选）

为什么说它很多信息不是“当前 state”能推回来的？
因为“当前状态”通常只有 after。比如你只看 book.title=New，你不知道它是从哪个旧 title 改来的、谁改的、当时是不是批量操作、是不是回滚导致的二次变更。这些都属于动作上下文。

所以 Chronicle 的“源”往往更像事件日志（event log），而不是一张“当前状态表”。

2) Chronicle 这种“时间线规则会变”的投影，怎么测试？

你担心得很对：Search 投影好测，因为“输入→输出”很机械；Chronicle 可能会不断改“摘要规则/展示规则”，看起来就像永远测不完。

解决办法：把测试拆成两层——“事件真相”稳定，“投影规则”可演进。

A. 先确认 SoT（事件源）稳定：chronicle_events

这层测试关注：

事件有没有被正确写出来（字段齐不齐、actor 对不对、entity 对不对、occurred_at 是否正确）

写入是否遵守授权/隔离（scope：library_id / user_id）

顺序/幂等键是否可用（event_id）

这层一旦稳了，你就有“可回放的真相胶片”。

B. 再测试 Projection（读优化结果）：“同一批 events → 产物是否符合当前规则”

你提到“timeline 刷新规则会变”——没错，所以投影测试要像“编译器测试”：

1）Golden fixtures（金样例）
准备一小批固定的 chronicle_events（10～50条就够），包含：

rename、update、delete、move/restore 这类关键动作

同一对象连续操作（测试合并/去噪/摘要）

多对象交织（测试排序、分页）

边界：空字段、超长文本、奇怪字符

然后跑一次 projector/rebuild，断言：

chronicle_entries 的条数、排序

summary 文本（或结构化字段）

关键可过滤字段（book_id、actor、day、event_type…）

当你改规则后，这套测试会告诉你“哪些输出变了”。你再决定：这是“预期变更”（更新 golden），还是“引入 bug”。

2）规则版本化（强烈建议）
如果你未来真的会频繁改摘要/合并逻辑，给投影产物加一个 projection_version（或 summary_version）非常值：

新规则上线：rebuild 产出 v2

老规则数据：仍可识别 v1（便于回滚/对比）
这让“规则演进”从噩梦变成流程。

3）时间相关怎么测？
Chronicle 的“时间线”最常见坑是分页/窗口：

用固定的 occurred_at（不要用 now），或者用“冻结时间”策略

测试 API 的分页：按 (occurred_at, id) 做稳定游标

测试“按天聚合/按 book 聚合”的正确性（尤其跨天边界、夏令时这类坑）

4）端到端观测（你已经很擅长这套）
你做过 Search 的 metrics，那 Chronicle 也可以复制：

lag_events / oldest_age_seconds / inflight

rebuild_duration / last_success_ts

按 library_id 维度（后面真做多租户/隔离时救命）

结论：Chronicle 不需要“不停刷新 UI 规则就没法测”。你只要把“事件源固定 + 投影规则可演进”这两层分开，测试就会非常工程化。

3) Chronicle 投影结果到底是什么？（截图3 那两种选项）

你看到的其实是在问：Chronicle 你想把“读模型”做成什么形态？

选项 A：chronicle_entries（面向 UI/筛选/全文/聚合 的读表）

源：chronicle_events（不动）

投影：chronicle_entries（或 chronicle_event_summaries）

好处：

UI 查询快（按 library/day/book/actor 过滤、分页稳定）

summary、可筛字段都预先算好

很适合“活动流/审计/时间线”这种读密集场景

代价：要维护 projector + rebuild

这通常是“第二个投影”最稳的选择，因为价值明显、边界清晰。

选项 B：chronicle_events 不动，只做“额外索引/聚合表”

比如：

chronicle_rollup_by_day（按天计数/摘要）

chronicle_rollup_by_book（每本书最近 N 条、计数）

chronicle_rollup_by_actor（某人活动统计）

它更偏“Stats/Dashboard”的风格：事件源不动，只加几个报表型投影。

4) 你问的 outbox 表策略：先独立，再合并？（你的理解非常接近正确）

一般生产落地的“最不后悔路线”是：

每个投影先独立 outbox 表（search_outbox_events、chronicle_outbox_events）

改动面小、风险小、好回滚

每个投影可以有自己最合适的索引/字段（尤其 payload 形状不同）

当你真的有 ≥2～3 个投影都稳定跑起来了，再考虑合并成通用 outbox_events + projection 字段

运维面板统一、DLQ统一、rebuild统一

但要严格约束 payload schema（不然会变“垃圾场”，你之前问的点就在这）

所以你那句“先走独立 outbox，再考虑合并”很靠谱：可逆、风险小、学习曲线也更平滑。

3) Chronicle 投影结果到底是什么？（截图3 那两种选项）

你看到的其实是在问：Chronicle 你想把“读模型”做成什么形态？

选项 A：chronicle_entries（面向 UI/筛选/全文/聚合 的读表）

源：chronicle_events（不动）

投影：chronicle_entries（或 chronicle_event_summaries）

好处：

UI 查询快（按 library/day/book/actor 过滤、分页稳定）

summary、可筛字段都预先算好

很适合“活动流/审计/时间线”这种读密集场景

代价：要维护 projector + rebuild

这通常是“第二个投影”最稳的选择，因为价值明显、边界清晰。

选项 B：chronicle_events 不动，只做“额外索引/聚合表”

比如：

chronicle_rollup_by_day（按天计数/摘要）

chronicle_rollup_by_book（每本书最近 N 条、计数）

chronicle_rollup_by_actor（某人活动统计）

它更偏“Stats/Dashboard”的风格：事件源不动，只加几个报表型投影。

4) 你问的 outbox 表策略：先独立，再合并？（你的理解非常接近正确）

一般生产落地的“最不后悔路线”是：

每个投影先独立 outbox 表（search_outbox_events、chronicle_outbox_events）

改动面小、风险小、好回滚

每个投影可以有自己最合适的索引/字段（尤其 payload 形状不同）

当你真的有 ≥2～3 个投影都稳定跑起来了，再考虑合并成通用 outbox_events + projection 字段

运维面板统一、DLQ统一、rebuild统一

但要严格约束 payload schema（不然会变“垃圾场”，你之前问的点就在这）

所以你那句“先走独立 outbox，再考虑合并”很靠谱：可逆、风险小、学习曲线也更平滑。

你现在应该怎么走下一步（不浪费时间的版本）

你已经把 Search 投影做得很完整了。接下来要把“daemon 化”能力变成通用肌肉，我建议你把第二个投影选成：

Chronicle：chronicle_events → chronicle_entries（读优化）

Outbox 仍先独立：chronicle_outbox_events

测试用 golden fixtures + rebuild 对照

观测指标照搬 Search 那套（投影维度换成 chronicle）

这样你会把同一套“claim/lease/retry/failed/DLQ/runbook”的骨架再复用一次——真正完成从“做成一个投影”到“做成一类投影系统”。