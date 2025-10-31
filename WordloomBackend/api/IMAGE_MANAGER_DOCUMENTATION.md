# Wordloom Orbit 图片管理系统实现文档

## 概述

本文档描述了为 Wordloom Orbit 系统实现的自动化图片生命周期管理解决方案。该系统确保所有用户上传的图片按照所属 Note 的 ID 进行分类存储，并在 Note 更新或删除时自动清理相关图片。

## 需求分析

### 原始问题
- 图片上传时没有按 Note ID 进行分类存储
- 图片与 Note 之间没有追踪关系
- 删除 Note 时相关图片不会自动清理
- 更新 Note 内容时，未被引用的旧图片不会被移除

### 设计目标
1. **自动文件夹创建**：新创建 Note 时自动生成对应的图片文件夹
2. **分类存储**：所有图片按 `{UPLOAD_DIR}/{note_id}/{filename}` 的结构存储
3. **引用追踪**：从 markdown 内容中自动提取被引用的图片
4. **自动清理**：删除 Note 时清理所有相关图片，更新内容时清理未被引用的图片
5. **灵活查询**：提供 API 端点查看图片状态信息

## 系统架构

### 核心模块

#### 1. `ImageManager` 类 (`app/core/image_manager.py`)

负责所有与图片生命周期相关的操作。

**主要方法：**

```python
class ImageManager:
    def create_note_folder(note_id: str) -> Path:
        """为新 Note 创建图片文件夹"""

    def delete_note_folder(note_id: str) -> bool:
        """删除 Note 对应的整个图片文件夹"""

    def extract_referenced_images(content_md: Optional[str]) -> Set[str]:
        """从 markdown 内容中提取所有被引用的图片文件名"""

    def get_unused_images(note_id: str, content_md: Optional[str]) -> Set[str]:
        """获取未被引用的图片文件列表"""

    def cleanup_unused_images(note_id: str, content_md: Optional[str]) -> list[str]:
        """删除未被引用的图片，返回被删除的文件名列表"""
```

**关键特性：**
- 支持多种 markdown 图片格式：`![alt](url)` 和 HTML `<img>` 标签
- URL 格式支持：
  - `/uploads/note_id/filename.png`
  - `uploads/note_id/filename.png`
  - 绝对 URL：`http://domain/uploads/note_id/filename.png`
- 自动去除查询参数和片段标识符

### 集成点

#### 2. Notes 路由修改 (`app/routers/orbit/notes.py`)

**修改 #1：创建 Note 时**
```python
@router.post("/notes", response_model=NoteOut)
def create_note(payload: NoteIn, db: Session = Depends(get_orbit_db)):
    # ... 数据库操作 ...
    # 为新创建的 note 自动创建对应的图片文件夹
    image_manager.create_note_folder(str(n.id))
    return n
```

**修改 #2：删除 Note 时**
```python
@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: str, db: Session = Depends(get_orbit_db)):
    # ... 数据库操作 ...
    # 删除 note 对应的整个图片文件夹
    image_manager.delete_note_folder(note_id)
```

**修改 #3：更新 Note 时**
```python
@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: str, payload: NoteIn, db: Session = Depends(get_orbit_db)):
    # ... 数据库操作 ...
    # 更新内容后，清理未被引用的图片
    image_manager.cleanup_unused_images(note_id, n.content_md)
    return n
```

#### 3. Uploads 路由修改 (`app/routers/orbit/uploads.py`)

**修改 #1：上传图片时确保文件夹存在**
```python
@router.post("/uploads")
async def upload_image(file: UploadFile = File(...), note_id: str = Query(...)):
    # ... 验证逻辑 ...
    # 确保 note_id 对应的文件夹存在（如果不存在则创建）
    note_dir = image_manager.create_note_folder(note_id)
    # ... 保存文件 ...
```

**新增 #1：清理端点**
```python
@router.post("/cleanup-images")
def cleanup_images(note_id: str = Query(...), content_md: str = Query("")):
    """清理 note 中未被引用的图片（手动触发）"""
    deleted_files = image_manager.cleanup_unused_images(note_id, content_md)
    return {
        "note_id": note_id,
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files
    }
```

**新增 #2：查询端点**
```python
@router.get("/images/{note_id}")
def get_note_images(note_id: str, content_md: str = Query("")):
    """查询 note 的图片信息（所有、被引用、未被引用的图片列表）"""
    # 返回详细的图片统计信息
```

## API 接口

### 1. 创建 Note
**Endpoint:** `POST /api/orbit/notes`
- 自动创建对应的图片文件夹
- 返回 Note 信息（包括 ID）

### 2. 上传图片
**Endpoint:** `POST /api/orbit/uploads`
- **参数：**
  - `file`: 图片文件
  - `note_id`: Note 的 ID（Query 参数）
- 自动确保文件夹存在
- 返回图片 URL：`/uploads/{note_id}/{filename}`

### 3. 更新 Note
**Endpoint:** `PUT /api/orbit/notes/{note_id}`
- 自动清理未被引用的图片

### 4. 删除 Note
**Endpoint:** `DELETE /api/orbit/notes/{note_id}`
- 自动删除整个图片文件夹

### 5. 查询图片状态
**Endpoint:** `GET /api/orbit/images/{note_id}`
- **Query 参数：**
  - `content_md`（可选）: Note 的 markdown 内容
- **返回示例：**
```json
{
  "note_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_images": 5,
  "all_images": ["abc123.png", "def456.jpg", ...],
  "referenced_count": 3,
  "referenced_images": ["abc123.png", "def456.jpg", ...],
  "unreferenced_count": 2,
  "unreferenced_images": ["xyz789.png", ...]
}
```

### 6. 手动清理未被引用的图片
**Endpoint:** `POST /api/orbit/cleanup-images`
- **Query 参数：**
  - `note_id`: Note 的 ID
  - `content_md`（可选）: Note 的 markdown 内容
- **返回示例：**
```json
{
  "note_id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted_count": 2,
  "deleted_files": ["xyz789.png", "old_image.jpg"]
}
```

## 目录结构

```
storage/orbit_uploads/
├── 550e8400-e29b-41d4-a716-446655440000/  (Note ID 文件夹)
│   ├── a1b2c3d4e5f6g7h8.png
│   ├── b2c3d4e5f6g7h8i9.jpg
│   └── c3d4e5f6g7h8i9j0.gif
├── 660e8400-e29b-41d4-a716-446655440001/
│   ├── d4e5f6g7h8i9j0k1.png
│   └── e5f6g7h8i9j0k1l2.webp
└── 770e8400-e29b-41d4-a716-446655440002/
    └── f6g7h8i9j0k1l2m3.jpeg
```

## 工作流程

### 场景 1：创建新 Note 并上传图片

```
1. 前端调用 POST /api/orbit/notes
   → 后端创建 Note（获得 ID）
   → 自动创建 {UPLOAD_DIR}/{note_id}/ 文件夹
   → 返回 Note ID 给前端

2. 前端调用 POST /api/orbit/uploads?note_id={note_id}
   → 后端确保文件夹存在（已存在则跳过）
   → 保存图片到 {UPLOAD_DIR}/{note_id}/{filename}
   → 返回 URL: /uploads/{note_id}/{filename}

3. 前端在编辑器中插入图片
   → markdown: ![alt](/uploads/{note_id}/{filename})

4. 前端调用 PUT /api/orbit/notes/{note_id}（更新内容）
   → 后端自动清理未被引用的图片
   → 保存 Note 内容
```

### 场景 2：编辑 Note 并删除图片引用

```
1. 用户从 Note 中删除某个图片的引用
   → markdown 内容不再包含该图片 URL

2. 前端调用 PUT /api/orbit/notes/{note_id}
   → 后端收到新的 content_md

3. ImageManager 自动：
   → 解析 content_md，提取所有被引用的图片
   → 比对文件夹中的所有图片
   → 删除未被引用的图片
```

### 场景 3：删除 Note

```
1. 前端调用 DELETE /api/orbit/notes/{note_id}
   → 后端从数据库删除 Note 记录
   → 自动删除整个 {UPLOAD_DIR}/{note_id}/ 文件夹
   → 返回 204 No Content
```

## 核心算法

### 提取被引用图片

```python
def extract_referenced_images(content_md: str) -> Set[str]:
    """
    支持的格式：
    1. Markdown: ![alt text](url)
    2. Markdown: ![](url)
    3. HTML: <img src="url">
    4. HTML: <img src='url'>
    5. HTML: <img src=url>

    URL 格式：
    - /uploads/{note_id}/{filename}
    - uploads/{note_id}/{filename}
    - http://domain/uploads/{note_id}/{filename}
    """
    # 使用正则表达式提取 URL
    # 从 URL 中提取文件名
    # 返回文件名集合
```

## 性能考虑

1. **文件夹创建**：幂等操作，使用 `mkdir(parents=True, exist_ok=True)`
2. **图片解析**：O(n) 其中 n 是 content_md 长度，使用正则表达式优化
3. **未使用图片清理**：O(m) 其中 m 是文件夹中的文件数
4. **磁盘占用**：自动清理确保不会出现孤立图片

## 错误处理

1. **缺少 note_id**：返回 400 Bad Request
2. **无效的文件类型**：返回 400 Bad Request（上传时）
3. **文件夹不存在**：自动创建（不抛出错误）
4. **文件读写错误**：捕获异常并记录日志

## 扩展功能建议

### 可选功能 1：图片引用计数数据库

```python
# 新建表 orbit_image_references
class ImageReference(Base):
    id: UUID
    note_id: UUID (FK)
    filename: str
    referenced_at: datetime

    __table_args__ = (
        UniqueConstraint('note_id', 'filename'),
    )
```

**优势：**
- 快速查询图片引用
- 支持图片搜索和统计
- 可以实现"哪些 Note 使用了此图片"的功能

### 可选功能 2：图片版本控制

```python
# 存储结构变更为：
storage/orbit_uploads/
├── {note_id}/
│   ├── current/  (当前版本)
│   │   ├── image1.png
│   │   └── image2.jpg
│   └── archived/  (存档版本)
│       └── 2025-10-30_v1/
│           ├── image1.png
│           └── image2_old.jpg
```

### 可选功能 3：定期清理任务

```python
# 使用 APScheduler 或 Celery
@scheduler.scheduled_job('cron', hour=2)
def cleanup_orphaned_images():
    """每天凌晨 2 点清理孤立图片"""
    # 检查所有 Note
    # 清理未被引用的图片
```

## 测试建议

### 单元测试

1. **ImageManager 单元测试**
   - 测试 URL 解析
   - 测试 markdown 图片提取
   - 测试文件操作

2. **集成测试**
   - 创建 Note → 上传图片 → 验证文件夹结构
   - 删除引用 → 更新 Note → 验证文件被删除
   - 删除 Note → 验证文件夹被删除

### 手动测试检查表

- [ ] 创建 Note 自动生成文件夹
- [ ] 上传图片正确分类到对应文件夹
- [ ] 上传文件时自动生成 UUID 文件名
- [ ] 删除 Note 清理文件夹
- [ ] 更新 Note 删除未被引用的图片
- [ ] 多张图片的正确处理
- [ ] 边界情况：空文件夹、无效 URL 等

## 迁移策略（如果有现存图片）

如果系统中已有上传的图片，需要迁移到新的目录结构：

```python
def migrate_images_to_new_structure():
    """
    从 {UPLOAD_DIR}/{filename}
    迁移到 {UPLOAD_DIR}/{note_id}/{filename}
    """
    # 1. 扫描所有 Note
    # 2. 对每个 Note，解析 content_md 找出图片
    # 3. 创建对应的文件夹
    # 4. 移动图片到新位置
    # 5. 更新 content_md 中的图片 URL
    # 6. 清理旧图片文件
```

## 总结

这个图片管理系统提供了：

✅ **自动化**：自动创建文件夹、清理未使用图片
✅ **组织性**：按 Note ID 分类，结构清晰
✅ **追踪性**：完整的图片引用关系管理
✅ **可靠性**：异常处理和幂等操作
✅ **可扩展性**：为未来功能预留接口

系统确保每个 Note 的图片相互隔离，删除 Note 时能够自动清理相关资源，不会产生孤立文件。
