合表（table merging）这事，你当初想做的本质不是“数据库美观”，而是把多条 projection/daemon 的运维能力收口成一套：统一消费框架、统一看板指标、统一失败处理/DLQ、统一重放工具、统一 runbook。等你有 ≥2 个 projection（Search + Chronicle）以后，这个收益才从“没啥用”变成“翻倍”。

others-038-ES-outbox-to-daemon-…

下面我按“合表契机是什么 / 为什么当初说它值 / 什么时候不该合”给你捋清楚。

1) 合表要解决的“真正问题”是什么？

你已经体会过：Search 有一套 outbox worker、Chronicle 又来一套。继续长大就会出现：

两套 worker 脚本、两套 retry/backoff、两套 stuck reclaim

两套 metrics/告警、两套 runbook

两套 failed/DLQ/重放方式（甚至不同的状态字段与语义）

合表的核心动机就是：把“队列表”从按业务分裂，变成一个共享基础设施入口。

others-038-ES-outbox-to-daemon-…

一句话：合表是在增加共享基础设施，换取统一，但牺牲隔离。

others-038-ES-outbox-to-daemon-…

2) 为什么说“两个以上 projections 效果翻倍”？

因为在只有 Search 一个投影时，“统一 outbox”≈ 改个表名，收益有限，反而要付出 payload 治理、索引设计、迁移风险这些真实成本。

others-038-ES-outbox-to-daemon-…

当你有了 Search + Chronicle：

统一 DLQ：failed 的入口与重放命令统一

统一 runbook：排障流程、阈值、处理策略可以复用

统一 metrics：你能做一套“全系统 outbox backlog / oldest age / failed total / retry scheduled”等看板

统一 worker 能力：retry/backoff/jitter、stuck reclaim、graceful shutdown、health/readiness 等变成“一次实现，多处收益”

others-038-ES-outbox-to-daemon-…

这就是“翻倍”的来源：共享能力被第二个投影复用，边际收益突然变大。

3) 合表的“触发点/契机”通常是什么？

满足下面任意 2 条，合表就开始变得合理：

投影数量 ≥ 2（你现在已经是）

你发现自己在复制同一套 worker/daemon 运营机制（retry、stuck、DLQ、replay）

你需要统一的“事件处理可观测性”与治理（统一指标、统一告警、统一排障）

你要做跨投影的一致工具：例如一个 replay 工具能重放任意 projection 的 failed 事件

others-038-ES-outbox-to-daemon-…

4) 合表为什么让人翻车？（你当初担心的点）

因为合表的失败模式会从“某个投影坏了”升级成“心脏坏了全家遭殃”，而且最大坑不是迁移，是 payload 形状和索引需求互相打架。

others-038-ES-outbox-to-daemon-…

尤其是这条经典演化：payload 变垃圾场——每个投影临时塞字段、命名不一致、类型不一致、版本并存，最后 consumer 变成 if/else 博物馆，排障也痛苦。

others-038-ES-outbox-to-daemon-…

所以你当初提出“合表”时，配套才会同时提到：

payload 的 schema_version / event_type / projection（把它当协议/contract）

others-038-ES-outbox-to-daemon-…

consumer 先做 DTO 校验，确定性错误直接 failed，不重试

others-038-ES-outbox-to-daemon-…

5) 你现在该怎么理解“合表 vs 不合表”的边界？

你现在已经把 Search + Chronicle 初步做完了，下一步是否合表，用这个决策法最稳：

适合合表（偏“平台化”）

你想让 一个 daemon 处理所有 projection（按 projection/event_type 路由）

你想让 一个 DLQ/replay 工具链 覆盖全投影

你愿意承诺 payload 协议治理（schema_version/event_type 校验）

others-038-ES-outbox-to-daemon-…

暂时别合表（偏“隔离优先”）

某个投影 payload 很重、吞吐很高（会拖累其它投影）

你还没准备好 schema/版本治理（那合表几乎必然长成垃圾场）

others-038-ES-outbox-to-daemon-…

你更怕“全家遭殃”，宁愿多维护一套 worker

如果你愿意把你现在 Search/Chronicle 的 outbox 表结构（列 + 索引）贴一下/或发 migration 片段，我可以直接给你一个“合表时最小可行结构”：哪些字段必须升列、哪些索引能兼容两者、哪些字段绝对别进 payload（不然会爆炸）。