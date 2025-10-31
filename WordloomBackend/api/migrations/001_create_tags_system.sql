-- ============================================================================
-- Wordloom Orbit Tags System - Database Migration
-- 创建独立的标签表和关联表
-- ============================================================================

-- Step 1: 创建标签表
CREATE TABLE IF NOT EXISTS orbit_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#808080',  -- 十六进制颜色代码，默认灰色
    description TEXT,                     -- 标签描述
    count INT DEFAULT 0,                  -- 该标签被使用的次数（缓存字段）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: 创建关联表（Note 和 Tag 的多对多关系）
CREATE TABLE IF NOT EXISTS orbit_note_tags (
    note_id UUID NOT NULL REFERENCES orbit_notes(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES orbit_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (note_id, tag_id)
);

-- Step 3: 创建索引以加快查询
CREATE INDEX IF NOT EXISTS idx_orbit_note_tags_tag_id ON orbit_note_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_orbit_note_tags_note_id ON orbit_note_tags(note_id);
CREATE INDEX IF NOT EXISTS idx_orbit_tags_name ON orbit_tags(name);

-- ============================================================================
-- Data Migration: 从 orbit_notes.tags (text array) 迁移到新表结构
-- ============================================================================

-- Step 4: 提取所有唯一的标签并插入 orbit_tags 表
INSERT INTO orbit_tags (name, color)
SELECT DISTINCT UNNEST(tags) AS tag_name, '#808080'
FROM orbit_notes
WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
ON CONFLICT (name) DO NOTHING;

-- Step 5: 计算每个标签的使用次数
UPDATE orbit_tags AS t
SET count = (
    SELECT COUNT(*)
    FROM orbit_notes
    WHERE tags @> ARRAY[t.name]
);

-- Step 6: 填充关联表（orbit_note_tags）
INSERT INTO orbit_note_tags (note_id, tag_id)
SELECT n.id, t.id
FROM orbit_notes n
JOIN orbit_tags t ON t.name = ANY(n.tags)
WHERE n.tags IS NOT NULL AND array_length(n.tags, 1) > 0
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Verification Queries (验证数据完整性)
-- ============================================================================

-- 查看迁移后的标签总数
-- SELECT COUNT(*) as total_tags FROM orbit_tags;

-- 查看每个标签的使用情况
-- SELECT name, count, color FROM orbit_tags ORDER BY count DESC;

-- 查看某个 Note 的所有标签
-- SELECT n.id, n.title, array_agg(t.name) as tags
-- FROM orbit_notes n
-- LEFT JOIN orbit_note_tags nt ON n.id = nt.note_id
-- LEFT JOIN orbit_tags t ON nt.tag_id = t.id
-- GROUP BY n.id, n.title;

-- ============================================================================
-- Optional: 保留备份（迁移后 1 周可删除）
-- ============================================================================

-- 重命名旧的 tags 字段为备份（先不删除）
-- ALTER TABLE orbit_notes RENAME COLUMN tags TO tags_backup;
