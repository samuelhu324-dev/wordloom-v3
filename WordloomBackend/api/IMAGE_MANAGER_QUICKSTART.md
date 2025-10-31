# Wordloom Orbit 图片管理系统 - 快速使用指南

## 文件清单

已创建/修改的文件：

### 新创建文件
1. **`app/core/image_manager.py`** - 核心图片管理模块
   - 提供 ImageManager 类处理所有图片生命周期操作

2. **`app/core/__init__.py`** - 模块初始化文件
   - 导出 ImageManager 供其他模块使用

3. **`IMAGE_MANAGER_DOCUMENTATION.md`** - 完整文档
   - 详细的设计、API、工作流程说明

### 修改的文件
1. **`app/routers/orbit/notes.py`**
   - 导入 ImageManager
   - `create_note()`: 创建 Note 时自动创建图片文件夹
   - `delete_note()`: 删除 Note 时自动清理图片文件夹
   - `update_note()`: 更新 Note 时清理未被引用的图片

2. **`app/routers/orbit/uploads.py`**
   - 导入 ImageManager
   - `upload_image()`: 改用 ImageManager 确保文件夹存在
   - `cleanup_images()`（新增）: 手动清理未被引用的图片
   - `get_note_images()`（新增）: 查询图片状态信息

## 核心特性

### 1️⃣ 自动文件夹创建
创建 Note 时自动在 `storage/orbit_uploads/` 下创建对应的文件夹：
```
storage/orbit_uploads/{note_id}/
```

### 2️⃣ 自动图片分类
上传的图片自动存储到对应 Note 的文件夹：
```
storage/orbit_uploads/{note_id}/{uuid_filename}.{ext}
```

### 3️⃣ 引用追踪
从 markdown 内容中自动提取被引用的图片：
- 支持 `![alt](url)` 格式
- 支持 `<img src="url">` 格式
- 支持多种 URL 格式

### 4️⃣ 自动清理
- **删除 Note**：自动删除整个图片文件夹
- **更新 Note**：自动删除未被引用的图片

### 5️⃣ 灵活查询
提供 API 查询图片状态，了解哪些图片被引用、哪些未被引用

## API 快速参考

### 创建 Note（自动创建文件夹）
```bash
curl -X POST http://localhost:8011/api/orbit/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Note",
    "content_md": "Initial content"
  }'
```
**返回：** Note ID（文件夹已创建）

### 上传图片到 Note
```bash
curl -X POST http://localhost:8011/api/orbit/uploads \
  -F "file=@image.png" \
  -F "note_id=550e8400-e29b-41d4-a716-446655440000"
```
**返回：** 图片 URL `/uploads/{note_id}/{filename}`

### 更新 Note 内容（自动清理未用图片）
```bash
curl -X PUT http://localhost:8011/api/orbit/notes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "content_md": "Updated content with ![alt](/uploads/550e8400.../image1.png)"
  }'
```
**效果：** 自动删除未被引用的旧图片

### 删除 Note（自动清理所有图片）
```bash
curl -X DELETE http://localhost:8011/api/orbit/notes/550e8400-e29b-41d4-a716-446655440000
```
**效果：** Note 和对应的图片文件夹被删除

### 查询图片状态
```bash
curl "http://localhost:8011/api/orbit/images/550e8400-e29b-41d4-a716-446655440000?content_md=..."
```
**返回：** 所有图片、被引用图片、未被引用图片的信息

### 手动清理未被引用的图片
```bash
curl -X POST http://localhost:8011/api/orbit/cleanup-images \
  -H "Content-Type: application/json" \
  -d '{
    "note_id": "550e8400-e29b-41d4-a716-446655440000",
    "content_md": "..."
  }'
```
**返回：** 被删除的文件列表

## 工作流程示例

### 场景：创建笔记并添加图片

```
步骤 1: 创建笔记
  POST /api/orbit/notes
  ↓
  后端自动创建: storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/

步骤 2: 上传第一张图片
  POST /api/orbit/uploads?note_id=550e8400-e29b-41d4-a716-446655440000
  ↓
  文件保存到: storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/a1b2c3d4.png
  返回 URL: /uploads/550e8400-e29b-41d4-a716-446655440000/a1b2c3d4.png

步骤 3: 上传第二张图片
  POST /api/orbit/uploads?note_id=550e8400-e29b-41d4-a716-446655440000
  ↓
  文件保存到: storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/b2c3d4e5.jpg

步骤 4: 更新笔记内容（包含两张图片）
  PUT /api/orbit/notes/550e8400-e29b-41d4-a716-446655440000
  content_md = "![img1](/uploads/550e8400-.../a1b2c3d4.png) ![img2](/uploads/550e8400-.../b2c3d4e5.jpg)"
  ↓
  后端检查所有图片是否被引用 ✓ 都被引用，无需清理

步骤 5: 编辑笔记，删除对第二张图片的引用
  PUT /api/orbit/notes/550e8400-e29b-41d4-a716-446655440000
  content_md = "![img1](/uploads/550e8400-.../a1b2c3d4.png)"
  ↓
  后端自动删除未被引用的图片: b2c3d4e5.jpg ❌

步骤 6: 删除笔记
  DELETE /api/orbit/notes/550e8400-e29b-41d4-a716-446655440000
  ↓
  整个文件夹被删除: storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/ ❌
```

## 目录结构变化

### 之前
```
storage/orbit_uploads/
├── a1b2c3d4.png         （图片名无规律）
├── b2c3d4e5.jpg
├── c3d4e5f6.gif
└── ...                  （所有图片混在一起）
```

### 之后（新系统）
```
storage/orbit_uploads/
├── 550e8400-e29b-41d4-a716-446655440000/
│   ├── a1b2c3d4.png     （只属于这个 Note）
│   └── b2c3d4e5.jpg
├── 660e8400-e29b-41d4-a716-446655440001/
│   ├── c3d4e5f6.gif
│   └── d4e5f6g7.webp
└── 770e8400-e29b-41d4-a716-446655440002/
    └── e5f6g7h8.jpeg
```

## 主要改进

| 功能 | 之前 | 现在 |
|------|------|------|
| 文件夹创建 | 手动 | ✅ 自动 |
| 图片分类 | 混乱 | ✅ 按 Note ID 组织 |
| 删除图片 | 手动 | ✅ 自动 |
| 引用追踪 | 无 | ✅ 自动解析 markdown |
| Note 删除 | 图片残留 | ✅ 自动清理 |
| 孤立文件 | 可能出现 | ✅ 自动清理 |

## 配置说明

系统使用的环境变量（来自 `app/database_orbit.py`）：

```python
ORBIT_UPLOAD_DIR = os.getenv("ORBIT_UPLOAD_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "storage", "orbit_uploads")
)
```

**默认位置：** `{项目根}/storage/orbit_uploads/`

**自定义位置：** 设置环境变量 `ORBIT_UPLOAD_DIR=/custom/path`

## 调试和监控

### 查看日志
上传、删除、清理操作会输出日志：
```
[2025-10-30 14:23:45] 创建文件夹: storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/
[2025-10-30 14:24:12] 删除文件: b2c3d4e5.jpg
[2025-10-30 14:25:00] 删除文件夹: storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/
```

### 调试 API
使用 GET `/api/orbit/images/{note_id}` 查看详细信息：
```bash
curl "http://localhost:8011/api/orbit/images/550e8400-e29b-41d4-a716-446655440000?content_md=..."
```

返回包含：
- 所有图片文件名
- 被引用的图片
- 未被引用的图片

## 常见问题

### Q: 如果不小心删除了被引用的图片怎么办？
A: 图片只能通过 Note 的 markdown 内容引用。删除图片的唯一方式是：
1. 从 markdown 中移除图片引用
2. 调用 `PUT` 更新 Note
3. 自动清理机制会删除未被引用的图片

### Q: 能否恢复已删除的图片？
A: 不能。已删除的图片不可恢复。建议定期备份 `storage/orbit_uploads/` 目录。

### Q: 如何处理已有的旧图片？
A: 需要执行迁移脚本。详见文档中的"迁移策略"部分。

### Q: 多个 Note 能否共享一张图片？
A: 当前设计中不支持。每张图片属于单一 Note。如果需要共享，建议：
1. 在第二个 Note 中重新上传一份副本
2. 或者未来实现图片引用表来支持多 Note 引用

### Q: 是否支持图片编辑/替换？
A: 当前不支持。替换图片的方法：
1. 上传新图片
2. 在 markdown 中更新引用 URL
3. 旧图片会被自动清理

## 后续优化建议

1. **添加图片压缩功能** - 上传时自动压缩大图片
2. **添加生成缩略图** - 加快图片加载速度
3. **添加图片搜索功能** - 查找使用特定图片的所有 Note
4. **添加定期清理任务** - 防止孤立文件积累
5. **添加配额管理** - 限制每个 Note 的图片总大小

## 支持

如有问题，请查看完整文档：`IMAGE_MANAGER_DOCUMENTATION.md`
