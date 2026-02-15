# 实验 1C：给 blocks/search_index 加索引（trigram / FTS）再对比 EXPLAIN

> 目标：让你看到两件事：
> 1) `ILIKE '%keyword%'` 在有 `pg_trgm + GIN` 后通常会从 `Seq Scan` 变成 `Bitmap Index Scan/Bitmap Heap Scan`
> 2) FTS（`to_tsvector @@ tsquery`）是另一条路线，适合“词项搜索”而不是纯子串匹配

## 0. 前置

- 建议先完成实验 1B 的 50k 造数（blocks + tags + search_index），否则数据量太小看不出 planner 变化。

## 1) 创建扩展与索引

```powershell
cd D:\Project\wordloom-v3

# 自动获取 devtest-db 容器名
$dbContainer = (docker ps --format "{{.Names}}" | Where-Object { $_ -match "devtest-db" } | Select-Object -First 1)
if (-not $dbContainer) { throw "找不到 devtest-db 容器。先运行：docker ps --format '{{.Names}}' 手动确认容器名。" }

# 执行建索引 SQL
Get-Content .\backend\scripts\labs\experiment1c_add_indexes.sql | docker exec -i $dbContainer psql -U wordloom -d wordloom_test
```

> 记录（2026-01-27）：本环境里没有 `postgres` 角色，所以不要用 `-U postgres`；直接用 `-U wordloom` 创建即可。

## 2) trigram：ILIKE 路线（期望走 Bitmap Index Scan）

### 2.1 search_index（单表）

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT entity_id, snippet
FROM search_index
WHERE entity_type = 'block'
  AND text ILIKE '%quantum%'
ORDER BY updated_at DESC
LIMIT 20;
```

为了更直观地看到 trigram 索引是否生效，建议再加一条“不排序、不 LIMIT”的过滤型查询：

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM search_index
WHERE entity_type = 'block'
  AND text ILIKE '%quantum%';
```

### 2.2 blocks（只测 content ILIKE，避免 OR/EXISTS 干扰 planner）

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT b.id, left(b.content, 200) AS snippet
FROM blocks b
WHERE b.content ILIKE '%quantum%'
ORDER BY b.updated_at DESC
LIMIT 20;
```

同样加一条过滤型查询：

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM blocks b
WHERE b.content ILIKE '%quantum%';
```

> 备注：实验 1B 的 blocks JOIN 版本因为有 `OR EXISTS (...)`，planner 可能仍偏向 Seq Scan；这是“意大利面 SQL”本身对优化器不友好的现实体现。

## 3) FTS：tsvector 路线（期望走 GIN FTS 索引）

### 3.1 search_index（单表）

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT entity_id, snippet
FROM search_index
WHERE entity_type = 'block'
  AND to_tsvector('simple', coalesce(text, '')) @@ plainto_tsquery('simple', 'quantum')
ORDER BY updated_at DESC
LIMIT 20;
```

过滤型查询（更容易看到 FTS 索引是否被使用）：

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM search_index
WHERE entity_type = 'block'
  AND to_tsvector('simple', coalesce(text, '')) @@ plainto_tsquery('simple', 'quantum');
```

### 3.2 blocks（content）

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT b.id, left(b.content, 200) AS snippet
FROM blocks b
WHERE to_tsvector('simple', coalesce(b.content, '')) @@ plainto_tsquery('simple', 'quantum')
ORDER BY b.updated_at DESC
LIMIT 20;
```

过滤型查询：

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM blocks b
WHERE to_tsvector('simple', coalesce(b.content, '')) @@ plainto_tsquery('simple', 'quantum');
```

## 4. 记录

本次输出文件都在：`backend/scripts/labs/_outputs/`

### 建索引

- 建索引输出：`experiment1c_apply_indexes_as_wordloom.txt`

### trigram（ILIKE）

- search_index（ORDER BY + LIMIT）：1.609 ms（`experiment1c_50k_trgm_search_index_order.txt`）
  - 说明：这条查询为了满足 `ORDER BY updated_at DESC LIMIT 20`，planner 更倾向走 `idx_search_index_updated`，再做 filter。
- search_index（filter-only）：14.764 ms（`experiment1c_50k_trgm_search_index_filter.txt`）
  - 关键 plan：`Bitmap Index Scan on ix_search_index_block_text_trgm`
- blocks（ORDER BY + LIMIT）：8.311 ms（`experiment1c_50k_trgm_blocks_order.txt`）
  - 关键 plan：`Bitmap Index Scan on ix_blocks_content_trgm`
- blocks（filter-only）：3.050 ms（`experiment1c_50k_trgm_blocks_filter.txt`）
  - 关键 plan：`Bitmap Index Scan on ix_blocks_content_trgm`

### FTS（to_tsvector @@ tsquery）

- search_index（ORDER BY + LIMIT）：6.946 ms（`experiment1c_50k_fts_search_index_order.txt`）
  - 同上：为了排序+limit，planner 仍可能选择 `idx_search_index_updated`，而不是 FTS 索引。
- search_index（filter-only）：2.834 ms（`experiment1c_50k_fts_search_index_filter.txt`）
  - 关键 plan：`Bitmap Index Scan on ix_search_index_block_text_fts`
- blocks（ORDER BY + LIMIT）：2.152 ms（`experiment1c_50k_fts_blocks_order.txt`）
  - 关键 plan：`Bitmap Index Scan on ix_blocks_content_fts`
- blocks（filter-only）：1.923 ms（`experiment1c_50k_fts_blocks_filter.txt`）
  - 关键 plan：`Bitmap Index Scan on ix_blocks_content_fts`

### 观察

- “最近更新的 20 条匹配”这种 query 形态（`ORDER BY updated_at DESC LIMIT 20`）很容易被 `updated_at` 索引主导：先按时间拿一小段，再 filter 文本。
- 要验证 trigram/FTS 索引是否真正用于“过滤”，用 filter-only query 最直观：能看到 `Bitmap Index Scan` 是否出现。
- 这也解释了为什么 search_index 的收益通常是“两步走”：
  - 结构层面：把 JOIN/OR/子查询收敛成单表（实验 1B）。
  - 索引层面：再用 trigram/FTS 把 filter 从 Seq Scan 变成索引路径（实验 1C）。
