---
kind: stub
status: archived
moved_from: docs/legacy/from-logs/v2-logs/log-S3B-scripts-snapshots-management.md
moved_to: docs/logs/log-S3B-2A-scripts-snapshots-management.md
moved_at: 2026-02-13
links:
  issue: 43
---

# ⚠️ This file moved

This document has been moved to:

➡️ **docs/logs/log-S3B-2A-scripts-snapshots-management.md**

Reason: migrate the log to the new front-matter based format and align with the current `backend/scripts/` layout (taxonomy + cutover + stub policy).

> Note: This stub is kept to preserve old links. Do not edit here.

adopted:

- 已采用 v1/v2 快照演进区：
  - 旧快照：`docs/architecture/runbook/labs/v1_snapshots/`
  - 新快照：`docs/architecture/runbook/labs/v2_snapshots/`
- 已创建 Labs-009 ExpB 输出根：`docs/architecture/runbook/labs/v2_snapshots/manual/_labs009_expB/`
- v2 样板输出结构（每次运行一个 run_id 目录）：
  - `_exports/`（Jaeger 导出）
  - `_logs/`（worker 日志）
  - `_metrics/`（预留：metrics 抓取/PromQL）
  - `_notes.md`（结论模板）

### 7) 眼下最小落地（不动老系统，立刻见效）

draft:
- 目标：不“一次性重构”，但从今天开始“新增不再散落”。
- 建议 3 个小而硬动作：
  - 1) 新增 `backend/scripts/legacy/` 并把现有脚本搬进去（先搬家，不改逻辑）。
  - 2) 新增 `backend/scripts/ops/`、`backend/scripts/labs/`、`backend/scripts/dev/`、`backend/scripts/migrations/` + README（先建空目录/规则）。
  - 3) 选 3 个最常用/最危险脚本做入口封装（薄封装），强制统一命令与输出规则。

adopted:

- 已按“先止血再演进”落地样板（Labs-009 ExpB）：
  - v2 统一入口：`backend/scripts/v2-scripts/cli.py`
  - v2 薄封装脚本：
    - `backend/scripts/v2-scripts/labs/run_labs009_expb_es429.py`
    - `backend/scripts/v2-scripts/labs/export_jaeger.py`
  - 复用的 v1 实现：
    - `backend/scripts/v1-scripts/search_outbox_worker.py`
    - `backend/scripts/v1-scripts/labs_009_export_jaeger.py`