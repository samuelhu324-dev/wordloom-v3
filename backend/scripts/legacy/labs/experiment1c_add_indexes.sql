-- 实验 1C：为 ILIKE / 搜索场景添加索引（DEVTEST-DB-5435）
-- 目标：让 search_index / blocks 在文本搜索时尽量走索引而不是 Seq Scan。

-- 1) trigram
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- search_index：只索引 block 行（partial index），避免把所有 entity_type 混在一起
CREATE INDEX IF NOT EXISTS ix_search_index_block_text_trgm
ON search_index
USING GIN (text gin_trgm_ops)
WHERE entity_type = 'block';

-- blocks：直接索引 content
CREATE INDEX IF NOT EXISTS ix_blocks_content_trgm
ON blocks
USING GIN (content gin_trgm_ops);

-- 2) FTS（可选）：只做索引，不改变表结构。注意：查询时必须用 @@ tsquery 才会使用。
CREATE INDEX IF NOT EXISTS ix_search_index_block_text_fts
ON search_index
USING GIN (to_tsvector('simple', coalesce(text, '')))
WHERE entity_type = 'block';

CREATE INDEX IF NOT EXISTS ix_blocks_content_fts
ON blocks
USING GIN (to_tsvector('simple', coalesce(content, '')));
