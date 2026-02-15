🧠 并发一致性模式：为什么判断必须进 SQL，而不能只写在业务层
一、问题背景（Problem Context）

在事件驱动 / 异步系统中，同一实体的多个事件可能：

并发处理（多个 handler / worker）

乱序到达（新事件先到，旧事件后到）

被重复投递（重试 / 至少一次投递）

典型场景包括：

search index 更新

状态同步（rename / status change）

投影表（read model）更新

目标是保证：

最终状态不会被旧事件“倒退覆盖”

二、天真的做法（❌ 错误示例）

在业务层（handler / service）中写 if-else 判断：

row = load_from_db(entity_id)

if event.version < row.version:
    return  # 忽略旧事件

save_new_state()

❌ 为什么看起来对，但实际不安全？

因为这是一个 Read → Check → Write 的流程：

读数据库（read）

判断条件（check）

写数据库（write）

在并发环境下，这三步 不是原子的。

三、并发下的真实失败场景（Failure Timeline）

两个 handler 并发执行：

时间	Handler A（新事件 v2）	Handler B（旧事件 v1）
t1	读到 row.version = 1	读到 row.version = 1
t2	判断通过	判断通过
t3	更新为 version = 2	更新为 version = 1（倒退）

结果：

旧事件在“合法判断”下，覆盖了新状态

这类问题在并发理论中称为：

TOCTOU（Time Of Check To Time Of Use）

Read–Modify–Write race

四、正确的做法（✅ 数据库级防倒退）

把“是否允许更新”的判断 下沉到数据库 UPDATE 本身。

SQL / ORM 语义示例
UPDATE search_index
SET
  text = :new_text,
  event_version = :incoming_version
WHERE
  entity_id = :id
  AND event_version <= :incoming_version;


或使用 UPSERT：

INSERT INTO search_index (...)
ON CONFLICT (entity_id)
DO UPDATE SET ...
WHERE search_index.event_version <= EXCLUDED.event_version;

关键点

判断和更新在 同一个原子语句 中完成

并发下不会出现“先判断、后被插队”的窗口

更新要么发生，要么被数据库拒绝（0 rows affected）

五、这在工程上的正式名字（Terminology）

这类模式在工程中被称为：

Atomic operation（原子操作）

Statement-level atomicity（语句级原子性）

Optimistic locking / Optimistic concurrency control

Conditional update / Guarded update

Compare-and-Set (CAS) semantics

一句标准工程表述：

Use a guarded atomic update in the database to prevent out-of-order events from regressing state.

六、为什么不能只靠业务层？
层	能力
业务层（Python / Service）	表达意图、流程、规则
数据库	并发控制、锁、原子性

业务层：

看的是 过去读到的快照

无法阻止并发插队

数据库：

在 同一个临界区 内判断 + 修改

天生为并发一致性而设计

👉 这是职责分工，不是写法偏好

---

## 补充实验：50k blocks + tags（JOIN） vs search_index（单表）

> 目标：让你亲眼看到“意大利面 SQL”是怎么出现的，以及 denormalized 投影为什么能把查询收敛成单表。

### 1) 一键造数（50k）

```powershell
cd D:\Project\wordloom-v3
$env:DATABASE_URL = "postgresql://wordloom:wordloom@localhost:5435/wordloom_test"

# 造 50k blocks + 500 tags + 每个 block 2 个 tag，并把 tag 名也写进 search_index.text
.\.venv\Scripts\python.exe .\backend\scripts\labs\experiment1b_generate_blocks_with_tags.py `
  --reset --seed 12345 --count 50000 --tags 500 --tags-per-block 2 --tag-keyword-rate 0.01 --with-search-index

# 自动获取 devtest-db 容器名（避免你机器上名字不一致）
$dbContainer = (docker ps --format "{{.Names}}" | Where-Object { $_ -match "devtest-db" } | Select-Object -First 1)
if (-not $dbContainer) { throw "找不到 devtest-db 容器。先运行：docker ps --format '{{.Names}}' 手动确认容器名。" }
```

### 2) blocks：LIKE + JOIN tags（意大利面 SQL）

```powershell
$Q_blocks_join = @'
EXPLAIN (ANALYZE, BUFFERS)
SELECT b.id, left(b.content, 200) AS snippet
FROM blocks b
WHERE b.content ILIKE '%quantum%'
   OR EXISTS (
       SELECT 1
       FROM tag_associations ta
       JOIN tags t ON t.id = ta.tag_id
       WHERE ta.entity_type = 'block'
         AND ta.entity_id = b.id
         AND t.name ILIKE '%quantum%'
   )
ORDER BY b.updated_at DESC
LIMIT 20;
'@
docker exec -i $dbContainer psql -U wordloom -d wordloom_test -c "$Q_blocks_join"
```

### 3) search_index：单表（收敛后的查询）

```powershell
$Q_search_index = @'
EXPLAIN (ANALYZE, BUFFERS)
SELECT entity_id, snippet
FROM search_index
WHERE entity_type = 'block'
  AND text ILIKE '%quantum%'
ORDER BY updated_at DESC
LIMIT 20;
'@
docker exec -i $dbContainer psql -U wordloom -d wordloom_test -c "$Q_search_index"
```

你会看到的典型现象：
- blocks 侧通常是 `Seq Scan + (OR + SubPlan/Join)`，数据量上来后会明显变慢（并发下更抖）。
- search_index 侧是单表扫描路径（这里我们走的是 `idx_search_index_updated` 的倒序索引扫描），结构更稳定。

### 后续（实验 1C）：让 ILIKE 真的走索引

如果你希望 search_index 的 `text ILIKE '%keyword%'` 不再 Seq Scan：
- 建议加 `pg_trgm + GIN`（trigram）或 `tsvector + GIN`（FTS），然后重新跑 EXPLAIN 看 planner 是否转为 `Bitmap Index Scan`。
- 模板与建索引 SQL 见：
  - `backend/scripts/labs/experiment1c_add_indexes.sql`
  - `backend/scripts/labs/experiment1c_record_template.md`

七、适用场景总结（When to Use）

当满足以下任意条件时，必须使用数据库级条件更新：

同一实体可能并发更新

事件可能乱序到达

系统允许重试 / 重放

状态不能倒退（版本 / 时间单调）

八、一句话记忆锚点（Mental Anchor）

业务层 if 判断的是“我看到的过去”；
SQL WHERE 判断的是“我允许的现在”。

或者更狠一句：

并发系统里，只有数据库能保证判断和修改发生在同一个时间点。

九、来自当前项目的实证（Proof from Practice）

在 Wordloom 的 search_index 实验中：

注释掉 SQL 的 WHERE event_version <= excluded.event_version

测试 test_search_index_*_is_out_of_order_safe 立即失败

恢复该条件，测试稳定通过

这是被测试验证过的并发一致性约束，而不是理论假设。