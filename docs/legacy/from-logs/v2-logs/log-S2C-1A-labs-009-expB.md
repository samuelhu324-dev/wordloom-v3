# Log-S2C-1A：Labs-009 / 实验 B（ES 429）触发策略对比与验收建议

Status: draft
links:
- Labs-009：`docs/architecture/runbook/labs/labs-009-observability-failure-drills.md`
- infra：`docker-compose.infra.yml`（含 Jaeger；Prometheus+Grafana 用 `--profile monitoring`）
- Grafana Dashboard：`Wordloom • Outbox + ES Bulk`（自动 provision）

## Background

实验 B 的核心不是“如何让 ES 一定返回 429”，而是验证：429 是否被正确分类为可恢复错误（`retry/backoff`）、`reason` 是否保持低基数（例如 `rate_limited`），以及 metrics → trace → logs 的证据链是否在压力/抖动下仍然可用。
当前仓库的 Prometheus + Grafana + Jaeger 已经是配套形态（infra compose 可直接拉起），因此本日志只讨论“触发策略与验收口径”，不再假设你缺监控组件。

## What/How to do

### 1) 触发模式 A：压测逼出 429（系统外侧触发）

draft:
- 本质：通过提高 batch_size/并发，或降低 ES 资源，把系统推到背压点，观察 ES 产生 429 的真实时空分布。
- 最擅长验证：
	- retry/backoff+jitter 是否真的“在降压”（而不是更快把系统打爆）。
	- 指标/日志/trace 在高压下是否仍可用（采样/爆量时是否变成噪声）。
	- 你的 batch_size、并发、sleep/backoff 参数是否合理。
- 不擅长验证：
	- 复现稳定性（今天出 429，明天可能不出）。
	- 精确分类断言（容易夹杂 timeout、5xx、连接池耗尽等多种失败）。
- 关键提醒（避免“测空气”）：
	- 若出现大量 `claimed=0`、一直空转，通常不是 ES 变强了，而是 outbox 没货/被别的 worker claim 走/claim 策略拿不到锁。
	- 压测前先保证“稳定供给”的 outbox 事件（否则压测只是在测空转路径）。

adopted:

### 2) 触发模式 B：可控注入 429（系统内侧触发，fault-injection）

draft:
- 本质：在 ES adapter 层加可控开关（按比例/按 op/按节奏）注入 429，让实验输出更干净、断言更严格。
- 最擅长验证（强信号、10 分钟级别完成）：
	- 错误分类逻辑是否正确：429 必须 → transient/retry；确定性 4xx 必须 → failed。
	- `reason=rate_limited` 的低基数设计是否落地（不会把具体错误串塞到 metrics label）。
	- tracing 的 `result=retry` 是否由“聚合器/父 span”正确写回（避免子 span error 但 batch ok）。
	- failed/DLQ 的落库行为是否正确（429 不应该直接进入 failed）。
- 不擅长验证：
	- 在真实资源紧张下系统是否能回稳（因为它不制造真实 CPU/IO/队列竞争）。

- 建议落点（本仓库当前实现）：
	- Search worker 的 ES “adapter”目前就在 worker 脚本内部：`backend/scripts/search_outbox_worker.py`。
	- 非 bulk 路径：单事件处理在 `_process_one(...)` 内部调用 `_process_upsert(...)` / `_process_delete(...)`。
	- 因此最稳的注入点是：在 `_process_one` 调用 `_process_upsert/_process_delete` 之前，根据 env 开关直接抛出一个 `httpx.HTTPStatusError(429)`。
	- 这样能复用既有的失败分类与 retry/backoff 逻辑，并且 metrics/traces/logs 都会自然产生“可验收信号”。

- 建议开关（示例）：
	- `OUTBOX_EXPERIMENT_ES_429_RATIO=0.3`（按比例注入）
	- 或 `OUTBOX_EXPERIMENT_ES_429_EVERY_N=3`（每 N 次注入一次，便于稳定复现）
	- `OUTBOX_EXPERIMENT_ES_429_OPS=upsert,delete`（只对指定 op 注入；留空表示对所有 op 生效）
	- `OUTBOX_EXPERIMENT_ES_429_SEED=1`（可选：固定随机种子，便于复现实验）

- reason 命名提醒（避免文档/查询口径漂移）：
	- 当前 worker 对 429 的低基数 reason 为 `es_429`（可视为 “rate_limited” 的实现名）。
	- 验收时关注“低基数 + 可枚举”这件事本身；若后续要把 `es_429` 重命名为 `rate_limited`，应走一次全链路口径同步。

adopted:

### 3) 推荐执行顺序（不需要“都测到死”）

draft:
- 第一阶段（必做）：先跑 fault-injection 版。
	- 目的：把“分类 + shared keys 三件套对齐 + result 聚合写回”校准到稳定。
- 第二阶段（推荐做一次即可）：再跑一次轻量压测版（2~5 分钟）。
	- 目的：确认在真实抖动/资源紧张下 backoff/jitter 真的能降压回稳。
- 若你还在修 shared keys / result 汇总等“链路对齐问题”，优先只做 fault-injection：压测会把噪声放大，相当于在暴风雨里找针。

adopted:

### 4) 最小验收组合（证据链闭环）

draft:
- 注入 429：固定比例（例如 30%）+ 固定 op（例如 bulk item）。
- Metrics 断言：`outbox_retry_scheduled_total{reason="rate_limited"}` 增长（并且维度只用低基数 keys）。
- Tracing 断言：`projection.process_batch` / `outbox.process` 能看到 `result=retry`，并用相同 shared keys 定位到代表性 trace。
- Logs 断言：结构化日志记录 429 细节（status code、响应摘要等高信息内容），同时 `reason=rate_limited` 与 tracing/metrics 对齐。

adopted: