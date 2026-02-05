# Run-003：Outbox worker 失败管理（模板 / 待填充）

> 说明：本 runbook 是“模板占位”。
> 等 labs-004 的 v1–v4 实验全部跑通并写出结论后，再把本文件从“模板”升级为“可执行 SOP”。
>
> 对应实验：`docs/architecture/runbook/labs/labs-004-worker-failure-management-v1-v4.md`

---

## 1) 目的与范围

- 目标：把 outbox worker 的失败处理做成可运营、可审计、可告警。
- 范围：`search_index_to_elastic` 投影 outbox worker（未来可扩展到其他投影）。
- 不在范围：业务层数据一致性规则、ES mapping 设计（由 run-002 管）。

---

## 2) 依赖与前置条件

- Postgres（dev/test）
- Elasticsearch
- API（产生 outbox）
- Outbox worker（脚本入口）
- Prometheus + Grafana（可选但推荐）

参考：`docs/ENVIRONMENTS.md`

---

## 3) 关键定义（必须统一口径）

- **pending**：等待处理；可能有 `next_retry_at`。
- **processing**：已被某 worker claim；应当带 lease / processing_started_at。
- **failed（终态）**：不会自动复活；只能通过显式 replay 回到 pending。
- **stuck**：processing 且 lease 过期或处理超时（max_processing_seconds）。

---

## 4) 启动与停止

### 4.1 启动顺序

1) DB
2) ES
3) API（可选，但通常需要）
4) worker
5) Prom/Grafana（可选）

### 4.2 worker 启动命令（TODO：按真实入口补齐）

- TODO：WSL2/Bash 启动示例
- TODO：Windows/PowerShell 启动示例（如果支持）

### 4.3 停止与重启策略（v4 TODO）

- TODO：SIGTERM graceful shutdown
- TODO：滚动重启策略

---

## 5) 配置项（运维口径）

> TODO：以“稳定默认值 + 可调范围 + 调参风险”形式补齐。

- 处理并发：`OUTBOX_CONCURRENCY`
- 批大小：`OUTBOX_BULK_SIZE`
- 轮询：`OUTBOX_POLL_INTERVAL_SECONDS`
- lease：`OUTBOX_LEASE_SECONDS`
- reclaim：`OUTBOX_RECLAIM_INTERVAL_SECONDS`
- 处理超时：`OUTBOX_MAX_PROCESSING_SECONDS`
- 重试：`OUTBOX_MAX_ATTEMPTS`, `OUTBOX_BASE_BACKOFF_SECONDS`, `OUTBOX_MAX_BACKOFF_SECONDS`

---

## 6) 观测与告警（TODO：实验后填写阈值）

### 6.1 必看指标

- `outbox_lag_events`
- `outbox_oldest_age_seconds`
- `outbox_inflight_events`
- `outbox_stuck_processing_events`
- `outbox_retry_scheduled_total`
- `outbox_terminal_failed_total`

### 6.2 推荐告警（占位）

- TODO：oldest_age 超过 SLA
- TODO：stuck_processing_events > 0 且持续 N 分钟
- TODO：terminal_failed_total 突增（按 reason 维度定位）

---

## 7) 常见故障处理（SOP 占位）

### 7.1 ES 不可用 / 网络故障

- 预期行为：retry 收敛（pending + next_retry_at），不会无限刷。
- 操作：
  - TODO：确认 ES 状态
  - TODO：确认 retry 指标形状
  - TODO：根因解除后观察 backlog 回落

### 7.2 确定性错误（坏 payload / mapping 冲突 / 4xx）

- 预期行为：进入 failed（终态），记录 `error_reason` 与 `error`。
- 操作：
  - TODO：按 reason 聚合统计
  - TODO：定位根因（坏数据 vs 代码 bug vs mapping）
  - TODO：修复根因后做 replay（见 8）

### 7.3 stuck（processing 长时间不动）

- 预期行为：reclaim 自愈。
- 操作：
  - TODO：确认 lease/max_processing 配置
  - TODO：确认 reclaim 日志与 stuck 指标回落

---

## 8) 失败终态与 replay（可审计）

> 注意：failed 是终态，不会自动复活。

### 8.1 replay 操作（TODO：补齐你最终认可的命令）

- dry-run：
  - TODO
- 执行：
  - TODO

### 8.2 replay 审计要求

- 记录：who/when/reason
- 留痕：replay_count 递增

---

## 9) 变更与回归验证

- 回归入口：跑一遍 labs-004 的 v1–v4。
- TODO：补 CI 或一键 smoke 脚本（可选）。

---

## 10) 附录：常用 SQL（TODO：从 labs-004 提炼最终版）

- TODO：状态分布
- TODO：stuck 统计
- TODO：failed 统计（按 error_reason 聚合）
