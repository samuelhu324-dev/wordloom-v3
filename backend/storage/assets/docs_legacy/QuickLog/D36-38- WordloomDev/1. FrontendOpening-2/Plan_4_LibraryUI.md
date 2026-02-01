Plan: 多库创建 + 描述封面 + 横向卡片落地
TL;DR: 先修正后端真实支持“多库 + 描述 + 封面”，同步 3 个 RULES 与 ADR，再补前端类型与横向卡片/上传流程。采用增量迁移：删除 user_id 唯一约束→新增 description 与可选 cover_media_id→扩展 UseCase & Router→前端同步字段与新组件。封面走 Media 关联（不重复二进制字段），虚拟 Basement 卡片保持前端合成，后端后续补统计端点。

Steps
数据库迁移: 修改 libraries 表 (移除 user_id UNIQUE → INDEX)、新增 description TEXT NULL、cover_media_id UUID NULL；更新 ORM backend/infra/database/models/library_model.py.
领域/仓储更新: 扩展 library.py 加 description、cover_media_id；调整 Repository 保存/取回逻辑及 ILibraryRepository.
用例与路由: 新建 UpdateLibraryUseCase + 请求/响应模式；修改 POST /libraries 接收 description；新增 PATCH /libraries/{id} 支持 name/description/cover_media_id；列表/详情返回新字段。
前端类型与 API: 更新 types.ts、frontend/src/features/library/api/index.ts 添加 description、cover_media_id、coverUrl；调整创建/更新表单与 LibraryMainWidget.
横向卡片与上传: 新增 LibraryCardHorizontal.tsx + 样式；添加布局切换（水平/网格）；接入 Media 选择/上传 Modal（复用现有媒体 hooks）；展示封面 + 描述截断。
虚拟 Basement 卡片与统计占位: 在 page.tsx 注入虚拟卡片（已存在改为使用真实统计字段占位）；规划后端 /basement/stats（延后实现）字段对齐。
文档同步: 更新 DDD_RULES.yaml (RULE-001 改为“无限库”，新增 Library 描述与封面约束)，HEXAGONAL_RULES.yaml 增加新的端点与端口说明，VISUAL_RULES.yaml 增加横向卡片与封面策略；撰写 ADR-073-library-description-and-cover-integration.md。
验证与测试: 添加后端测试（多库创建/更新/描述持久化/封面关联）、前端组件/集成测试（创建显示、布局切换、上传封面）。
Further Considerations
封面策略: Option A 直接 cover_media_id + 关联查询; Option B 纯 MediaAssociation 查询。推荐 A 简化读取。
描述长度限制: 建议 500 字（RULE-LIB-DESC-001）还是 1000？需确认。
横向布局持久化: localStorage 记忆用户最后选择 (key: wl_libraries_layout)? 是否需要服务端偏好后续再 ADR。