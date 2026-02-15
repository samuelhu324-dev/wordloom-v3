# Run-005：Labs-009 / 实验 A（ES 挂掉）成功跑通 SOP

目标：把 Labs-009 的实验 A（ES stop → 插入 delete outbox → worker retry → metrics/trace/logs 取证 → 落快照）整理成一份“可复用的一次成功操作清单”。

本 Runbook 只负责“怎么跑 + 怎么留证据”；实验背景、验收口径与故障复盘细节见：
- labs：`docs/architecture/runbook/labs/labs-009-observability-failure-drills.md`

---

## 1) 前置条件

- 已启动：Postgres + Jaeger + Elasticsearch（ES 在实验步骤里会被 stop/start）
- worker 与 Jaeger 的 tracing 已开启（建议实验期 `always_on`）
- 建议仅保留单个 worker 实例，避免 Jaeger/metrics 被多进程污染

### 1.1 端口与地址（默认）

- Jaeger UI：`http://localhost:16686`
- Jaeger API：`http://localhost:16686/api`
- OTLP/HTTP：`http://localhost:4318`
- ES：`http://localhost:9200`

---

## 2) 一次成功跑通（实验 A，ES down）

> 说明：以下步骤按“最后一次成功跑通”的顺序组织。
> 产物（快照）统一写入：
> `docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/`

### 2.1 启动/确认 infra（Jaeger + ES 等）

Windows（PowerShell）：

```powershell
docker compose -f docker-compose.infra.yml up -d
```

可选：确认 Jaeger services 列表能访问（用于后续导出快照）：

```powershell
(Invoke-RestMethod -Uri "http://localhost:16686/api/services" -Method Get) | ConvertTo-Json -Depth 5
```

### 2.2 准备环境变量（worker 与脚本共用）

Windows（PowerShell，示例值按你的环境调整）：

```powershell
$env:WORDLOOM_ENV = "test"
$env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test"

$env:WORDLOOM_TRACING_ENABLED = "1"
$env:OTEL_TRACES_SAMPLER = "always_on"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"

$env:ELASTIC_URL = "http://localhost:9200"
$env:ELASTIC_INDEX = "wordloom-test-search-index"

$env:OUTBOX_WORKER_ID = "w-labs009-expA"
$env:OUTBOX_METRICS_PORT = "9109"
$env:OUTBOX_HTTP_PORT = "9111"
```

### 2.3 停掉 ES（制造 transient 故障）

Windows（PowerShell）：

```powershell
docker compose -f docker-compose.infra.yml stop es
```

### 2.4 插入一条 delete outbox 事件（稳定触发一次 ES 调用）

Windows（PowerShell）：

```powershell
$env:OUTBOX_OP = "delete"
python .\backend\scripts\labs_009_insert_search_outbox_pending.py
```

脚本会打印/写入本次插入的 outbox_event_id（用于后续 Jaeger 精确查询）。

### 2.5 启动 search outbox worker（观察 retry/backoff）

Windows（PowerShell）：

```powershell
python .\backend\scripts\search_outbox_worker.py
```

观察点：
- 日志中应能看到 `Observability schema: labs-009-v2 (file=...)`
- ES down 时应出现 `reason=es_connect` 一类 retry 线索

### 2.6 抓取证据（metrics + logs + Jaeger 导出）

#### 2.6.1 抓 `/metrics`

Windows（PowerShell）：

```powershell
$ts = Get-Date -Format "yyyyMMddTHHmmss"
Invoke-WebRequest -UseBasicParsing "http://localhost:$env:OUTBOX_METRICS_PORT/metrics" |
  Select-Object -ExpandProperty Content |
  Out-File -Encoding utf8 "docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/metrics-$ts.txt"
```

#### 2.6.2 导出 Jaeger 快照（推荐用 WSL2 bash，避免 URL encode 坑）

WSL2（bash）：

```bash
SERVICE="wordloom-search-outbox-worker"
ts="$(date +%Y%m%dT%H%M%S)"

# services / operations 快照（用于确认 service 与 operation 名称）
curl -sS "http://localhost:16686/api/services" \
  -o "docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/jaeger-services-${ts}.json"

curl -sS "http://localhost:16686/api/services/${SERVICE}/operations" \
  -o "docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/jaeger-operations-${ts}.json"

# 1) 批处理概览：按 claim_batch_id 过滤（从日志里拿 claim_batch_id）
CLAIM_BATCH_ID="<paste-claim-batch-id>"
curl -sS \
  --data-urlencode "service=${SERVICE}" \
  --data-urlencode "lookback=1h" \
  --data-urlencode "limit=20" \
  --data-urlencode "operation=projection.process_batch" \
  --data-urlencode "tags={\"wordloom.claim_batch_id\":\"${CLAIM_BATCH_ID}\",\"wordloom.obs_schema\":\"labs-009-v2\"}" \
  "http://localhost:16686/api/traces" \
  -o "docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/jaeger-projection-by-claim_batch_id-${ts}.json"

# 2) 单条事件：按 outbox_event_id 过滤（从插入脚本输出/快照里拿 outbox_event_id）
OUTBOX_EVENT_ID="<paste-outbox-event-id>"
curl -sS \
  --data-urlencode "service=${SERVICE}" \
  --data-urlencode "lookback=1h" \
  --data-urlencode "limit=20" \
  --data-urlencode "operation=outbox.process" \
  --data-urlencode "tags={\"wordloom.outbox_event_id\":\"${OUTBOX_EVENT_ID}\",\"wordloom.obs_schema\":\"labs-009-v2\"}" \
  "http://localhost:16686/api/traces" \
  -o "docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/jaeger-by-event-outbox_event_id-${ts}.json"
```

#### 2.6.3 留存 worker 日志

建议把 worker stderr/stdout 重定向保存为快照（示例）：

Windows（PowerShell）：

```powershell
$ts = Get-Date -Format "yyyyMMddTHHmmss"
python .\backend\scripts\search_outbox_worker.py 2> "docs/architecture/runbook/labs/_snapshots/manual/_labs009_expA/worker-$ts.err.txt"
```

> 注意：该方式会让 worker 以前台方式运行且输出重定向；实验结束后可 Ctrl+C 退出。

### 2.7 恢复 ES

Windows（PowerShell）：

```powershell
docker compose -f docker-compose.infra.yml start es
```

---

## 3) 验收 checklist（实验 A）

- Metrics：能看到 retry 指标增长（典型 `reason=es_connect`）
- Tracing：
  - `projection.process_batch` 可用 `wordloom.claim_batch_id` + `wordloom.obs_schema=labs-009-v2` 命中
  - `outbox.process` 可用 `wordloom.outbox_event_id` + `wordloom.obs_schema=labs-009-v2` 命中
- Logs：
  - 启动行包含 schema marker（`labs-009-v2`）
  - 错误细节在 logs 中可用 `trace_id/span_id` 对齐 Jaeger

---

## 4) 其他实验预留（Labs-009）

> 这里只预留位置；具体触发方式与验收口径以 Labs-009 为准。

### 4.1 实验 B：ES 429（限流/背压）

TODO

### 4.2 实验 C：确定性 4xx（毒丸数据）

TODO

### 4.3 实验 D：部分成功（partial bulk success）

TODO

### 4.4 实验 E：DB 竞争/锁/死锁

TODO

### 4.5 实验 F：stuck & reclaim（租约过期回收）

TODO

### 4.6 实验 G：重复投递 / 幂等

TODO

### 4.7 实验 H：投影规则版本化风险（projection_version）

TODO
