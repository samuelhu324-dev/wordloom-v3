-- 创建统一媒体资源表
-- 支持 Checkpoint Marker 多图、Note 封面、Bookshelf 封面

CREATE TABLE IF NOT EXISTS orbit_media_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 文件信息
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(50),
    file_hash VARCHAR(64) UNIQUE,

    -- 多态关联：entity_type 用来区分是哪种资源
    -- 可选值: checkpoint_marker, note_cover, bookshelf_cover
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,

    -- 图片元数据
    width INTEGER,
    height INTEGER,

    -- 排序和管理
    display_order INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    deleted_at TIMESTAMP,

    -- 唯一约束：同一实体的同一文件不能重复
    CONSTRAINT unique_file_per_entity UNIQUE(entity_id, file_hash)
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_media_entity ON orbit_media_resources(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_media_deleted ON orbit_media_resources(deleted_at);
CREATE INDEX IF NOT EXISTS idx_media_created ON orbit_media_resources(created_at);
CREATE INDEX IF NOT EXISTS idx_media_file_hash ON orbit_media_resources(file_hash);

-- 添加一个列到 checkpoint_markers 表来关联媒体记录（可选，用于查询优化）
-- 这个列用于快速获取某个 marker 的所有媒体
ALTER TABLE orbit_note_checkpoint_markers
ADD COLUMN IF NOT EXISTS image_urls JSONB DEFAULT '[]'::jsonb;

-- 添加一个列到 notes 表来关联封面图（可选）
ALTER TABLE orbit_notes
ADD COLUMN IF NOT EXISTS cover_image_id UUID;

-- 添加一个列到 bookshelves 表来关联封面图（可选）
ALTER TABLE orbit_bookshelves
ADD COLUMN IF NOT EXISTS cover_image_id UUID;

-- 输出表创建完成信息
SELECT 'Media resources system initialized successfully' as status;
