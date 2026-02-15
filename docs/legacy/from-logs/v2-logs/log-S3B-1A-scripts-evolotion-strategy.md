# Log-S3B-1A：脚本演进策略（入口稳定、实现可迁移）

Status: draft
links:
- S3B（治理总纲）：`docs/logs/v2-logs/log-S3B-scripts-snapshots-management.md`
- v2 统一入口（现状落地）：`backend/scripts/v2-scripts/cli.py`
- v2 围栏规则：`backend/scripts/v2-scripts/README.md`

## Background

脚本整理时最常见的“工程级担忧”是：一搬家路径就变，所有旧命令/笔记/CI 全炸；未来还有 v3/v4，难道每次都要大迁徙？

成熟团队的解法不是“永远不搬家”，而是：**入口稳定（对外 API）**、**实现可迁移（内部实现）**。

核心原则：把“路径/文件名”当内部实现；把“命令/入口”当对外 API。API 必须稳定。

## What/How to do

### 1) 不让人直接跑脚本文件：建立稳定入口层

draft:
- 把 `python path/to/script.py` 视为“内部实现直连”，不要把它当长期 API。
- 对外只暴露稳定入口（统一 CLI/命令空间），例如：
	- `python backend/scripts/v2-scripts/cli.py <namespace> <command> ...`
- 好处：以后脚本内部怎么拆、怎么换文件、怎么 v3/v4，入口不变。

adopted:

### 2) 演进区（v1/v2）允许存在，但要有兼容层（shim/wrapper）

draft:
- 允许保留 v1（历史演进区）与 v2（新规范区），但必须解决“旧入口不失效”。
- 两种兼容方式：
	- A) 转发脚本（forwarding stub）：旧路径保留同名文件，只负责 import/调用新实现。
	- B) 统一 CLI：旧入口变成 CLI 的别名（运行时提示 deprecated，并转发到新命令）。
- 迁移手法要点：旧入口尽量保持可跑，减少“迁移冲击波”。

adopted:

### 3) 长期组织不要以“版本目录”为中心：按风险/生命周期分区更稳定

draft:
- “v1/v2/v3”不是你真正关心的维度；更稳定的维度是：
	- 这是 ops 还是 labs？能不能在 prod 跑？是否需要 dry-run？是否要审计？是否有生命周期？
- 因此长期推荐：按 `ops/labs/dev/migrations` 分区；版本作为元数据（脚本头部/注册表），而非目录结构的主轴。

adopted:

### 4) 让迁移变成“改一行映射”：引入命令注册表（registry）+ 路由

draft:
- 建立 command registry：入口命令固定，实现位置由映射决定。
- 效果：实现文件换位置/拆分时，只改 registry 的一行映射，用户命令不变。
- 类比：URL 路由不变，handler 可替换。

adopted:

### 5) 渐进迁移（freeze + wrap + migrate-by-touch）：避免大迁徙

draft:
- Step 1：冻结旧目录（不再新增）；旧脚本仅修 bug。
- Step 2：给旧脚本加“壳”（shim）：挑常用/危险脚本优先接入新入口。
- Step 3：按价值迁移：每次“碰到要改”就迁一小块，并在旧位置保留 wrapper。
- 预期结果：旧目录自然萎缩，不需要一次性重构。

adopted:

### 6) 把入口当 API：建立弃用策略（deprecation policy）

draft:
- 旧入口保留一段时间（例如 3~6 个月或直到不再依赖旧笔记）。
- 运行时打印 warning（含新命令）。
- 文档/README 全部更新为新命令。
- 最后再删除旧入口。

adopted:

### 7) 最小 MVP（公司味但不复杂）：稳定入口 + 少量 shim + 逐步演进

draft:
- 稳定入口：一个统一 CLI（v2-scripts 的 `cli.py`）
- 兼容层：旧位置保留 3~5 个常用脚本 wrapper（不影响旧命令）
- 迁移纪律：新需求只进 v2 分区；v1 只做修复

adopted: