# 🚀 Wordloom Orbit 图片管理系统 - 开始使用

**最后更新：** 2025-10-30
**版本：** 1.0 MVP
**状态：** ✅ 立即可用

---

## ⚡ 快速开始（3 步）

### 第 1 步：验证系统是否工作

```bash
cd WordloomBackend/api
python test_image_manager.py
```

**预期结果：** 看到绿色的 ✓ 标记，表示系统正常运行

### 第 2 步：查看关键文件

你需要了解的文件：
- `app/core/image_manager.py` - 核心逻辑
- `app/routers/orbit/notes.py` - Note 路由
- `app/routers/orbit/uploads.py` - 上传路由

### 第 3 步：阅读文档

选择一份适合你的文档：
- **只有 5 分钟？** → 读 `IMAGE_MANAGER_QUICKSTART.md`
- **有 15 分钟？** → 读 `IMAGE_MANAGER_DOCUMENTATION.md`
- **想要概览？** → 读 `PROJECT_COMPLETION_REPORT.md`

---

## 📋 系统工作原理

### 自动化流程

```
用户创建 Note
    ↓
后端自动创建 storage/orbit_uploads/{note_id}/ 文件夹
    ↓
用户上传图片
    ↓
后端自动存储到 storage/orbit_uploads/{note_id}/{filename}
    ↓
用户编辑笔记删除图片引用
    ↓
后端自动清理未被引用的图片
    ↓
用户删除 Note
    ↓
后端自动删除整个图片文件夹
```

### 文件存储结构

```
storage/orbit_uploads/
├── 550e8400-e29b-41d4-a716-446655440000/  ← Note ID
│   ├── a1b2c3d4e5f6g7h8.png               ← 图片文件（UUID名称）
│   ├── b2c3d4e5f6g7h8i9.jpg
│   └── c3d4e5f6g7h8i9j0.gif
├── 660e8400-e29b-41d4-a716-446655440001/
│   └── d4e5f6g7h8i9j0k1.webp
└── ...
```

---

## 🔌 API 使用

### 创建 Note（自动创建文件夹）

```bash
curl -X POST http://localhost:8011/api/orbit/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的笔记",
    "content_md": "这是笔记内容"
  }'
```

**响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "我的笔记",
  "content_md": "这是笔记内容",
  ...
}
```

**发生了什么？**
- ✨ 自动创建了 `storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/` 文件夹

### 上传图片（自动分类）

```bash
curl -X POST http://localhost:8011/api/orbit/uploads \
  -F "file=@my_image.png" \
  -F "note_id=550e8400-e29b-41d4-a716-446655440000"
```

**响应：**
```json
{
  "url": "/uploads/550e8400-e29b-41d4-a716-446655440000/a1b2c3d4e5f6g7h8.png"
}
```

**发生了什么？**
- ✨ 图片自动保存到 `storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/a1b2c3d4e5f6g7h8.png`

### 更新 Note（自动清理未用图片）

```bash
curl -X PUT http://localhost:8011/api/orbit/notes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "content_md": "更新的内容\n\n![图片](/uploads/550e8400-e29b-41d4-a716-446655440000/a1b2c3d4e5f6g7h8.png)"
  }'
```

**发生了什么？**
- ✨ 后端自动解析 markdown，检测图片引用
- ✨ 删除文件夹中未被引用的其他图片

### 删除 Note（自动删除文件夹）

```bash
curl -X DELETE http://localhost:8011/api/orbit/notes/550e8400-e29b-41d4-a716-446655440000
```

**发生了什么？**
- ✨ Note 从数据库中删除
- ✨ 整个 `storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/` 文件夹被删除

### 查询图片状态（调试用）

```bash
curl "http://localhost:8011/api/orbit/images/550e8400-e29b-41d4-a716-446655440000?content_md=..."
```

**响应：**
```json
{
  "note_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_images": 3,
  "all_images": ["a1b2c3d4.png", "b2c3d4e5.jpg", "c3d4e5f6.gif"],
  "referenced_count": 2,
  "referenced_images": ["a1b2c3d4.png", "b2c3d4e5.jpg"],
  "unreferenced_count": 1,
  "unreferenced_images": ["c3d4e5f6.gif"]
}
```

---

## 💻 代码集成点

### 在 notes.py 中的 3 个修改

**修改 1: 导入**
```python
from app.core.image_manager import ImageManager
image_manager = ImageManager(ORBIT_UPLOAD_DIR)
```

**修改 2: 创建 Note 时**
```python
@router.post("/notes")
def create_note(...):
    # 创建 Note 的数据库记录
    ...
    # 自动创建文件夹
    image_manager.create_note_folder(str(n.id))  # ← 新增
    return n
```

**修改 3: 删除 Note 时**
```python
@router.delete("/notes/{note_id}")
def delete_note(...):
    # 删除数据库记录
    ...
    # 自动删除文件夹
    image_manager.delete_note_folder(note_id)  # ← 新增
```

**修改 4: 更新 Note 时**
```python
@router.put("/notes/{note_id}")
def update_note(...):
    # 更新数据库记录
    ...
    # 自动清理未被引用的图片
    image_manager.cleanup_unused_images(note_id, n.content_md)  # ← 新增
    return n
```

### 在 uploads.py 中的改动

**改进：上传图片时**
```python
@router.post("/uploads")
async def upload_image(...):
    # 改为使用 ImageManager 创建文件夹
    note_dir = image_manager.create_note_folder(note_id)  # ← 改进
    # 保存图片
    dest = note_dir / name
    dest.write_bytes(await file.read())
    ...
```

**新增：查询图片状态**
```python
@router.get("/images/{note_id}")
def get_note_images(note_id: str, content_md: str = Query("")):
    # 返回图片统计信息
    ...
```

**新增：手动清理**
```python
@router.post("/cleanup-images")
def cleanup_images(note_id: str = Query(...), content_md: str = Query("")):
    # 手动触发清理
    ...
```

---

## 🧪 测试系统

### 运行完整测试

```bash
cd WordloomBackend/api
python test_image_manager.py
```

### 测试将验证

- ✅ 创建 Note 自动创建文件夹
- ✅ 上传图片正确分类
- ✅ 查询图片状态信息
- ✅ 更新 Note 并保存引用
- ✅ 自动清理未被引用的图片
- ✅ 删除 Note 清理文件夹

---

## 📊 监控和调试

### 查看文件夹结构

```bash
# Windows
dir storage\orbit_uploads /s /b

# Linux/Mac
find storage/orbit_uploads -type f
```

### 查看日志

系统会输出操作日志：
```
[创建] storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/
[上传] 保存到 storage/orbit_uploads/.../image1.png
[清理] 删除 storage/orbit_uploads/.../unused_image.jpg
[删除] 删除文件夹 storage/orbit_uploads/550e8400-e29b-41d4-a716-446655440000/
```

### API 调用验证

```bash
# 1. 创建 Note 并获取 ID
curl -X POST http://localhost:8011/api/orbit/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"test"}'

# 2. 查询图片状态
curl "http://localhost:8011/api/orbit/images/{note_id}"

# 3. 手动清理
curl -X POST http://localhost:8011/api/orbit/cleanup-images \
  -d "note_id={note_id}"
```

---

## ⚙️ 配置

### 默认上传目录

```python
ORBIT_UPLOAD_DIR = storage/orbit_uploads/  # 相对于项目根目录
```

### 自定义上传目录

```bash
# 在 .env 文件中设置
export ORBIT_UPLOAD_DIR=/custom/path/to/uploads
```

---

## 🔒 安全考虑

- ✅ **UUID 文件名** - 防止路径遍历攻击
- ✅ **类型验证** - 仅允许特定图片格式（PNG, JPG, GIF, WebP, SVG）
- ✅ **ID 验证** - 检查 Note ID 有效性
- ✅ **异常处理** - 所有错误都被妥善处理

---

## 🎯 常见任务

### 任务 1: 检查某个 Note 有多少张图片

```bash
curl "http://localhost:8011/api/orbit/images/550e8400-e29b-41d4-a716-446655440000"
```

**查看返回的：** `total_images` 字段

### 任务 2: 找出未被引用的图片

```bash
curl "http://localhost:8011/api/orbit/images/550e8400-e29b-41d4-a716-446655440000?content_md=..."
```

**查看返回的：** `unreferenced_images` 数组

### 任务 3: 手动清理未使用的图片

```bash
curl -X POST http://localhost:8011/api/orbit/cleanup-images \
  -d "note_id=550e8400-e29b-41d4-a716-446655440000" \
  -d "content_md=..."
```

**查看返回的：** `deleted_files` 列表

### 任务 4: 删除某个 Note 及其所有图片

```bash
curl -X DELETE http://localhost:8011/api/orbit/notes/550e8400-e29b-41d4-a716-446655440000
```

**自动清理所有关联图片**

---

## 📚 进阶阅读

### 想要深入了解？

| 文档 | 适合 | 内容 |
|------|------|------|
| `IMAGE_MANAGER_QUICKSTART.md` | 快速入门 | 功能概览、API 参考、常见问题 |
| `IMAGE_MANAGER_DOCUMENTATION.md` | 深入学习 | 系统设计、算法、最佳实践 |
| `IMPLEMENTATION_SUMMARY.md` | 项目理解 | 代码修改、架构设计决策 |
| `PROJECT_COMPLETION_REPORT.md` | 完整总结 | 项目成果、测试覆盖、后续计划 |
| `CHANGELOG.md` | 版本历史 | 版本信息、升级指南 |

---

## 🆘 故障排除

### 问题 1: 上传图片后看不到文件

**解决方案：**
1. 检查 `storage/orbit_uploads/` 目录是否存在
2. 查看上传时返回的 URL 中的 note_id 是否正确
3. 运行测试脚本确认系统工作

### 问题 2: 删除 Note 后文件夹仍然存在

**解决方案：**
1. 确保使用的是 DELETE 请求，而不是 PUT
2. 检查 note_id 是否完全正确
3. 查看是否有权限问题

### 问题 3: 图片无法被自动清理

**解决方案：**
1. 验证 content_md 中的 URL 格式是否正确
2. 确保 markdown 格式正确：`![alt](/uploads/{note_id}/{filename})`
3. 运行查询端点检查图片状态

### 问题 4: 后端无法启动

**解决方案：**
1. 检查 Python 版本 (需要 3.9+)
2. 确保所有依赖已安装：`pip install -r requirements.txt`
3. 检查 `storage/` 目录是否存在并可写

---

## ✨ 性能提示

- 💡 **大量图片？** 系统支持无限数量，但文件系统性能会受影响
- 💡 **频繁更新？** 清理操作很快（O(m)，m = 文件夹中的文件数）
- 💡 **大文件？** 建议在前端进行压缩，后端只验证大小

---

## 🎓 学习路径

### Day 1: 理解系统
- [ ] 读 `IMAGE_MANAGER_QUICKSTART.md`（5 分钟）
- [ ] 运行 `test_image_manager.py`（2 分钟）
- [ ] 查看 `app/core/image_manager.py`（10 分钟）

### Day 2: 集成到前端
- [ ] 检查前端上传代码
- [ ] 确保传递 `note_id` 参数
- [ ] 测试上传和引用流程

### Day 3: 生产环境
- [ ] 配置上传目录
- [ ] 设置备份策略
- [ ] 监控磁盘空间

---

## 🎉 你已准备好了！

系统现在已经完全集成到你的 Wordloom Orbit 项目中。

✅ **后端：** 自动化图片管理已实现
✅ **文档：** 完整的文档已提供
✅ **测试：** 自动化测试脚本已准备
✅ **支持：** 常见问题和故障排除已覆盖

**现在就开始使用吧！** 🚀

---

**需要帮助？** 查看相应的文档或运行测试脚本。

*最后更新：2025-10-30*
