Plan: Library 前置 Basement 视图化回收站
TL;DR：统一采用方案A：在每个 Library 的详情“前置界面”提供“Basement（回收站）”可视化层，按“书架分组”展示回收内容：整架删除则以“实体色”展示卡片；书架仍存在则以“灰度透明色”，点击可展开查看其被删除的 Book。恢复规则：书被恢复且原书架不存在时，必须选择一个现存书架；原书架仍存在时支持“恢复到原书架/放到新书架”。后端保持扁平端点，扩充分组数据与存在性标识；三 RULES 文件同步修订为“无限 Library + Basement 视图语义”。

Steps
修订规则与 ADR（无限 Library + Basement 语义对齐）

更新 DDD_RULES.yaml 与 HEXAGONAL_RULES.yaml 的 Basement 段落：每个 Library 自带 Basement；删除 Library 时将其 Bookshelf/Book 软删除并归档到 Basement；恢复策略与跨聚合限制说明。
更新 VISUAL_RULES.yaml：前端卡片语义（实体色=整架已删除；灰度=书架仍存在）、操作动效、空状态、确认弹窗、键盘无障碍规则。
新增 ADR-072-basement-ux-and-restore-flows.md：定义分组结构、布尔字段 bookshelf_exists、事件与审计、与扁平路由对齐。
后端契约巩固与补充（保持扁平端点）

GET /bookshelves/basement?library_id=...：返回 Basement 书架信息（已存在）。
GET /books/deleted?library_id=...：返回按“bookshelf 分组”的分页数据，每组包含 bookshelf_id|name|bookshelf_exists|count|items[]。
POST /books/{id}/restore：Body/Query 指定 target_bookshelf_id；若原书架存在，返回 suggested_original_bookshelf_id 供 UI 两选一。
GET /bookshelves/deleted?library_id=... 与 POST /bookshelves/{id}/restore：用于整架恢复（含书籍批量恢复语义，避免逐本恢复）。
Library 级删除与恢复：DELETE /libraries/{id} 软删除→全部转 Basement；POST /libraries/{id}/restore 恢复时带策略说明（可选“仅恢复 Library（保留 Basement 内容）/一并恢复附属”）。
响应形状统一 {items,total}，并明确 enum 传输小写（normal/basement），适配层大小写映射。
前端模型与 Hooks（FSD）

entities: 新增 BasementGroupDto（bookshelf_id|name|bookshelf_exists|items: BookSummary[]）、DeletedBooksListDto。
features/library: useBasement(libraryId) 获取分组数据；useRestoreBook 支持原书架/新书架二选一；useRestoreBookshelf；useEmptyBasement（分组/全局）。
统一 enum 映射（transport: normal/basement → UI: NORMAL/BASEMENT）；Query Key 规范：['basement', libraryId, filters]。
Library 前置 UX（方案A 双区布局）

pages /admin/libraries/[libraryId]：左侧为正常 Bookshelf 列表；右侧为“Basement 面板”（sticky）。
面板内容：按“书架分组”的卡片栅格：
实体色卡片：该“书架已删除”（组内都在 Basement）。
灰度透明卡片：该“书架仍存在”（仅部分书被删除）。
卡片点击展开：列出已删除 Books，行级操作“恢复”“查看原书”（若存在）。
顶部工具：筛选（按书架/关键词/时间）、批量选择、批量恢复、清空回收站（强确认）。
空状态：无删除项时显示提示与导航（返回 Library / 创建书籍）。
恢复与边界条件策略

恢复 Book：
原书架存在：弹窗提供 A) 恢复到原书架；B) 选择其他现存书架（必选）。
原书架不存在：必须选择现存书架（列出本 Library 内可用书架）。
恢复 Bookshelf：整架恢复（含架内 Books 一并恢复）；原 Library 若未恢复，提示先恢复 Library 或选择迁入另一个 Library（若允许跨 Library，需后端策略支持；默认禁止跨 Library）。
删除 Library：将所有 Bookshelf/Book 软删除并归档到 Basement；在“已删除 Libraries”页仍可访问该 Library 的 Basement 视图做粒度恢复或整库恢复。
权限/归属：所有 Basement 端点要求 library_id，后端校验归属与范围；跨 Library 恢复默认禁止（可作为后续增强）。
验证与可观测性

Use Case 级单测：分组一致性、bookshelf_exists 正确性、分页、孤儿 Book（原书架缺失）处理、批量恢复/清空。
E2E 场景：删除 Book→Basement 显示→恢复成功；整架删除→实体色分组→一键恢复；整库删除→Basement 访问→分组恢复与整库恢复。
指标与审计：埋点“删除/恢复”事件；管理员审计日志（谁在何时恢复了什么内容）。
Further Considerations
方案A 交互确认：右侧“Basement 面板”固定布局，还是切换 Tab（Basement / Shelves）？推荐面板，恢复效率更高。
全局 Basement：是否需要 /admin/basement 总览（跨 Library）？默认按 Library 局部治理；全局页可作为后续可视化与运营入口。
清理策略：行业常见做法是“回收站保留 30/60/90 天 + 可配置 + 超期自动清除 + 导出能力”。建议加滞留期与提醒