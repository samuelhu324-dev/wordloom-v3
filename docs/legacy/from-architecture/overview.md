# Architecture Overview

## SoT vs Projection

- SoT（Source of Truth）：业务写入的真相源（权限/隔离/约束/事务），以 Postgres 为准。
- Projection：从 SoT 派生的“读模型”（例如 Search），通过 outbox + worker 异步更新，可 rebuild。

## 核心数据流（Search）

1) SoT 写入（Library/Bookshelf/Book/Block…）
2) 同事务写 `search_index`（Postgres projection）并 enqueue `search_outbox_events`
3) `search_outbox_worker` 消费 outbox，把文档写入 Elasticsearch
4) 读路径（API /search）从投影读取（受 feature flag 控制，可快速回退）

## SLO/SLA 建议（示例）

- 交互型 API（用户等）：关注 P95/P99
  - 例：GET /search：P95 < 2s，P99 < 10s
- 后台 worker/daemon（用户不直接等）：关注“投影新鲜度” + error rate
  - 例：99% 的事件在 30s 内投影完成（或按资源调到 5min）
