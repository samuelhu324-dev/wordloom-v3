# backend/scripts

Status: draft

目标：把“新增脚本与常用入口”收敛到一个可治理的命令空间：分区（labs/ops/dev/migrations）+ 统一入口（cli.py）+ 统一输出（snapshots）。

## 硬规则（从今天起执行）

1) 新增脚本必须放在 `labs/ops/dev/migrations` 之一
2) `legacy/` 视为历史演进区：
   - 尽量不要新增新的“常用入口”到 legacy
   - 新入口通过 wrapper/路由复用 legacy（薄封装，不改老逻辑）
3) 输出（快照/导出/日志）必须写入统一输出根：
   - Labs 证据：`docs/labs/_snapshot/`
   - Runbook 证据：`docs/runbook/_snapshot/`
   - 每次运行创建独立 `run_id` 目录，避免“输出垃圾山”

## 分区说明

- `labs/`：失败演练、注入、导出证据（不可当生产工具）
- `ops/`：runbook/救火脚本（要求 dry-run/审计字段）
- `dev/`：开发机工具（start/stop/smoke/diag）
- `migrations/`：一次性/阶段性脚本（跑完冻结）
- `legacy/`：历史脚本与旧实现归档区（冻结为参考）

## 统一入口

- `cli.py`：最小路由器，把“怎么跑”固定下来。

示例：

- 导出 Jaeger（失败演练证据）：
  - `python backend/scripts/cli.py labs export-jaeger --service wordloom-search-outbox-worker --lookback 24h`

- 运行实验 B（ES 429 注入，样板入口）：
  - `python backend/scripts/cli.py labs expb-es429 --duration 30 --service wordloom-search-outbox-worker`

## 输出目录约定（_snapshot）

Labs 统一输出根：`docs/labs/_snapshot/`

- 实验输出（每次运行一个 run_id 目录）：`docs/labs/_snapshot/manual/_lab-S3A-2A-3A-expB/<run_id>/`
  - `_exports/`：Jaeger 导出 JSON
  - `_metrics/`：metrics 抓取/PromQL 结果
  - `_logs/`：worker 运行日志（stdout/stderr）
  - `_notes.md`：本次结论/是否通过/下一步
