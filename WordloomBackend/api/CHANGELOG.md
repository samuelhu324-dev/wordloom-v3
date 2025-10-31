# Wordloom Orbit 图片管理系统 - 变更日志

## 版本 1.0 (2025-10-30)

### 🎉 首次发布

#### 新功能
- ✅ 自动图片文件夹创建（按 Note ID）
- ✅ 自动图片引用追踪（支持 markdown 和 HTML 格式）
- ✅ 自动清理未被引用的图片
- ✅ 自动级联删除 Note 时的图片文件夹
- ✅ 图片状态查询 API
- ✅ 手动清理触发端点

#### 新增文件

**核心模块：**
- `app/core/image_manager.py` - ImageManager 类（209 行）
  - `create_note_folder()` - 创建 Note 对应的图片文件夹
  - `delete_note_folder()` - 删除 Note 的整个图片文件夹
  - `extract_referenced_images()` - 从 markdown 中提取被引用的图片
  - `get_unused_images()` - 获取未被引用的图片
  - `cleanup_unused_images()` - 清理未被引用的图片

- `app/core/__init__.py` - 模块初始化

**文档：**
- `IMAGE_MANAGER_DOCUMENTATION.md` - 完整技术文档（380+ 行）
- `IMAGE_MANAGER_QUICKSTART.md` - 快速开始指南（200+ 行）
- `IMPLEMENTATION_SUMMARY.md` - 实现总结
- `CHANGELOG.md` - 本文件

**测试：**
- `test_image_manager.py` - 自动化测试脚本

#### 修改的文件

**app/routers/orbit/notes.py**
- 导入 `ImageManager` 和 `ORBIT_UPLOAD_DIR`
- `create_note()` - 添加自动创建文件夹逻辑
- `delete_note()` - 添加自动清理文件夹逻辑
- `update_note()` - 添加自动清理未被引用图片逻辑

**app/routers/orbit/uploads.py**
- 导入 `ImageManager`
- `upload_image()` - 改为使用 `ImageManager` 创建文件夹
- 新增 `cleanup_images()` - POST 端点，手动清理图片
- 新增 `get_note_images()` - GET 端点，查询图片信息

#### API 端点

**现有端点增强：**
- `POST /api/orbit/notes` - 自动创建图片文件夹
- `PUT /api/orbit/notes/{id}` - 自动清理未被引用的图片
- `DELETE /api/orbit/notes/{id}` - 自动删除图片文件夹
- `POST /api/orbit/uploads` - 图片自动分类到 note_id 文件夹

**新增端点：**
- `POST /api/orbit/cleanup-images` - 手动清理未被引用的图片
- `GET /api/orbit/images/{note_id}` - 查询图片状态信息

#### 目录结构变化

**之前：**
```
storage/orbit_uploads/
├── a1b2c3d4.png
├── b2c3d4e5.jpg
├── c3d4e5f6.gif
└── ...
```

**现在：**
```
storage/orbit_uploads/
├── {note_id_1}/
│   ├── uuid1.png
│   ├── uuid2.jpg
│   └── uuid3.gif
├── {note_id_2}/
│   └── uuid4.webp
└── {note_id_3}/
    └── uuid5.jpeg
```

#### 核心功能

1. **自动化**
   - Note 创建 → 自动创建文件夹
   - 图片上传 → 自动分类到 note_id 文件夹
   - 内容更新 → 自动清理未被引用的图片
   - Note 删除 → 自动删除文件夹

2. **追踪**
   - 支持 markdown `![alt](url)` 格式
   - 支持 HTML `<img src="url">` 格式
   - 自动提取 URL 中的文件名
   - 支持相对路径和绝对 URL

3. **查询**
   - 获取 Note 的所有图片
   - 获取被引用的图片
   - 获取未被引用的图片
   - 实时统计信息

#### 性能指标

- **文件夹创建：** O(1)
- **图片解析：** O(n)，其中 n = content_md 长度
- **未使用图片清理：** O(m)，其中 m = 文件夹中的文件数
- **磁盘占用：** 自动清理，无孤立文件

#### 兼容性

- Python 3.9+
- FastAPI 0.100+
- SQLAlchemy 2.0+
- 支持 PostgreSQL + psycopg

#### 已知限制

1. 当前版本不支持多 Note 共享图片（可在未来版本实现）
2. 不支持图片版本控制（可在未来版本实现）
3. 不支持图片编辑/替换（需要重新上传新文件）
4. 没有配额管理（可在未来版本实现）

#### 测试覆盖

✅ 单元测试 - ImageManager 类所有方法
✅ 集成测试 - 完整工作流
✅ 边界情况 - 空文件夹、无效 URL 等
✅ 错误处理 - 异常捕获和日志记录

#### 文档

- ✅ 完整的技术文档（380+ 行）
- ✅ 快速开始指南（200+ 行）
- ✅ API 参考
- ✅ 工作流程示例
- ✅ 常见问题解答
- ✅ 后续优化建议
- ✅ 测试用例

#### 后续改进项目

**优先级高：**
- [ ] 图片压缩功能（上传时自动压缩大于 5MB 的图片）
- [ ] 缩略图生成
- [ ] 定期孤立文件清理任务

**优先级中：**
- [ ] 图片元数据存储
- [ ] 图片搜索功能
- [ ] 配额管理

**优先级低：**
- [ ] 多 Note 共享图片
- [ ] 图片版本控制
- [ ] 访问控制和权限

---

## 版本历史

### 规划中的版本

#### v1.1 (预计 11 月)
- 图片压缩和缩略图生成
- 元数据存储
- 定期清理任务

#### v2.0 (预计 12 月)
- 图片引用关系数据库
- 搜索功能
- 配额管理

#### v3.0 (预计 2026 年 Q1)
- 多 Note 图片共享
- 版本控制
- 权限管理

---

## 升级指南

### 从无图片管理到 v1.0

如果之前有现存图片，需要执行迁移：

1. **停止服务**
   ```bash
   # 停止 Orbit 后端
   ```

2. **备份现有图片**
   ```bash
   cp -r storage/orbit_uploads storage/orbit_uploads.backup
   ```

3. **执行迁移脚本**（未来版本提供）
   ```bash
   python migrate_images_to_v1.py
   ```

4. **验证迁移**
   ```bash
   python test_image_manager.py
   ```

5. **启动服务**
   ```bash
   # 启动 Orbit 后端
   ```

---

## 贡献指南

### 报告 bug

使用 GitHub Issues，包含：
- 复现步骤
- 预期结果
- 实际结果
- 日志信息

### 功能建议

欢迎提交 PR，包含：
- 详细的功能描述
- 测试用例
- 文档更新

---

## 许可证

同主项目 Wordloom

---

## 致谢

感谢所有贡献者和用户的支持！

---

**最后更新：2025-10-30**
