# Log-S2C：Observability Triage（失败管理 / 故障演练）

Status: draft
links:
- Labs-008：shared keys 三件套对齐验收（Metrics / Tracing / Logs）
- Labs-009：经典失败场景菜单（可复现故障演练套件）
- docker-compose.infra.yml（prometheus/grafana profile）
- Grafana Dashboard：Wordloom • Outbox + ES Bulk（自动 provision）

## Background

系统长大后，“失败”不是异常而是常态：网络抖动、背压、毒丸数据、并发抢占、进程崩溃都会出现。
本日志的目标是把故障排障链路固定成一套可训练的肌肉记忆：从 metrics 缩小范围 → 用 tracing 定位步骤 → 用 structured logs 取细节证据。

## What/How to do

### 1) 统一失败语义与 shared keys（作为排障“钥匙”）

draft:
- 以 Labs-008 的 shared keys 为统一口径：在 metrics labels、trace attributes、logs 字段里共享同一组低基数 keys。
- 失败分类必须“可枚举”：metrics 的 `reason` 只能是低基数枚举（例如 `es_unreachable`、`rate_limited`、`mapping_conflict`、`db_contention`）。
- 关联键必须“可跳转”：logs 必须包含 `trace_id`/`span_id`；API 请求必须能用 `correlation_id` 作为 pivot 在 tracing 里定位 trace。
adopted:
-

### 2) 常态化面板观测（Prometheus + Grafana 接通）

draft:
- 启动监控栈（仅 infra，不启动 app）：
	- `docker compose -f docker-compose.infra.yml --profile monitoring up -d prometheus grafana`
- 若你修改过 `docker/prometheus/prometheus.yml`：执行一次 reload 使其生效：
	- `curl -X POST http://localhost:9090/-/reload`
- 确保应用侧 metrics 可被抓取（应用跑在宿主机，Prom 从容器侧抓 host）：
	- API：Windows 侧常用端口 `8000`（`run_api_win.py`），Prom 已配置抓取 `host.docker.internal:8000/metrics`
	- Worker：确保 `OUTBOX_METRICS_PORT` 落在 Prom 抓取端口之一（默认常见：`9108`/`9109`/`9110`；lab/演练常用：`9129`）
	- 验证：打开 `http://localhost:9090/targets`，`wordloom-*` job 应显示 `UP`
- 验证 Prometheus targets 正常：打开 `http://localhost:9090/targets`，应看到 `wordloom-*` job。
- 打开 Grafana：`http://localhost:3000`（admin/admin），在 `Wordloom` 文件夹下打开 `Wordloom • Outbox + ES Bulk`。
- 常态化观测最小面板关注：
	- Worker：`outbox_failed_total`、`outbox_retry_scheduled_total`、`outbox_processed_total`
	- ES Bulk：`outbox_es_bulk_requests_total`、`outbox_es_bulk_failed_requests_total`
- 面板排障路径（固定动作，不依赖“灵感”）：
	- 先用面板把范围缩小到 `env + projection + op + reason/result`
	- 再去 Jaeger 用同名 tags/operation（例如 `projection.process_batch`）过滤到 trace
	- 再用 trace_id 回到 jsonl 日志看细节（错误摘要/堆栈/实体 ID 等高基数信息）
adopted:
-

### 3) 失败观测演练（隔离为 Labs-009）

draft:
- 经典失败场景（ES down / 429 / 毒丸 4xx / partial / DB 竞争 / stuck&reclaim / 幂等重复 / 规则版本）已整理为 Labs-009。
- 本日志不再内嵌实验细节，避免把 runbook 写成“超长论文”；以 Labs-009 为唯一可执行入口。
adopted:
-

### 4) 失败后的收尾动作（定位 → 修复 → 复盘）

draft:
- 对 `result=failed` 的事件：明确处理策略（修复数据/修复映射/修复代码）并保留 replay 入口（人工或自动）。
- 对 `result=retry` 的事件：确保 backoff 与 max_attempts 可观测（attempt 递增、reason 收敛），避免“静默循环”。
- 对“tracing 缺失”的场景（例如进程崩溃）：以 metrics+logs 为主证据链，保证仍可复盘（这也是 Labs-009 的关键验收点之一）。
adopted:
-