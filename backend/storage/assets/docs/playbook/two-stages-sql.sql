-- stage 1: candidates from search_index (cheap)
WITH candidate_blocks AS (
  SELECT
    si.entity_id AS block_id,
    si.event_version AS order_key
  FROM search_index si
  WHERE si.entity_type = 'block'
    AND to_tsvector('english', si.text) @@ plainto_tsquery('english', :q)
  -- 用 event_version 做排序键，避免索引更新与业务表更新时间不一致导致“排序抖动”
  ORDER BY si.event_version DESC
  LIMIT :candidate_limit
)

-- stage 2: business filter + assemble tags (strict)
SELECT
  b.id,
  b.content,
  array_remove(array_agg(DISTINCT t.name), NULL) AS tags
FROM candidate_blocks c
JOIN blocks b
  ON b.id = c.block_id
LEFT JOIN tag_associations ta
  ON ta.entity_type = 'block' AND ta.entity_id = b.id
LEFT JOIN tags t
  ON t.id = ta.tag_id AND t.deleted_at IS NULL
WHERE b.soft_deleted_at IS NULL
  AND (:book_id::uuid IS NULL OR b.book_id = :book_id)
GROUP BY b.id, c.order_key
ORDER BY c.order_key DESC
LIMIT :result_limit;