1) 拆表 vs 合表：本质区别是什么？
拆表（你熟）

典型动机：性能、职责、冷热分离、可维护性。

把一个表拆成多个：每张表更单一，索引更有针对性

失败模式通常是“某张表设计不好/索引不对”，影响范围较局部

你可以对不同表用不同索引、不同字段、不同约束

一句话：拆表是在减少耦合、缩小爆炸半径。

合表（你还没踩过）

典型动机：统一运维入口、统一消费框架、统一看板、统一 DLQ。

把多个“队列表”合成一个“超级队列表”：所有 projection 都往里塞

失败模式变成“一个地方搞崩，全家遭殃”（尤其 outbox 是系统心脏）

最大难点不是迁移，而是：不同投影的访问模式/数据形态/索引需求互相打架

一句话：合表是在增加共享基础设施，换取统一，但牺牲隔离。

2) “payload 变成垃圾场”是啥意思？

当你把所有投影事件都塞进同一张 outbox_events(payload jsonb)，最容易出现这条演化路径：

Search 需要：{book_id, block_id, plain_text, tags...}

Chronicle 需要：{event_type, happened_at, actor_id...}

Media 需要：{file_key, mime, size, checksum...}

Stats 需要：{counter_delta, dimension...}

然后大家开始“临时加字段”：

这次我加个 foo，下次他加个 bar

有的叫 libraryId，有的叫 library_id

有的 book_id 是 UUID，有的是字符串

有的 payload 里嵌套巨大对象（甚至把全文塞进去）

老版本事件结构没迁移，新版本 handler 还得兼容

最后的结果是：

payload 的形状不稳定（每个投影、每个版本都不一样）

消费者代码变成 if/else 大拼盘（“如果 payload 有 X 就按新逻辑，没有就按旧逻辑”）

查询/排障困难（你看到一条 failed，但不知道 payload 是否缺字段、字段类型错、版本错）

长期维护成本爆炸（新人看到 jsonb：这坨到底应该长啥样？没人说得清）

这就是“垃圾场”：不是说 jsonb 不行，而是没有规则的 jsonb 会自动变成规则的坟场。

3) 为什么需要“严格的 schema 约束”？

因为你把 outbox 当成“通用队列”后，payload 就成了“协议（contract）”。

协议如果不约束，会发生两类致命问题：

A. 数据正确性问题（最烦的那种）

producer 写了一个“缺字段/类型错”的 payload

consumer 处理时报错（400 mapper parsing / KeyError / 类型不对）

然后进入重试/failed/DLQ

你排障时发现：不是 ES/网络问题，是 payload 结构烂了

这类 bug 的特点：发生得晚、定位慢、重试浪费资源。

B. 兼容性问题（系统演进杀手）

你升级了 payload 格式（比如 title 改名 book_title）

老事件还在表里，新 worker 已经按新格式读

于是 consumer 必须兼容多个版本：if payload.version < 2 ... else ...

很快 consumer 变成“版本博物馆”

所以你需要 schema 来保证：

写入时就验证：不合法的 payload 当场拒绝（或者进入单独的 failed 通道），不要进入队列污染系统

版本可控：明确 payload 的 schema_version，以及演进策略

字段命名一致、类型一致：减少消费者的 if/else 分支

4) “严格 schema”具体怎么做？（不一定要很重）

给你三种从轻到重的方案，你可以选符合你现在阶段的：

方案 1：最轻（强烈建议你至少做到这个）

payload 里加两个字段：

projection（你表里已经有）

schema_version（建议加）

event_type（BlockUpdated / BookUpdated …）

consumer 里按 (projection, event_type, schema_version) 路由到对应的 Pydantic DTO 校验：

校验失败：直接 failed（不重试），记录 error（这是确定性错误）

校验成功：再 process

这就能阻止“垃圾 payload”进入业务处理阶段。

方案 2：中等（当你有 2-3 个投影时很划算）

在 DB 层加一点约束（不写死字段细节，但至少防止离谱）：

payload ? 'schema_version'

payload ? 'event_type'

jsonb_typeof(payload->'schema_version')='number' 之类

或者把关键字段提升成列（例如 event_type 单独列），方便索引/统计

方案 3：重（大规模系统才常见）

用 JSON Schema / Avro / Protobuf 管理 payload 协议

schema 有注册表（schema registry）

消费者按 schema 版本解析

你现在完全不需要走到这一步。

5) 你现在为什么觉得“统一 outbox 早期收益不大”？

因为你只有 Search 一个投影时：

统一表 ≈ 把 search_outbox_events 改名 outbox_events（收益很有限）

迁移 + 索引设计 + payload 治理成本却是真实存在的

等你做 Chronicle（第二个投影）时，统一表的收益才明显：

统一 DLQ

统一 runbook

统一 metrics

统一重放/回放工具

最后给你一个“合表时的最小防腐要求”（很实用）

如果你将来合表，我建议你至少做到这三条，payload 就不容易烂：

payload 必须包含 event_type + schema_version

consumer 必须在 process 前做 DTO 校验

确定性错误（400/mapping/schema 校验失败）直接 failed，不重试

做到这三条，所谓“payload 垃圾场”基本就被堵住了。

如果你愿意继续往下挖，我可以用你现在的 Search 投影举一个很具体的例子：
同一张 outbox_events 里同时放 Search 和 Chronicle 时，索引为什么会互相打架（以及怎么设计索引才不会慢得像在沼泽里跑步）。