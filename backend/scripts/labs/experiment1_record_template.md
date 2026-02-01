# 实验 1：LIKE 基线 vs search_index 单表（5k/50k）记录模板

> 目标：用同一关键词查询，对比 **业务表 blocks** 与 **冗余索引表 search_index** 的查询代价差异。
> 建议每次只改一个变量（规模 5k→50k），其余参数保持不变。

## 0. 环境信息

- 日期：2026-01-27
- 分支/Commit：____
- 机器：____（CPU/内存）
- OS：Windows
- 数据库：DEVTEST-DB-5435（`localhost:5435/wordloom_test`）
- 数据库版本：PostgreSQL 14.20 (Debian) on x86_64-pc-linux-gnu

## 1. 数据生成参数

- 脚本：`backend/scripts/labs/experiment1_generate_blocks.py`
- `--keyword`：`quantum`
- `--keyword-rate`：0.01（= 1%）
- `--seed`：12345
- `--with-search-index`：是
- `--reset`：是（确保可重复跑）

## 2. 数据集 A：5k

### 2.1 造数命令

- 命令：
  - `$env:DATABASE_URL="postgresql://wordloom:wordloom@localhost:5435/wordloom_test"`
  - `\.venv\Scripts\python.exe .\backend\scripts\labs\experiment1_generate_blocks.py --reset --seed 12345 --count 5000 --with-search-index`
- 输出：OK: inserted 5000 blocks into book=32a0a091-7a7b-443f-abe2-26a51e3b4af2. Also inserted search_index rows.

### 2.2 blocks 基线

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, left(content, 200) AS snippet
FROM blocks
WHERE content ILIKE '%quantum%'
ORDER BY updated_at DESC
LIMIT 20;
```

- Planning Time：3.184 ms
- Execution Time：7.437 ms
- Rows：匹配 49 行；返回 20 行（LIMIT 20）
- Buffers：shared hit=420
- Scan：Seq Scan

<details>
<summary>EXPLAIN 输出</summary>

```text
Limit  (cost=482.44..482.49 rows=20 width=56) (actual time=7.007..7.008 rows=20 loops=1)
  Buffers: shared hit=420
  ->  Sort  (cost=482.44..482.69 rows=101 width=56) (actual time=7.005..7.006 rows=20 loops=1)
        Sort Key: updated_at DESC
        Sort Method: top-N heapsort  Memory: 30kB
        Buffers: shared hit=420
        ->  Seq Scan on blocks  (cost=0.00..479.75 rows=101 width=56) (actual time=0.644..6.913 rows=49 loops=1)
              Filter: (content ~~* '%quantum%'::text)
              Rows Removed by Filter: 4951
              Buffers: shared hit=417
Planning:
  Buffers: shared hit=208
Planning Time: 3.184 ms
Execution Time: 7.437 ms
```

</details>

### 2.3 search_index（entity_type='block'）

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT entity_id, snippet
FROM search_index
WHERE entity_type = 'block'
  AND text ILIKE '%quantum%'
ORDER BY updated_at DESC
LIMIT 20;
```

- Planning Time：0.757 ms
- Execution Time：2.222 ms
- Rows：返回 20 行（LIMIT 20）；过滤丢弃 1502 行
- Buffers：shared hit=114
- Scan：Index Scan Backward（idx_search_index_updated）

<details>
<summary>EXPLAIN 输出</summary>

```text
Limit  (cost=0.28..161.67 rows=20 width=228) (actual time=0.339..2.199 rows=20 loops=1)
  Buffers: shared hit=114
  ->  Index Scan Backward using idx_search_index_updated on search_index  (cost=0.28..815.28 rows=101 width=228) (actual time=0.338..2.197 rows=20 loops=1)
        Filter: ((text ~~* '%quantum%'::text) AND ((entity_type)::text = 'block'::text))
        Rows Removed by Filter: 1502
        Buffers: shared hit=114
Planning:
  Buffers: shared hit=259
Planning Time: 0.757 ms
Execution Time: 2.222 ms
```

</details>

## 3. 数据集 B：50k

### 3.1 造数命令

- 命令：
  - `$env:DATABASE_URL="postgresql://wordloom:wordloom@localhost:5435/wordloom_test"`
  - `\.venv\Scripts\python.exe .\backend\scripts\labs\experiment1_generate_blocks.py --reset --seed 12345 --count 50000 --with-search-index`
- 输出：OK: inserted 50000 blocks into book=32a0a091-7a7b-443f-abe2-26a51e3b4af2. Also inserted search_index rows.

### 3.2 blocks 基线

（同 2.2，粘贴指标与 EXPLAIN）

- Planning Time：0.676 ms
- Execution Time：72.160 ms
- Rows：匹配 470 行；返回 20 行（LIMIT 20）
- Buffers：shared hit=2297
- Scan：Seq Scan

<details>
<summary>EXPLAIN 输出</summary>

```text
Limit  (cost=2654.01..2654.06 rows=20 width=56) (actual time=72.131..72.134 rows=20 loops=1)
  Buffers: shared hit=2297
  ->  Sort  (cost=2654.01..2655.40 rows=556 width=56) (actual time=72.130..72.131 rows=20 loops=1)
        Sort Key: updated_at DESC
        Sort Method: top-N heapsort  Memory: 30kB
        Buffers: shared hit=2297
        ->  Seq Scan on blocks  (cost=0.00..2639.21 rows=556 width=56) (actual time=0.195..71.936 rows=470 loops=1)
              Filter: (content ~~* '%quantum%'::text)
              Rows Removed by Filter: 49530
              Buffers: shared hit=2294
Planning:
  Buffers: shared hit=204
Planning Time: 0.676 ms
Execution Time: 72.160 ms
```

</details>

### 3.3 search_index

（同 2.3，粘贴指标与 EXPLAIN）

- Planning Time：0.843 ms
- Execution Time：5.749 ms
- Rows：返回 20 行（LIMIT 20）；过滤丢弃 3796 行
- Buffers：shared hit=281
- Scan：Index Scan Backward（idx_search_index_updated）

<details>
<summary>EXPLAIN 输出</summary>

```text
Limit  (cost=0.29..96.80 rows=20 width=228) (actual time=0.128..5.728 rows=20 loops=1)
  Buffers: shared hit=281
  ->  Index Scan Backward using idx_search_index_updated on search_index  (cost=0.29..4874.29 rows=1010 width=228) (actual time=0.127..5.725 rows=20 loops=1)
        Filter: ((text ~~* '%quantum%'::text) AND ((entity_type)::text = 'block'::text))
        Rows Removed by Filter: 3796
        Buffers: shared hit=281
Planning:
  Buffers: shared hit=251
Planning Time: 0.843 ms
Execution Time: 5.749 ms
```

</details>

## 4. 结论（先写观察，不要先解释）

- 观察 1：____
- 观察 2：____
- 下一步猜想：____

## 5. 进阶（可选）

- 为 blocks/content 和 search_index/text 分别加 `GIN (to_tsvector(...))` 或 trigram 索引后再跑对比
- 把 LIKE 改成 `to_tsvector @@ plainto_tsquery`，看 planner 是否切换到索引扫描
