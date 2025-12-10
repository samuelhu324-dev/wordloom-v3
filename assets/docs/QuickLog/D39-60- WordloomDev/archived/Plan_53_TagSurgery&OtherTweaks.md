Plan: 书橱标签总表化 + 状态修复 + 三规与 ADR‑098
TL;DR：把书橱标签彻底接入“Tag 总表 + 嫁接表”模型，让 Bookshelf 与 Library 共用一套标签与 UI；修复 ACTIVE/ARCHIVED 状态与 Pin/Archive 行为；为 Libraries 页的 Lucide 图标补齐 tooltip；最后同步 DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES，并用 ADR‑098 固化决策。下面是具体中文执行计划，供你 / 实现代理逐步落地。

Steps
后端：统一 Tag 数据模型（总表 + 嫁接表）
1.1 复查 backend 中 Tag 相关表和模型（tags 总表 + library_tags / bookshelf_tags 等嫁接表），确认目前是否已经存在 bookshelf_tags；若没有，补充 migration（仅一张中间表，包含 bookshelf_id, tag_id, 唯一约束）。
1.2 在 Domain 层为 Bookshelf 引入“只读 tag 视图”：例如在 DTO 层增加 tag_ids: List[UUID] 与 tags_summary: List[str]，但领域聚合内部只保存关联，不直接保存字符串列表。
1.3 在 Repository / Query 层调整 Bookshelf Dashboard / 详情 DTO 拼装逻辑：

读：通过 JOIN bookshelf_tags ON tags 取出 tag 列表，填充 tag_ids 与 tags_summary；
写：增加一个专门方法用于“全量替换关联标签”，例如 replace_bookshelf_tags(bookshelf_id, tag_ids)，内部先删后插，保持幂等。
后端：设计并固化书橱标签更新 API
2.1 为 Patch 接口设计统一请求体：

方案 A（复用现有 UpdateBookshelf）：PATCH /api/v1/bookshelves/{id} 接受 { name?, tags? }，其中 tags 是 UUID[]（tag_ids），不再接受字符串。
方案 B（专门标签接口）：新增 PUT /api/v1/bookshelves/{id}/tags，body 为 { tag_ids: UUID[] }，语义是“全量替换”。
2.2 在 Application UseCase 中实现对应入口：例如 UpdateBookshelfTagsUseCase 或在 UpdateBookshelfUseCase 中明确处理 tag_ids：
校验所有 tag_ids 必须存在于 Tag 总表；
调用 Repository 的 replace_bookshelf_tags 完成事务性更新。
2.3 更新 API 层 schema（Pydantic / FastAPI）：
DTO 请求类型展示 tag_ids: List[UUID] = []，输出 DTO 明确包含 tag_ids 和 tags_summary；
保证 DDD 约束：“Domain 不关心标签的展示文案”。
前端：对齐 Bookshelf Tag 数据结构与 Library
3.1 在 tag / features 中梳理 Library 的标签组件与 hooks（例如 LibraryTagsRow, useTagSuggestions），提炼一个通用 TagSelector：

统一内部状态为 selectedTagIds: string[]；
展示用 Tag DTO 包含 id, name, color（如有）。
3.2 在 BookshelfDashboardCard / BookshelfDashboardBoard 的 DTO 类型中补齐 tag_ids 与 tags_summary：
用 tag_ids 作为编辑用数据源；
用 tags_summary 和 Library 的 TagChip 样式来渲染书橱行里的标签行（最多 3 个，空态 "-- 无标签 --"）。
3.3 将 Tag 推荐列表改为真正的“总表数据”：复用 Library 那套 /api/v1/tags?scope=bookshelf / scope=library API，只是 scope 不同，避免新增端点。
前端：重构书橱 Tag 编辑对话框（BookshelfTagEditDialog）
4.1 把 Dialog 的内部状态从 string[] → { selectedTagIds: string[], availableTags: TagDTO[] }；
4.2 打开 Dialog 时：

用行 DTO 的 tag_ids 初始化 selectedTagIds；
使用统一 useTagSuggestions(scope='bookshelf') hook 去加载 Tag 总表，映射为 TagChip 列表。
4.3 保存时：
构造请求体：
若采用方案 A：PATCH /api/v1/bookshelves/{id}，body { name, tag_ids: selectedTagIds }；
若采用方案 B：PUT /api/v1/bookshelves/{id}/tags，body { tag_ids: selectedTagIds }；
成功后 invalidate ['bookshelves_dashboard', libraryId]；不在前端手动拼接字符串标签。
4.4 禁止在 Dialog 内“新建标签”：
输入框只做搜索与筛选现有 Tag；
若用户输入一个不存在的关键词，提供“前往 Tag 管理页创建”的跳转链接，但不直接 POST。
前端：统一标签视觉样式（仿书库页）
5.1 提取 Library 标签的 CSS（Tag pill 样式）到共享模块：

在 frontend/src/shared/styles/... 或 entities/tag 下创建 TagPill.module.css（或使用现有）；
包含高度 24px、圆角 999px、边框色 rgba(var(--wl-text-primary), 0.08)、hover 阴影等。
5.2 书橱列表和 Dashboard：
使用同一个 TagPill 组件来渲染 tags 列；
空态显示 -- 无标签 --，颜色使用 --wl-text-tertiary。
5.3 若标签超出 3 个，复用 Library 的“＋N” pill 设计，hover / tooltip 展示完整列表。
书库页 Lucide 图标 tooltip 补齐（Libraries 页面）
6.1 找到 Libraries 列表组件（如 LibraryList.tsx）和卡片组件，列出所有 Lucide 图标（视图数、书架数、编辑次数、删除、置顶、归档等）。
6.2 引入统一的 IconButtonWithTooltip 或统一 Tooltip 组件（如果 Bookshelf Dashboard 已有，就直接复用）：

API：<IconButtonWithTooltip icon={Eye} title="浏览次数｜Views" ariaLabel="最近 7 天浏览 117 次" />；
内部统一设置 title + aria-label，符合 VISUAL_RULES 和 ADR‑097。
6.3 在 Library 列表中把所有裸 IconButton 替换为带 Tooltip 的版本；
6.4 保证 tooltip 文案中英双语（“中文｜English”），并且与 Bookshelf Dashboard 统一命名。
修复 Bookshelf ACTIVE → ARCHIVED 状态变更
7.1 后端：确认 ArchiveBookshelfUseCase / status 字段逻辑：

ACTIVE → ARCHIVED：是否强制取消 pinned（规则建议：归档自动取消置顶）；
ARCHIVED → ACTIVE：是否恢复 pinned，或保持不置顶。
7.2 API：
确认前端用于切换归档的端点签名（例如 POST /api/v1/bookshelves/{id}/archive / /restore），或 PATCH status=archived/active；
修正任何“同时提交 pinned + status”的 payload，确保 Archive/Restore 只改 Status，一切与 Pin 相关的变化通过 Pin UseCase 完成。
7.3 前端：
在 Bookshelf Dashboard 行操作里，确保状态按钮 / 菜单只调用单一的 Archive/Restore mutation；
成功后刷新列表并校验：状态列纯文本从 ACTIVE → ARCHIVED；Pinned 条目数变化符合规则（如自动归零）；
修复任何导致 422 的错误 payload（例如不合法枚举、缺字段）。
规则文件（DDD / HEXAGONAL / VISUAL）更新计划
8.1 DDD_RULES.yaml：

在 POLICIES_ADDED_NOV25 下新增一个 POLICY-BOOKSHELF-TAG-GRAFTING：
说明 Tag 总表 + 嫁接表模式；
明确 Bookshelf 只保存 tag id 关联，不复制 tag 文本；
指出 BookshelfTagEditDialog 只能提交 tag_ids。
8.2 HEXAGONAL_RULES.yaml：
在 bookshelf_audit_list_action_contract 补充：
新增/确认 UpdateBookshelfTagsPort 或扩展 UpdateBookshelfUseCase 的 port description；
明确 Tag 更新走“全量替换”策略与对应端口签名；
描述 Tag 模块与 Bookshelf 模块之间的依赖方向（Bookshelf 只依赖 Tag 读端口，不反向依赖）。
8.3 VISUAL_RULES.yaml：
在 bookshelf_audit_tag_edit_dialog 与 bookshelf_dashboard_layout_v2 中：
写清“标签样式完全沿用 Library 标签组件”；
指明 Dialog 内禁止新建标签，只能 pick 总表；
记录标签切换的交互细节与空态文案（"-- 无标签 --"）。
8.4 三规中共同强调：
状态列 ACTIVE/ARCHIVED 纯文本 + token 控色、Pin/Archive 操作复用既有 UseCase、tooltip 统一文案和 aria 要求。
ADR‑098：结构与要点
9.1 文件路径：assets/docs/ADR/ADR-098-bookshelf-tags-grafting-and-status-consistency.md（命名风格沿用 ADR‑097）。
9.2 章节建议：

Context：
描述当前书橱标签无法保存、与 Library 不一致、违反 Tag 全局模型的问题；
提及 ACTIVE/ARCHIVED 状态 UI 不连贯、422 错误。
Problem & Forces：
需要统一 Tag 总表 + 嫁接表；
不破坏现有 Library Tag 流程；
遵守三份 RULES 的边界（Domain 不落色、不复制文案）。
Options：
A：用统一的 UpdateBookshelfUseCase 携带 tag_ids；
B：新建独立 UpdateBookshelfTagsUseCase / /tags 端点；
C（否决）：继续使用字符串标签。
Decision：
选择 A 或 B，并写清：
Tag 总表 + bookshelf_tags 嫁接表；
前端只操作 tag_ids；
Dialog 禁止 inline create；
ACTIVE/ARCHIVED 状态机与 Pin/Archive 行为规范。
Consequences：
Pros：一致性、去重、便于统计和跨模块搜索；
Cons：需要迁移旧数据、部分前端逻辑大改。
Implementation Notes：
列出关键后端文件（UseCase / Repository / migration）；
列出关键前端文件（Dialog、Dashboard、TagSelector）；
三规更新条目引用。
验证与迁移检查
10.1 数据迁移：

若历史 Bookshelf 已存有字符串 tags 字段，需要一次性 migration，将其解析为 Tag 总表 / bookshelf_tags 关联；
若没有旧数据，可直接上线新结构。
10.2 自动测试：
Backend：为新端点 / UseCase 写 Contract Test，验证 tag_ids 保存与读取一致；
Frontend：针对 BookshelfTagEditDialog 写单测，用虚拟 Tags/Bookshelf DTO 断言：选中标签后，仅传递 ID 数组。
10.3 手动验证场景：
创建/编辑 Bookshelf，打开 Tag Dialog：
选择多个 Tag，保存 → 刷新页面，标签与 Library 视图一致显示；
切换 ACTIVE → ARCHIVED，并验证 Pin/Archive 计数与日志卡片是否同步；
在 Libraries 和 Bookshelf Dashboard 上 hover 所有 Lucide 图标，查看 tooltip 与 aria 是否符合规定。