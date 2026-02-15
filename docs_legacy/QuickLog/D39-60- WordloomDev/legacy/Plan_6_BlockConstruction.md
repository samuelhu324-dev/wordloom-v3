一、Block 领域与聚合模型建议

聚合边界
新增独立聚合根 Block（不从属于 Book 聚合内部集合，使用 book_id 外键关联）。
Block 不嵌套其它 Block（线性序列），保持简单的顺序列表。
顺序字段 sequence_index（0..N-1 连续），重排时保持无空洞。
字段初版
id: UUID
book_id: UUID
library_id: UUID（权限/多库过滤）
sequence_index: int
block_type: enum {paragraph, heading, list, code, quote, task}（后续可扩展 math, table, image）
markdown: text（原始 Markdown）
html_cache: text 可空（服务端渲染或前端回填）
is_pinned: bool（可选，后续用于快速跳转）
status: enum {normal, archived, deleted}（软删除进入 BasementBlock 视图）
word_count / char_count（派生）
created_at / updated_at / soft_deleted_at
领域不变式
sequence_index 必须连续且唯一同一 book 范围内。
markdown 长度 ≤ 20KB（视觉规则给出 UX 限制提示）。
block_type 与 markdown 内容语法匹配（heading 只能有一级行；code 至少包含反引号块）。
删除使用软删除（设置 soft_deleted_at + status=deleted），恢复清除。
领域事件
BlockCreated(block_id, book_id, sequence_index, occurred_at)
BlockContentUpdated(block_id, book_id, diff_summary, occurred_at)
BlockReordered(block_id, book_id, old_index, new_index, occurred_at)
BlockDeleted(block_id, book_id, occurred_at)
BlockRestored(block_id, book_id, occurred_at)
BlockPinnedStatusChanged(block_id, book_id, is_pinned, occurred_at)
用例（Application 层）
CreateBlockUseCase(book_id, library_id, block_type, markdown)
UpdateBlockContentUseCase(block_id, markdown)
ReorderBlockUseCase(book_id, block_id, target_index)
DeleteBlockUseCase(block_id)
RestoreBlockUseCase(block_id, target_index?)（默认回原位置或末尾）
ListBlocksUseCase(book_id, skip, limit)
PinBlockUseCase(block_id, is_pinned)
仓储接口（Output Port）
save(block: Block) -> Block
get_by_id(block_id) -> Optional[Block]
get_by_book(book_id, skip, limit, include_deleted=False) -> (List[Block], total)
reorder(book_id, block_id, new_index)（内部执行局部批量 shift）
get_deleted_by_book(book_id, skip, limit) -> (List[Block], total)
hard_delete(block_id)（极少使用）
性能与索引
复合索引 (book_id, sequence_index)
软删除过滤索引 (book_id, soft_deleted_at)
全文检索（未来）：专用 search_block_content 索引或外部引擎
二、API / 合同建议

分页响应 BlockPaginatedResponse (与 V2 一致)
{
"items": [BlockDetailResponse...],
"total": 120,
"page": 1,
"page_size": 50,
"has_more": true
}
BlockDetailResponse
id, book_id, block_type, markdown, html(optional), sequence_index, status, is_pinned, word_count, created_at, updated_at, soft_deleted_at
创建请求 CreateBlockRequest
book_id, library_id, block_type, markdown
更新请求 UpdateBlockContentRequest
markdown（幂等）
重排请求 ReorderBlockRequest
block_id, target_index
软删除 / 恢复请求 DeleteBlockRequest / RestoreBlockRequest
错误代码
BLOCK_NOT_FOUND
BLOCK_INVALID_TYPE
BLOCK_INVALID_MARKDOWN
BLOCK_REORDER_OUT_OF_RANGE
BLOCK_SEQUENCE_INVARIANT_BROKEN（仅内部断言）
三、前端界面 / UX（Visual 层）

点击 Book 卡片 → 进入 BookDetailPage 包含：
顶部：书籍标题 / 描述 / 统计（block 数量）
BlockList：虚拟滚动（react-window / 自研 Intersection）加载分页
Block 编辑单元
单击进入编辑态：Markdown textarea + 工具栏（bold / italic / heading / code / list / quote）
保存策略：debounce 800ms 自动保存 + 手动 Ctrl+S
状态提示：保存中 / 已保存 / 出错重试
重排：拖拽（drag handle）或键盘快捷（Alt+↑/↓）
新建：在当前块下方按 Enter+Enter（空行）或工具栏“新建段落”
占位与空状态
空书籍：展示“暂无 Block，按 N 创建首块”
加载骨架：灰色矩形 + 闪动条
内容长度提示
15KB 显示黄色警告；>20KB 拒绝保存（前端截断并提示分拆）

错误反馈
重排失败：红色 toast “序号冲突，已刷新最新顺序”
保存失败：在块右上角小图标提示并可手动重试
四、Hexagonal 适配策略

Markdown 渲染
前端主渲染（轻量），后端可选延迟生成 html_cache（未来用于搜索摘要）
后端适配器：MarkdownServicePort → render(markdown) -> html（可空实现现在返回 None）
BlockRepositoryPort（如上）
Transaction / Ordering
Reorder 用例内部：获取目标 book_id 全部 Block id / index → 只调整受影响的区间（最少 UPDATE）
发送 BlockReordered 事件供统计或审计
防并发策略
更新和重排使用 updated_at 乐观锁（If-Match header 或请求带 last_updated_at；冲突返回 409 BLOCK_VERSION_CONFLICT）
软删除与恢复
与书籍 basement 类似，可后续建立 Block Basement 视图（二期）
五、DDD 规则新增（概要）

CONVENTION-BLOCKS-001：Block 聚合根字段与不变式列表
CONVENTION-BLOCKS-002：顺序维护原则（连续序列、重排算法、事务范围）
CONVENTION-BLOCKS-003：Markdown 校验策略（长度、类型匹配）
CONVENTION-BLOCKS-004：事件命名与属性最小化
CONVENTION-RESPONSES-BLOCKS-001：统一分页响应采用 Pagination V2
ENUM-BLOCK-TYPE-TRANSPORT：transport 层 block_type 为 lower_case；domain 枚举 UPPER_SNAKE_CASE
六、阶段实施计划（中文）
阶段 1（今日）：

建立 Block 领域模型与仓储接口（只内存或简单 SQLAlchemy 表结构迁移）
基础 API：POST /blocks, GET /blocks?book_id=, PATCH /blocks/{id}, POST /blocks/{id}/reorder
前端：BookDetailPage 基本跳转 + BlockList 只读展示（虚拟滚动占位）
阶段 2：
编辑保存（debounce）与工具栏 Markdown 格式化（最小功能：粗体、斜体、标题、代码块）
创建/删除/恢复操作；序号重排交互（拖拽 + 快捷键）
阶段 3：
乐观更新 + 错误回滚处理；分页加载更多；性能优化（request batching）
事件集成（统计 word_count、最近更新列表）
阶段 4：
html_cache 后端渲染服务接口（可用 python-markdown 库）；搜索 / 预览摘要；Block Basement 视图
阶段 5：
富类型扩展（任务、引用、图片上传、表格）；复杂块插件体系（保持 Hexagonal 插拔）
七、ADR-080 主要章节（将创建）
标题：ADR-080: Block Editor Integration, Markdown Domain Model, Ordering & Soft Delete Strategy
内容要点：

Context：需要支持逐段块结构、顺序、Markdown、软删除
Decision：独立 Block 聚合 + Pagination V2 + 乐观锁 + 外部 Markdown 渲染可插拔
Alternatives：嵌入 Book 聚合 / 单一长文字段 / 无序块集合 / 强制服务器渲染
Consequences：灵活扩展、额外顺序维护开销、需要索引与并发控制
Implementation Steps 与 Timeline（阶段 1-5）
Testing Guidelines（顺序断言、乐观锁冲突案例、Markdown 校验）
Future Extensions（搜索、插件、协同编辑）
References：现有三份 RULES + Evans DDD + Hexagonal Ports
八、后续文件更新（待你确认后执行）

VISUAL_RULES.yaml：新增 RULE_BLOCK_EDITOR_INTERACTION_001, RULE_BLOCK_MARKDOWN_LIMITS_001
HEXAGONAL_RULES.yaml：新增 RULE_BLOCK_REPOSITORY_PORT_001, RULE_MARKDOWN_RENDER_SERVICE_PORT_001, RULE_BLOCK_REORDER_TRANSACTION_001
DDD_RULES.yaml：新增 CONVENTION-BLOCKS-* 系列与响应合同
新建 ADR-080 markdown 文件
请确认是否同意以上方案与阶段计划。如果同意，我将：

立即创建 ADR-080 文件
提交三份 RULES 补丁
准备 Block 数据库迁移草案与最小接口骨架