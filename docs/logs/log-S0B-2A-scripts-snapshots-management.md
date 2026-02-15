# Log-S0B/2A：tools/scripts & snapshots management

---

**id**: `S0B-2A`
**kind**: `log`               # log | lab | runbook | adr | note
**title**: `tools/scripts & snapshots management`
**status**: `draft`          # draft | stable | archived
**scope**: `S0B`
**tags**: `EVOLUTION, Docs, Observability, sub/1`
**links**: ``
  **issue**: `#43, #44`
  **pr**: ``
  **adr**: ``
  **runbook**: ``
**created**: `2026-02-13`
**updated**: `2026-02-13`

---

## Background

在清理 `backend/scripts/` 与实验输出的过程中，一个核心问题会反复出现：legacy 资产会自然堆积，而“新增脚本 + 新输出”如果没有围栏与统一入口，会快速回到脚本沼泽与 snapshots 垃圾山。
因此这份 log 的目标不是重构全部历史，而是建立可持续的治理外骨骼：分区（按物种）+ 统一入口（命令空间）+ 统一输出根（证据区）+ cutover 规则（从某个编号开始执行）+ stub（保留旧链接）。
整体编号/管理体系与 [docs/logs/log-S4B-3A-unified-indices-legacy taxonomy -front matter.md](docs/logs/log-S4B-3A-unified-indices-legacy%20taxonomy%20-%20front%20matter.md) 保持一致：交付与内容用稳定编号表达，时间顺序放到 Git Project/Issue，机械可管理字段放到 front matter。

## What/How to do

1) Directory taxonomy（脚本“物种”分区）

**draft**:

- 以风险与生命周期做分区，而不是以作者/文件名记忆：
  - `backend/scripts/ops/`：runbook/救火工具（可审计、默认 dry-run、可重复执行）
  - `backend/scripts/labs/`：失败演练/注入/导出证据（强调可复现与证据产出，不作为生产工具）
  - `backend/scripts/migrations/`：一次性/阶段性迁移与修复（跑完冻结，跟 milestone 归档）
  - `backend/scripts/dev/`：开发机效率脚本（本地 start/stop/smoke/diag）
  - `backend/scripts/legacy/`：历史脚本与临时探针的围栏区（冻结为参考，避免继续增长）
- 规则：新增脚本只能落在 `ops/labs/migrations/dev`；无法归类的临时探针先进入 `legacy` 并设定自然死亡策略。

**stable**:

- 已在仓库落地脚本分区（截图1）：`backend/scripts/{ops,labs,migrations,dev,legacy}`。

**archived**:

2) Stable entrypoint（统一入口：命令空间，而非文件名）

**draft**:

- 统一入口用一个轻量路由器承载，避免“记文件名/找脚本”成本：`backend/scripts/cli.py`。
- 入口的职责：
  - 固定“怎么跑”的参数契约（避免每个脚本自己发明参数风格）
  - 提供一致的默认安全开关（例如 ops 默认 dry-run）
  - 强制输出落点一致（见 3）
- 兼容策略：允许入口在必要时调用 `legacy/` 中的旧逻辑，但入口本身必须稳定、可复用、可审计。

**stable**:

- 已落地统一入口：`backend/scripts/cli.py`（命令空间稳定，不再依赖记文件名）。
- legacy 复用落点统一：旧实现集中在 `backend/scripts/legacy/`，入口通过调用 legacy 来保持演进安全。

**archived**:

3) Snapshots policy（统一输出根 + 可审计的证据区）

**draft**:

- 输出的目标不是“留一堆文件”，而是形成可回放/可验收的证据包：日志、导出、指标、结论。
- 建议统一输出根（与 `backend/scripts/README.md` 保持一致）：
  - Labs：`docs/labs/_snapshot/`
  - Runbook：`docs/runbook/_snapshot/`
  - 说明：两者都用于“证据包”落点；差别仅在语义归档（lab=演练证据，runbook=操作/救火证据）。
- 每次运行一个文件夹（示例）：
  - `<run_id>/`
    - `_exports/`（例如 Jaeger 导出）
    - `_logs/`（stdout/stderr 或结构化日志）
    - `_metrics/`（PromQL/metrics 抓取结果，避免手抄）
    - `_notes.md`（验收清单 + 结论 + 下一步）
- 保留策略（原则）：
  - labs 输出：保留最近 N 次（或按 milestone 归档）
  - ops/migrations：按审计价值与交付节点归档

**stable**:

- 已创建快照根目录（截图2/3）：
  - `docs/labs/_snapshot/`
  - `docs/runbook/_snapshot/`
- 已将脚本默认输出根对齐到 `docs/labs/_snapshot/`：`backend/scripts/cli.py` 与 `backend/scripts/labs/*.py`。

**archived**:

4) Legacy taxonomy + Cutover（不删历史，但从某个点开始“新体系执行”）

**draft**:

- Legacy 原则：不轻易删除；优先“归类 + 指路 + 冻结”，按需迁移。
- Cutover 规则：从 `S3B-2A` 起，新增内容必须遵循：分区 + 统一入口 + 统一输出根；旧内容默认只读参考。
- 迁移触发条件：只有当某段 legacy 仍高频使用/高风险/阻塞交付时，才迁移到新分区，并在旧位置留下 stub。

**stable**:

- 已执行 cutover：从 `S3B-2A` 起，新增治理文档与入口按 front matter + 统一目录规则落地。
- legacy 内容保留但冻结：旧文档与旧脚本通过 stub/入口保留引用，不再作为正文/入口继续扩写。

**archived**:

5) Stub policy（保留旧链接，不让搬家炸链）

**draft**:

- 对外部引用（Issue/PR/Chat/Runbook）而言，最重要的是“旧链接仍能找到新位置”。
- Stub 的写法与规范参考 [docs/STUB.md](docs/STUB.md)：
  - 在旧文件位置保留一个 `kind: stub` 的归档文档
  - 写清 `moved_from/moved_to/moved_at` 与关联 `links.issue/pr`
  - 明确告知“不要在 stub 上继续编辑”
- 本文对应的 legacy stub 位置：
  - `docs/legacy/from-logs/v2-logs/log-S3B-scripts-snapshots-management.md`

**stable**:

- 已把旧 log-S3B 文档改为 stub，并指向新 log：
  - from：`docs/legacy/from-logs/v2-logs/log-S3B-scripts-snapshots-management.md`
  - to：`docs/logs/log-S3B-2A-scripts-snapshots-management.md`
- 已把旧 Labs-009 文档改为 stub，并迁移为新编号 lab（同时保留实验 A 的历史结论与快照清单）：
  - from：`docs/legacy/from-labs/labs-009-observability-failure-drills.md`
  - to：`docs/labs/lab-S3A-2A-3A-observability-failure-drills.md`

**archived**:
