# 实验 1B：blocks（LIKE + JOIN tags） vs search_index（单表）

> 目标：在 50k blocks 下，对比：
> - blocks：`ILIKE` + `JOIN tag_associations/tags`（会产生 DISTINCT/GROUP BY 的“意大利面 SQL”）
> - search_index：单表（denormalized text 包含 block content + tag names）

## 0. 造数

```powershell
cd D:\Project\wordloom-v3
$env:DATABASE_URL = "postgresql://wordloom:wordloom@localhost:5435/wordloom_test"
.\.venv\Scripts\python.exe .\backend\scripts\labs\experiment1b_generate_blocks_with_tags.py --reset --seed 12345 --count 50000 --tags 500 --tags-per-block 2 --tag-keyword-rate 0.01 --with-search-index
```

## 1) blocks：LIKE + JOIN tag

```sql
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
```

### 输出（50k, 2026-01-27）

输出文件：`backend/scripts/labs/_outputs/experiment1b_50k_blocks_join.txt`

```text
Limit  (cost=2692906.88..2692906.93 rows=20 width=56) (actual time=258.724..258.730 rows=20 loops=1)
  Buffers: shared hit=2250 read=4397
  ->  Sort  (cost=2692906.88..2693034.41 rows=51010 width=56) (actual time=174.205..174.209 rows=20 loops=1)
    Sort Key: b.updated_at DESC
    Sort Method: top-N heapsort  Memory: 30kB
    Buffers: shared hit=2250 read=4397
    ->  Seq Scan on blocks b  (cost=0.00..2691549.52 rows=51010 width=56) (actual time=10.959..173.425 rows=1739 loops=1)
      Filter: ((content ~~* '%quantum%'::text) OR (hashed SubPlan 2))
      Rows Removed by Filter: 98261
      Buffers: shared hit=2247 read=4397
      SubPlan 2
        ->  Nested Loop  (cost=0.42..89.95 rows=176 width=16) (actual time=6.051..6.891 rows=797 loops=1)
          Buffers: shared hit=213 read=9
          ->  Seq Scan on tags t  (cost=0.00..24.25 rows=1 width=16) (actual time=6.006..6.149 rows=4 loops=1)
            Filter: ((name)::text ~~* '%quantum%'::text)
            Rows Removed by Filter: 496
            Buffers: shared hit=9 read=9
          ->  Index Only Scan using uq_tag_associations_tag_entity on tag_associations ta  (cost=0.42..63.94 rows=176 width=32) (actual time=0.019..0.173 rows=199 loops=4)
            Index Cond: ((tag_id = t.id) AND (entity_type = 'block'::entitytype))
            Heap Fetches: 185
            Buffers: shared hit=204
Planning Time: 2.216 ms
JIT:
  Timing: Generation 0.629 ms, Inlining 46.280 ms, Optimization 26.226 ms, Emission 21.490 ms, Total 94.625 ms
Execution Time: 275.840 ms
```

## 2) search_index：单表

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT entity_id, snippet
FROM search_index
WHERE entity_type = 'block'
  AND text ILIKE '%quantum%'
ORDER BY updated_at DESC
LIMIT 20;
```

### 输出（50k, 2026-01-27）

输出文件：`backend/scripts/labs/_outputs/experiment1b_50k_search_index.txt`

```text
Limit  (cost=10880.12..10880.14 rows=8 width=228) (actual time=156.655..156.658 rows=20 loops=1)
  Buffers: shared hit=3494 read=6129
  ->  Sort  (cost=10880.12..10880.14 rows=8 width=228) (actual time=156.653..156.655 rows=20 loops=1)
    Sort Key: updated_at DESC
    Sort Method: top-N heapsort  Memory: 30kB
    Buffers: shared hit=3494 read=6129
    ->  Seq Scan on search_index  (cost=0.00..10880.00 rows=8 width=228) (actual time=0.237..156.267 rows=1739 loops=1)
      Filter: ((text ~~* '%quantum%'::text) AND ((entity_type)::text = 'block'::text))
      Rows Removed by Filter: 98261
      Buffers: shared hit=3491 read=6129
Planning Time: 0.752 ms
Execution Time: 156.690 ms
```

## 3. 记录

- blocks 执行时间：275.840 ms
- search_index 执行时间：156.690 ms
- 观察：
  - 两边都出现了 `Seq Scan`：因为 `ILIKE '%...%'` 对 B-Tree 索引不友好；search_index 的好处是把 JOIN/子查询形态收敛成单表，结构更简单。
  - blocks 侧额外出现了 `OR + SubPlan(Nested Loop)`，以及明显的 JIT 成本（本次 JIT Total 约 95ms），这就是“意大利面”复杂度的来源。
  - 下一步如果要让 search_index 真正走索引过滤：建议加 trigram（`gin_trgm_ops`）或 `tsvector + GIN`，再对比 planner 是否从 Seq Scan 转为 Bitmap/Index Scan。
