# Tags System Migration Guide
## 标签系统迁移指南

### 概述
本指南说明如何执行 Wordloom Orbit 标签系统的数据库迁移，将现有的 `orbit_notes.tags` 文本数组迁移到独立的表结构。

### 前置条件
- PostgreSQL 服务器正在运行
- 已连接到 `wordloomorbit` 数据库
- Python 3.8+ 已安装
- 所有依赖包已安装（SQLAlchemy, psycopg2 等）

### 步骤 1: 设置环境变量

**Windows (PowerShell):**
```powershell
$env:ORBIT_DB_URL = "postgresql+psycopg://postgres:pgpass@127.0.0.1:5433/wordloomorbit"
```

**Windows (CMD):**
```cmd
set ORBIT_DB_URL=postgresql+psycopg://postgres:pgpass@127.0.0.1:5433/wordloomorbit
```

**Linux/macOS:**
```bash
export ORBIT_DB_URL="postgresql+psycopg://postgres:pgpass@127.0.0.1:5433/wordloomorbit"
```

### 步骤 2: 执行迁移脚本

从 `WordloomBackend/api` 目录运行以下命令：

```bash
# 使用 Python 执行迁移脚本
python migrate_tags_system.py
```

**预期输出:**
```
📂 Reading migration from: /path/to/migrations/001_create_tags_system.sql
📊 Connecting to database: postgresql+psycopg://...
[1/28] Executing: CREATE TABLE IF NOT EXISTS orbit_tags...
[2/28] Executing: CREATE TABLE IF NOT EXISTS orbit_note_tags...
...
✅ Successfully executed 28 migration statements!

🎉 Tags system migration completed successfully!
📋 The following tables were created/updated:
   - orbit_tags: 存储标签信息（名称、颜色、描述、计数）
   - orbit_note_tags: 多对多关联表（note 与 tag 的关系）
   - Indexes created for performance optimization

✨ Your data has been migrated from orbit_notes.tags array to the new structure.
```

### 步骤 3: 验证迁移

可选：验证迁移是否成功。使用 PostgreSQL 客户端连接到数据库并执行以下查询：

```sql
-- 查看创建的标签
SELECT COUNT(*) as total_tags FROM orbit_tags;

-- 查看每个标签的使用情况
SELECT name, count, color FROM orbit_tags ORDER BY count DESC LIMIT 10;

-- 查看某个 Note 的所有标签
SELECT n.id, n.title, array_agg(t.name) as tags
FROM orbit_notes n
LEFT JOIN orbit_note_tags nt ON n.id = nt.note_id
LEFT JOIN orbit_tags t ON nt.tag_id = t.id
WHERE n.id = '某个-note-id'
GROUP BY n.id, n.title;
```

### 步骤 4: 重启后端服务

迁移完成后，重启 Orbit API 服务器以加载新的模型：

```bash
# 停止当前的服务器（如果运行中）
Ctrl+C

# 重启服务器
python -m uvicorn app.main_orbit:app --host 0.0.0.0 --port 8012 --reload
```

### 步骤 5: 重启前端开发服务器

可选：如果前端已经在运行，可能需要清除缓存并重启：

```bash
# 在前端目录 (WordloomFrontend/next)
npm run dev
# 或
pnpm dev
```

### 文件变更总结

**后端:**
- ✅ `/app/models/orbit/tags.py` - 新增：标签模型
- ✅ `/app/routers/orbit/tags.py` - 新增：标签 API 端点
- ✅ `/app/routers/orbit/notes.py` - 修改：更新查询逻辑加载标签关系
- ✅ `/app/database_orbit.py` - 修改：导入新的标签模型
- ✅ `/app/main_orbit.py` - 修改：包含标签 API 路由
- ✅ `/migrations/001_create_tags_system.sql` - 新增：数据库迁移脚本
- ✅ `/migrate_tags_system.py` - 新增：Python 迁移执行器

**前端:**
- ✅ `/domain/notes.ts` - 修改：添加 Tag 类型和 tagsRel 字段
- ✅ `/domain/api.ts` - 修改：更新 RawNote 和转换函数
- ✅ `/domain/tags.ts` - 新增：标签 API 客户端函数
- ✅ `/ui/TagColorPicker.tsx` - 新增：颜色选择器组件
- ✅ `/ui/TagManagementPanel.tsx` - 新增：标签管理界面

### 备份和回滚

如需备份或回滚，可以使用以下 SQL（在执行迁移前执行）：

```sql
-- 备份原始 tags 数据（可选）
ALTER TABLE orbit_notes RENAME COLUMN tags TO tags_backup;

-- 如需恢复
ALTER TABLE orbit_notes RENAME COLUMN tags_backup TO tags;
```

### 常见问题

**Q: 迁移过程中出现连接错误？**
A: 确保 PostgreSQL 服务器正在运行，检查数据库连接字符串。

**Q: 迁移后标签没有显示颜色？**
A: 颜色值已默认设置为灰色（#808080）。可以通过 TagManagementPanel 或 API 更新颜色。

**Q: 如何添加新标签？**
A: 使用新的标签 API 端点或通过编辑页面的 TagManagementPanel 添加标签。

**Q: 旧的 `tags` 字段还会用到吗？**
A: 为了向后兼容，旧的 `tags` 字段仍然保存，但建议逐步迁移到使用 `tags_rel`。

### 支持

如有问题，请参考：
- 后端 API 文档：`/docs` (Swagger UI)
- 前端组件文档：见各组件文件注释
- 数据库架构：见 `001_create_tags_system.sql`

---

**迁移日期**: $(date)
**版本**: 1.0.0
**状态**: 准备就绪
