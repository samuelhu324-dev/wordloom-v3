上传/加载现状说明（回答你的三个点）

你刚才在 Library 卡片里“更换封面”所选的图片，确实已经读入浏览器：通过 FileReader 把文件转成 DataURL（base64）后保存在 localStorage('libraryCoverMap:' + library.id)，再即刻用 <img src=...> 渲染。不存在后端请求与媒体存储写入。

例如 Library “A” 上显示的那张图片：来源路径就是本地存储的 DataURL。刷新页面（同一浏览器、未清除 localStorage）会重新读取并渲染；换浏览器 / 清除缓存则不会保留，因为后端没有记录。当前 gradient 封面是备用占位，当无 coverDataUrl 时显示。

加载 / 上传规则目前不是使用原有 Media 模块的正式规则：

没有调用后端 MediaRepository 或 storage.py 中的 save_bookshelf_cover / save_book_cover 等函数（后端只为 Bookshelf/Book cover 预留了目录：bookshelf_covers/, book_covers/，并无 library_covers）。
上传流程无文件类型、大小、维度校验；浏览器读什么就存什么。
无异步压缩、无转码、无权限控制；纯前端实验级实现。
安全与性能：base64 会增大体积 ~33%；大量或超大图会增长 localStorage 占用（普遍浏览器 5MB 左右配额），可能导致后续写入失败。
统计与回滚：删除/替换图片只是覆盖 localStorage，后端不可恢复。

当前实现核心代码要点

读取：localStorage.getItem('libraryCoverMap:' + library.id)
保存：localStorage.setItem('libraryCoverMap:' + library.id, result) （result 是 DataURL）
展示逻辑：若存在 DataURL → <img>；否则显示自定义渐变 + “COVER” 文本。
潜在风险与限制

容量上限：多张高分辨率图（例如几 MB）会逼近 localStorage 限制，引发写入异常（当前代码只 toast “封面保存失败”）。
安全：未做 MIME 验证，理论上可选择任意文件（浏览器会按类型限制图片，但仍建议显式检查）。
不可共享：换设备 / 别的用户不可见，同一库跨用户协作时封面失一致性。
缺少清理策略：没有 TTL 或大小控制，会持续堆积。
建议的下一步演进（若要接入正式 Media 规则）

后端新增 Library 封面保存端点：
POST /api/v1/libraries/{id}/cover → 接受 multipart/form-data (file)。
存储目录：新增 library_covers/；返回 url。
前端改为：
选择文件 → 先做校验（类型 image/jpeg|png|webp、大小上限比如 2MB、维度最大宽高）。
调用上传 API → 得到持久化 URL → 用 URL 替换 DataURL 并写入 React Query 缓存 / 列表实体。
本地仍可临时使用 DataURL 预览（乐观 UI），成功后换成正式 URL。
加入缓存与降级：
后端返回图片时可配置合理的 Cache-Control。
若上传失败：回退到原有封面或默认渐变。
添加清理 / 替换策略：
重复上传时旧文件可选择即时删除或定期后台清理（需要记录引用计数或直接覆盖）。
安全校验：
后端用 Pillow 或类似库验证图片格式，拒绝伪装文件。
限制分辨率（例如宽或高 > 2560 时自动缩放）。
访问控制：
多用户模式恢复后确保封面 URL 仅该库所属用户可访问（若不公有）。
临时改进（保持纯前端但更安全）

增加前端类型/大小判断：
添加错误捕获与 fallback：写入失败 → 不替换封面，只提示。
记录一个简化的版本号或更新时间：libraryCoverMapMeta:{id} = { updatedAt, mime }.
总结一句话
当前封面上传是前端本地 DataURL 存储的试验实现，不走后端 Media 管线；若要正式化需要新增后端 library cover 端点、规范文件校验与缓存策略。

需要我直接给出后端接口草案或前端迁移代码示例？告诉我下一步想做哪块，我可以继续。

---

Plan: 接入后端 Media 规则与封面整合
TL;DR：以后端已存在的全局 /api/v1/media 路由与 SQLAlchemyMediaRepository 为基础，分阶段接入 Library 封面上传功能，替换当前前端 localStorage DataURL 方案；通过 cover_media_id 字段与 Media 关联，实现统一存储与回收站生命周期。同步完善三份规则文件：在 DDD 补齐 Media 聚合与封面策略，在 Hexagonal 明确端口/用例与适配器映射，在 Visual 增加封面加载/失败/交互规范，并预留后续扩展到 Block 图片/视频与全局 Media 管理页的演进路径。

Steps
后端扩展: 在 media_router.py 增加封面专用上传路径（或复用 /images + Query: entity_type=LIBRARY&entity_id），新增 UseCase 组合：上传成功后调用 associate_media_with_entity，并提供获取封面 URL 的简单读取（扩展 DIContainer + Library 查询聚合逻辑）。
库封面更新流程: 前端 LibraryCard.tsx 由 FileReader → 改为 FormData POST /api/v1/media/images，拿到 media.id 后调用 PATCH /api/v1/libraries/{id} 写入 cover_media_id，移除 libraryCoverMap:* 本地存储分支（保留 feature flag 回滚）。
加载显示: 在 types.ts 利用 cover_media_id 请求 /api/v1/media/{id} 得到元数据并生成 coverUrl（后端返回 storage_key → 前端拼接 /api/v1/files/{storage_key} 或未来 CDN）；失败时回退当前 gradient 哈希逻辑。
规则文件更新:
DDD_RULES.yaml Domain 7: Media → 增加聚合说明 + POLICY-MEDIA-UPLOAD-001 (类型/大小/配额) + POLICY-LIBRARY-COVER-ASSOCIATION (单主封面、可置空、删除封面不删 Library)。
HEXAGONAL_RULES.yaml module_media 下补充端口列表（MediaRepository + Upload/Associate/Restore/Purge UseCases）与适配器路径 media_repository_impl.py，新增 Library cover 集成说明与不跨 Domain Service 原则。
VISUAL_RULES.yaml 添加 library_cover_visual_rules（加载 skeleton、失败回退、裁剪 ratio、拖拽上传、最大尺寸提示、权限占位符）。
安全与验证: 后端在 Upload UseCase 内应用 MIME 白名单(JPEG/PNG/WEBP/GIF) + 尺寸/时长/文件大小校验 + 存储配额策略（引用 POLICY-009）；前端限制 file.size 与类型，失败弹 Toast 并不更新 cover_media_id。
分阶段演进: Phase 1 (Library 封面) → Phase 2 (Block 图片/视频块引用 media_id) → Phase 3 (全局 Media 管理/回收站视图 + 分页) → Phase 4 (CDN 缓存 & 自适应压缩)；各阶段追加 ADR：ADR-085-library-cover-media-integration.md 等。
回滚与兼容: 增加前端 feature flag WL_MEDIA_COVER_ENABLED（在 config.ts），关闭时恢复 localStorage 分支；后端保持字段可空，撤回只需停止上传与更新操作。
测试策略: 后端增加单元测试（Upload/Associate/Purge/Restore）与集成测试（test_media_router.py）；前端加 React Query hook 测试与 E2E (上传 → 回退 → 删除)；验证 30 天软删除策略模拟（强制设置 trash_at）。
Further Considerations
封面 URL 获取方式：选 A 直接数据库存储 storage_key 前端拼接；选 B 后端返回签名 URL（私有存储需要）。
图片压缩策略：可选预处理 (server-side Pillow/WebP) 或延迟引入 CDN 自适应；当前建议延后至 Phase 4。
Block 媒体扩展：是否统一使用同一上传端点 + entity_type=BLOCK？若确认需在 DDD/HEXAGONAL 同步策略字段提前预留。