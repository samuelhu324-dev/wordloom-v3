# Labs-008：Observability Shared Keys（Metrics / Tracing / Structured Logs 对齐验证）

Status: draft

目标：验证“截图1/实验2”关键链路在三件套里共享同一组可过滤的低基数字段（shared keys），并且可以从任意一个信号快速跳转到另一个信号。

- Metrics：用 labels 快速缩小范围（projection/op/reason/result）
- Tracing：用 span attributes 快速定位步骤（projection/op/batch_size/attempt/result + correlation_id）
- Structured Logs：用字段读细节，并能用同一组 keys 过滤（projection/op/batch_size/attempt/result + trace_id/span_id）

---

## 0) 前置条件

- Postgres / Elasticsearch 已启动（同 Labs-007）
- Jaeger 已启动并开启 OTLP/HTTP（端口 `4318`），UI `http://localhost:16686`
- 环境变量（示例）：

```powershell
$env:WORDLOOM_TRACING_ENABLED = "1"
# 若需要显式指定 OTLP 端点：
# $env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
```

---

## 1) Shared Keys 约定（本 lab 的验收口径）

### 1.1 低基数（必须在 metrics labels + trace attributes + logs 字段都能看到）

- `projection`（例如 `search_index_to_elastic` / `chronicle_events_to_entries`）
- `op`（例如 `upsert`/`delete`/`mixed`）
- `batch_size`
- `attempt`
- `result`（例如 `ok`/`failed`/`success`/`partial`）

### 1.2 关联键（允许形态不同，但必须能互相跳转）

- Logs ↔ Tracing：`trace_id`/`span_id`（日志自动注入）
- correlation_id → Tracing：`correlation_id`（作为 HTTP server span tag，可用 Jaeger tag 过滤找到 trace）

说明：metrics labels 避免高基数（不要把 `entity_id`、`book_id` 等塞到 label）。高基数信息可以保留在 tracing/logs。

---

## 2) 执行步骤（以实验2为主）

### 2.1 启动 API + 单 worker（避免多 worker 抢占导致 trace 分裂）

- API：按 run-004 / labs-007 的方式启动
- 仅启动 1 个 worker（search 或 chronicle 二选一即可）：

```powershell
# search worker
python backend/scripts/search_outbox_worker.py

# 或 chronicle worker
# python backend/scripts/chronicle_outbox_worker.py
```

#### WSL2 备注（如果你在 WSL2 里跑）

在本仓库结构下，WSL2 里直接用 `backend.api.app.main:app` 往往会失败（因为 `backend/` 不是 Python package）。
推荐做法：把 `backend/` 加到 `PYTHONPATH`，然后用 `api.app.main:app` 启动。

另外，如果 Windows 侧已经有进程占用了 `8000`，WSL2 绑定 `8000` 会直接报错；这种情况下改用 `8001`（并把后续 curl/Invoke 请求也改端口）。

WSL2（bash）启动示例：

```bash
cd /mnt/d/Project/wordloom-v3

export PYTHONPATH="/mnt/d/Project/wordloom-v3/backend"
export WORDLOOM_ENV=test
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export WORDLOOM_TRACING_ENABLED=1
export OTEL_TRACES_SAMPLER=always_on
export OTEL_EXPORTER_OTLP_ENDPOINT='http://localhost:4318'

# 若 8000 被占用，改成 8001
python3 -m uvicorn api.app.main:app --host 0.0.0.0 --port 8001
```

WSL2 检查端口是否被占用：

```bash
ss -ltnp | grep ':8000' || true
```

### 2.2 触发一个可复现的 outbox 批次

- 复用 Labs-007 的“确定性 pending outbox row”方式（或通过 API 触发业务事件）

---

## 3) 证据采集与核对

### 3.1 Metrics：核对 labels 是否包含 shared keys

目标：能从 metrics 看到投影维度与结果维度，并用它缩小范围。

- 关注指标（示例）：
  - `outbox_processed_total{projection="...",op="..."}`
  - `outbox_failed_total{projection="...",op="...",reason="..."}`
  - `outbox_retry_scheduled_total{projection="...",op="...",reason="..."}`

验收：至少能用 `projection/op/reason` 把问题定位到“哪个 worker + 哪类操作/原因”。

### 3.2 Tracing：核对 span attributes 是否包含 shared keys + correlation_id

目标：在 Jaeger 里用 operation 过滤（例如 `projection.process_batch`），并确认 tags 存在。

- 用脚本导出/验证（复用 Labs-007 脚本）：

```powershell
python backend/scripts/_labs_007_exp2_export_validate_jaeger.py --operation projection.process_batch
```

验收：在 `projection.process_batch` span 的 tags 里能看到：
- `projection` / `wordloom.projection`
- `op` / `batch_size` / `attempt` / `result`

加验收（API 侧）：任意 HTTP server span 或其同 trace 内的 span 可通过 tag 查到：
- `correlation_id`（或 `wordloom.correlation_id`）

### 3.3 Logs：核对结构化字段是否包含 shared keys + trace_id/span_id

目标：worker 在关键点输出结构化 log，字段与 tracing/metrics 对齐。

验收：worker 日志中至少出现：
- `event=outbox.claim_batch`（包含 `projection/worker_id/batch_size/claimed`）
- `event=projection.process_batch`（包含 `projection/op/batch_size/attempt/result`）
- 同时具备 `trace_id`/`span_id`（tracing enabled 时自动注入）

---

## 4) DoD（完成判定）

- 能从 metrics 选择一个异常维度（projection/op/reason），并在 tracing 中用同名字段过滤到对应 trace
- tracing 中能用 `correlation_id` tag（API 请求）定位到 trace（用于取证/审计链路）
- logs 中能用相同字段过滤到 batch 级事件，并通过 `trace_id` 跳转到 Jaeger

---

## 5) 快照留存（可选）

沿用 Labs-007 的快照治理：仅保留最小证据集（validator 输出 + 关键 trace 导出）。

### 5.1 Golden fixtures（建议保留的最小集合）

命名建议（示例）：`labs-008-<scope>-<yyyyMMdd-HHmmss>.<ext>`，其中 scope 取：`api`/`worker-search`/`worker-chronicle`/`jaeger`/`validator`。

建议最小保留集（够复核即可；其余归档到 `_archive/`）：

- 1) validator 结果（证明 span/tags 通过验收）
  - `labs-008-validator-<ts>.json` 或脚本输出文件（若脚本当前输出为 jsonl/txt，则按实际保存）
- 2) Jaeger trace 导出（证明 trace 树存在且可过滤）
  - `labs-008-jaeger-trace-<ts>.json`
- 3) worker 日志截样（证明 logs 结构化字段与 shared keys 对齐，并含 trace_id/span_id）
  - `labs-008-worker-search-<ts>.jsonl`（或 `labs-008-worker-chronicle-<ts>.jsonl`）
- 4) API 日志截样（证明 correlation_id 存在并可 pivot；以及 trace_id/span_id 注入）
  - `labs-008-api-<ts>.jsonl`

注：metrics 一般不做“快照文件”留存；若确需证据，可保存一次 `/metrics` 抓取结果：`labs-008-metrics-<ts>.txt`。
