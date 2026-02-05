# Module: Chronicle (SoT + Projection)

本文是 Labs-005（Chronicle Projection）在工程侧的统一说明与 Phase B 事件目录（Event Catalog）。

核心原则：

- `chronicle_events` 记录稳定、可审计的底层事实（facts）。
- Timeline/Score breakdown 是投影（projection），不应直接等同于 events 本身。
- 投影规则可版本化演进；facts 尽量长期稳定。

---

## 数据流（闭环）

- **SoT**: `chronicle_events`
	- 最小事件源，允许历史数据不完整（例如旧数据没有 actor/request 链路）。
- **Outbox**: `chronicle_outbox_events`
	- 每写入一条 `chronicle_events`，同事务 enqueue 一条 outbox（worker 异步投影）。
- **Projection**: `chronicle_entries`
	- worker/rebuild 将 `chronicle_events` 物化为 UI 友好结构（summary、聚合字段等）。

> 注意：Phase C 才考虑把部分 payload 字段“提升为列 + 索引”。Phase B 先确保语义稳定与覆盖面。

---

## 事件信封（payload envelope）

为了避免立刻改表（`chronicle_events` 是 minimal schema），审计/串联字段统一放在 `payload` 顶层：

- `schema_version`: number（当前为 1）
- `provenance`: `live | backfill`（历史回填写 `backfill`）
- `source`: 事件来源（例如 `api`）
- `actor_kind`: `user | system | unknown`
- `correlation_id`: 请求链路 ID（HTTP 的 `X-Request-Id`）
- `http`: `{ route, method }`（可选）

这些字段由 Chronicle Recorder 自动注入（调用方不必每次手填）。

---

## Phase B：事件目录（Event Catalog）

### 1) 稳定 facts（后端 ChronicleEventType）

本阶段的目标不是“把所有 UI 文案做成事件”，而是补齐能长期维护的事实：

- **Book**
	- `book_created`: 创建书
	- `book_renamed`: 书名变更（payload: `{from,to}`）
	- `book_updated`: 书元数据变更（payload: `{fields:{...}, trigger?}`；建议只记录变更字段名，不塞大文本）
	- `book_viewed`: 查看书（访问/浏览；payload 可选 `{view_source}`）
	- `book_opened`: 打开书（进入编辑/阅读内容；建议用于 visits 统计）
	- `cover_changed`: 封面变更（payload: `{from_icon?,to_icon?,media_id?,trigger?}`）
	- `book_maturity_recomputed`: 成熟度重算（系统事件；payload 至少包含 `trigger`，并依赖 `correlation_id` 串联触发链路）

- **Block**
	- `block_created`: 新建块（payload: `{block_type?}`）
	- `block_updated`: 编辑块内容/元数据（payload: `{fields:{changed:[...]}}`）
	- `block_type_changed`: 块类型变更（payload: `{from,to}`）
	- `block_soft_deleted`: 软删除块
	- `block_restored`: 恢复块

- **Tag**
	- `tag_added_to_book`: 给书加标签（payload: `{tag_id}`）
	- `tag_removed_from_book`: 给书移除标签（payload: `{tag_id}`）

- **Todo**
	- `todo_promoted_from_block`: 从块内 TODO 提升（payload: `{todo_id,text,is_urgent?}`；block_id 绑定到 event.block_id）
	- `todo_completed`: TODO 完成（payload: `{todo_id,text,promoted?}`；block_id 绑定到 event.block_id）

> 说明：facts 的粒度以“可解释 + 可审计 + 可推导 UI 投影”为准。

---

### 2) Timeline（投影）→ facts 映射

前端 Timeline 只是展示层。每个条目应能对应到某个稳定 fact（或少数 system 事件）。

#### Timeline 事件（UI 文案 → event_type）

- `Book created` → `book_created`
- `Book renamed` → `book_renamed`
- `Book updated` → `book_updated`
- `Cover updated` → `cover_changed`
- `Block created` → `block_created`
- `Block updated` → `block_updated`
- `Block deleted` → `block_soft_deleted`
- `Block restored` → `block_restored`
- `Block type updated` → `block_type_changed`
- `Tag added` → `tag_added_to_book`
- `Tag removed` → `tag_removed_from_book`
- `Maturity recomputed` → `book_maturity_recomputed`（系统事件，允许保留，但要求能追溯触发来源：`trigger + correlation_id`）

> 其它已有 Timeline 类型（book_moved/structure_task_*/todo_* 等）依旧保留；Phase B 的重点是让「编辑/标签/块结构」这些主链路能从后端 facts 读出来。

---

### 3) Score breakdown（投影）→ facts 映射

Score breakdown 的 card/因子来自成熟度计算结果（投影/算法层），不应直接等于 events。

我们要做的是：给每个因子标注它依赖的稳定 facts（最少集合），方便长期维护/审计。

#### 结构（Structure）

- `structure_title`（Title completed）
	- 依赖 facts：`book_renamed` / `book_updated(fields.changed includes title)`
- `structure_summary`（Summary meets target）
	- 依赖 facts：`book_updated(fields.changed includes summary)`
- `structure_tags`（Tags configured）
	- 依赖 facts：`tag_added_to_book` / `tag_removed_from_book`
- `structure_cover`（Cover customized）
	- 依赖 facts：`cover_changed`（或 `book_updated` 的 cover 字段变更作为补充）
- `structure_blocks`（Block milestones）
	- 依赖 facts：`block_created` / `block_soft_deleted` / `block_restored` / `block_type_changed`

#### 活动（Activity）

- `activity_recent_edit`（Recent edits）
	- 依赖 facts：`block_updated` / `book_updated`
- `activity_visits`（Visit frequency）
	- 依赖 facts：`book_opened` / `book_viewed`（如缺失，可先以 `book_opened` 为准）
- `activity_todo_health`（Todo hygiene）
	- 依赖 facts：`todo_promoted_from_block` / `todo_completed`

#### 质量（Quality）

- `quality_block_variety`（Block variety）
	- 依赖 facts：`block_created` / `block_type_changed`（更好的做法是周期性 `content_snapshot_taken` 提供 type 计数）
- `quality_outline_depth`（Outline depth）
	- 依赖 facts：`block_created` / `block_soft_deleted` / `block_restored`（或 `content_snapshot_taken` 提供 block_count）

#### 任务（Task）

- `task_long_summary` / `task_tag_landscape` / `task_outline_depth` / `task_todo_zero`
	- 依赖 facts：
		- 触发/评估：`book_maturity_recomputed`（系统事件）
		- 完成/回退：`structure_task_completed` / `structure_task_regressed`

---

## Phase B 落地点（当前已接入的写入位置）

这部分是为了排障：知道“事实事件在哪里写进去”。

- Block
	- create: Block Router 成功创建后写 `block_created`
	- update: Block Router 成功更新后写 `block_updated`
	- delete: Block Router 软删除后写 `block_soft_deleted`
	- restore: Block Router 恢复后写 `block_restored`
	- Phase0 的 block update/type/delete/restore 同样补齐了 Chronicle 记录（用于 legacy 路径）
	- TODO facts：当 todo_list 块内容发生变化时，通过 diff 生成 `todo_promoted_from_block` / `todo_completed`

- Tag
	- associate/disassociate（BOOK）：在 Tag adapters 写 `tag_added_to_book` / `tag_removed_from_book`（覆盖路由调用与内部 tag_sync）

- Book
	- PATCH update: Book Router 写 `book_updated`，并在 cover 字段变化时写 `cover_changed`
	- upload cover: Book Router 成功绑定 media 后写 `cover_changed`
	- maturity recompute: 成熟度重算用例中写 `book_maturity_recomputed`（系统事件）
	- view/open: `GET /books/{book_id}` 写 `book_viewed`；`GET /blocks?book_id=...`（第一页）写 `book_opened`
	- view/open（legacy Phase0）: `GET /phase0/books/{book_id}/blocks`（第一页）写 `book_opened`

---

## Phase C（产品化）准入条件

当 Phase B 的 facts + event catalog 被验证“够用且查询频繁”之后，再做 DB migration：

- 将 `correlation_id / actor_kind / source / provenance / schema_version` 从 payload 提升为列（可索引）
- 统一 `schema_version` 演进策略（每个 event payload 顶层固定）

Phase C 迁移完成后：

- `chronicle_events` 新增列：`schema_version, provenance, source, actor_kind, correlation_id`
- 新增索引：`correlation_id`，以及 `(source, occurred_at)`（支持排障与统计）

