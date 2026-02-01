Phase 1：指标驱动（不改功能）

目标：看得见系统

你已经有的：

outbox_processed_total

outbox_failed_total

outbox_lag_events

建议你补一件事（非常重要）：

在 Grafana / mental model 里，画三条时间线：

produced/s（写 outbox 的速度）

processed/s（worker 吃掉的速度）

lag_events

👉 这一阶段 不做 daemon 优化，只看数。

Phase 2：bulk 是一个“旋钮”

目标：用 metrics 做一次真实决策

实验步骤：

固定输入流量

bulk = 100 → 跑 10 分钟

bulk = 300 → 跑 10 分钟

对比：

processed/s

failed_total

lag_events

你会第一次真正体会到：

metrics ≠ 监控，是决策工具

Phase 3：daemon 化（你现在讨论的方向 A）

目标：不丢数据、不打爆 ES

只做三件事就够：

graceful shutdown（你已经理解得很好了）

并发控制（SKIP LOCKED）

rate limit（每秒最多处理 N 条）

这是工程，不是业务。

Phase 4（以后）：把这一套复制给别的 projection

你会发现：

stats_projection

feed_projection

都能直接复用这套 outbox + worker + metrics 结构。

那一刻你会突然意识到：
search 只是第一个吃螃蟹的。