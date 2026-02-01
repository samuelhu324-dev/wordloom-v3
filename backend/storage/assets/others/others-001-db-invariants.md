# DB Invariants (Blob/Ref Model)

这份文件不是科普文，也不是 README。
它是数据库宪法摘要：

> 这个系统在 DB 层保证了哪些不可违背的事实（invariants）？

目标读者：后端/DB/数据修复脚本作者。

---

## A. 术语

- **Blob（内容层）**：按 `file_hash/blob_hash` 作为内容地址（content-addressed）的二进制对象。
	- 关注“文件是什么”：hash、mime、size、storage_key…
	- 与业务实体无关，可被多个实体/多个 role 共享。
- **Ref（引用层）**：某个业务实体关联某个 blob 的一条关系。
	- 关注“谁在引用它”：workspace/entity/role/position/blob_hash…
- **Active（活跃行）**：`deleted_at is null`。
	- 约束（唯一性）只对 active 行生效；软删行不参与唯一性冲突。

---

## B. 表与职责

- **public.media_blobs**
	- 存内容元数据：`file_hash`, `mime_type`, `file_size`, `storage_key`, …
	- 通过 `file_hash` 做全局去重：同内容只存一份 blob 记录。
- **public.media_refs**
	- 存引用关系：`workspace_id`, `entity_type`, `entity_id`, `role`, `position(display_order)`, `blob_hash`, `deleted_at`, …
	- 通过 partial unique index 保证“幂等 attach”与“槽位唯一”。

---

## C. Invariants（不可违背的事实）

按“规则 + 约束载体 + 失败会怎样”描述。

### I1 Blob 唯一

- 规则：同 `blob_hash/file_hash` 只能有一条 blob。
- 约束载体：`PRIMARY KEY (file_hash)`（或 `UNIQUE(file_hash)`）。
- 失败会怎样：重复插入同 hash → DB 报唯一冲突；写入逻辑应采用 `UPSERT`（冲突即复用）。

### I2 Ref 幂等（slot 维度，应用语义）

- 背景：当前系统采用 **I3 Slot 唯一** 作为主要约束（policy2）。
  这意味着：允许同一个 blob 在同一 entity 的同一 role 下出现多次（只要 position 不同）。

- 规则（应用语义，不是 DB 唯一索引）：同一个 slot（workspace/entity/role/position）若重复写入同一个 blob，
  视为幂等重试，应返回既有 active ref，不产生新的 active ref。

- 约束载体：
  - DB 层仅强制 I3（slot 唯一）。
  - “同 slot 同 blob 的幂等”由写入逻辑保证（查询当前 slot 的 active ref：
    - 若 blob_hash 相同 → NOOP/DUPLICATE → OK_RETURN_EXISTING
    - 若 blob_hash 不同 → REPLACE → OK_REPLACED）

- 失败会怎样：
  - 若未实现上述逻辑，重复写入会触发 I3 的唯一冲突（500 或 IntegrityError），或者产生错误的替换行为。

### I3 Slot 唯一（同 entity 的同一槽位只允许一张 active）

- 规则：同一个 entity 的 `(role, position)` 是一个槽位（slot），同一时刻只能有一张 active。
	- 用于：封面（position=0）、列表第 N 张图等。
- 约束载体：partial unique index：
	- `(workspace_id, entity_type, entity_id, role, position) WHERE deleted_at IS NULL`
- 失败会怎样：同槽位插入新 ref → DB 报唯一冲突；应用必须走“替换/移动”逻辑（例如软删旧 ref 或更新 slot 指向），而不是盲目 `insert`。

### I4 删除语义（删除 ref 不删除 blob）

- 规则：删除 ref（软删/硬删）只影响该引用，不影响 blob，也不影响其它 role/其它实体对同一 blob 的引用。
- 约束载体：
	- ref 使用 `deleted_at` 表达删除。
	- blob 不做 cascade delete（GC 另议）。
- 失败会怎样：
	- 若错误地 cascade delete blob，会导致其它引用断裂（orphan refs）或媒体丢失。
	- 正确行为：删 ref 后 blob 仍存在，直到未来 GC 判断 “unreferenced”。

### I5 写入事件强一致（Decision/Result 固化）

这是一条工程约束：**媒体写入行为必须可回放**。
做法是把写入的关键决策与最终结果记录到 DB，并且与业务写入处于**同一事务**（强一致）：

- 规则：每次媒体写入请求（以 `request_id` 标识）应至少落两条事件：
	- `WRITE_DECISION`：我打算怎么做
	- `WRITE_RESULT`：实际做到了什么
- 约束载体：
	- `event_type` 使用 enum（最小四类：`WRITE_REQUEST` / `WRITE_DECISION` / `WRITE_DB` / `WRITE_RESULT`）
	- `decision` / `result` 使用 enum（固定取值，见下）
	- 事件表的插入与 `media_blobs/media_refs` 的写入在同一事务中提交/回滚
- 失败会怎样：
	- 若事件与业务不在同一事务：会出现“写入成功但无事件”或“事件存在但写入回滚”，导致排障不可回放。

#### Decision（你决定“要做什么”）

用于 `WRITE_DECISION` 事件，固定取值：

- `INSERT`：该 slot 为空，计划新增 ref。
- `DUPLICATE`：命中幂等规则（同 entity+role 已 attach 同一 blob），计划不新增，直接返回既有 ref。
- `REPLACE`：slot 已占用，但业务允许替换（先软删旧 ref 或更新 slot 指向，再写入新 ref）。
- `REJECT`：业务规则拒绝（例如 position 越界、role 不允许、权限不足、类型不允许）。
- `NOOP`：本次请求不应产生任何 DB 变更（常见于重复提交/客户端重放；语义上比 `DUPLICATE` 更强调“什么都不做”）。

区分要点：
- `DUPLICATE` = 命中 **I2 幂等 attach**（同资源重复 attach）。
- `NOOP` = 更泛的“这次什么都不做”，可能是重复请求、非法但选择静默、或已是目标状态。

#### Result（你最终“做成了什么”）

用于 `WRITE_RESULT` 事件，固定取值：

- `OK_INSERTED`：确实新增了 ref。
- `OK_RETURN_EXISTING`：未新增，返回已存在 ref（通常对应 `DUPLICATE/NOOP`）。
- `OK_REPLACED`：替换成功（旧 ref 不再 active，新 ref 生效）。
- `REJECTED`：业务拒绝（不算系统错误）。
- `FAILED`：失败（记录 `error_code` / `error_message`，通常伴随事务回滚）。

#### Decision → Result 的允许映射（强约束）

- `INSERT` → `OK_INSERTED` | `FAILED`
- `DUPLICATE` → `OK_RETURN_EXISTING` | `FAILED`
- `REPLACE` → `OK_REPLACED` | `FAILED`
- `REJECT` → `REJECTED`
- `NOOP` → `OK_RETURN_EXISTING` | `FAILED`

建议在 DB 侧使用 enum 把取值“钉死”（避免自由字符串漂移）：

```sql
-- 推荐类型名（示例）
-- create type public.media_write_decision as enum (...);
-- create type public.media_write_result as enum (...);
-- create type public.media_write_event_type as enum ('WRITE_REQUEST','WRITE_DECISION','WRITE_DB','WRITE_RESULT');
```

---

## D. 常用健康检查 SQL（3 条足够）

### D1 Slot 冲突检查（应返回 0 行）

```sql
select workspace_id, entity_type, entity_id, role, position, count(*) as n
from public.media_refs
where deleted_at is null
group by workspace_id, entity_type, entity_id, role, position
having count(*) > 1
order by n desc
limit 50;
```

### D2 entity+blob 幂等冲突检查（应返回 0 行）

```sql
select workspace_id, entity_type, entity_id, role, blob_hash, count(*) as n
from public.media_refs
where deleted_at is null
group by workspace_id, entity_type, entity_id, role, blob_hash
having count(*) > 1
order by n desc
limit 50;
```

### D3 Orphan refs（ref 找不到 blob，应返回 0 行）

```sql
select r.*
from public.media_refs r
left join public.media_blobs b on b.file_hash = r.blob_hash
where b.file_hash is null
limit 50;
```

---

## E. 写入事件健康检查（可选，但推荐）

### E1 同一 request_id 的事件序列（用于回放）

```sql
select created_at, event_type, decision, result, error_code
from public.media_write_events
where request_id = '<REQUEST_ID>'::uuid
order by created_at asc;
```

### E2 缺失决策/结果事件的请求（应尽量接近 0）

```sql
with per_request as (
	select
		request_id,
		bool_or(event_type = 'WRITE_DECISION') as has_decision,
		bool_or(event_type = 'WRITE_RESULT') as has_result
	from public.media_write_events
	group by request_id
)
select *
from per_request
where not (has_decision and has_result)
limit 50;
```

---

## ✅ 验收标准

任何人看完这份 md，都能回答：

- “重复上传会发生什么？”
	- 命中 I2 → 返回已有 ref，不新增。
- “为什么 slot 冲突会报错？”
	- 命中 I3 → 必须走替换/移动逻辑。
- “删除会删到哪里？”
	- 命中 I4 → 只删 ref，不删 blob。