Plan: Book 展柜 Tag + PIN 行为升级
本次改动围绕 3 个核心：
1）在书本展柜/Grid 视图中，用“首个 Tag 名称”替代原来的 DRAFT 字段，同时减轻右上角统计 “2本” 的字重；
2）统一 Grid / List 视图的 hover 行为为 icon-only（编辑 / 删除 / PIN），并为 pinned 书籍增加左侧丝带；
3）在 Book 层正式引入 Tag 只读展示链路，并在 DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES + ADR-102 中固化规则。
以下是可直接交给工程师实现的详细步骤。

Steps 1：前端数据模型与 DTO 扩展（Book + Tag）
在 index.ts（或 BookDto 定义所在文件）：

为 BookDto 新增可选字段：tagsSummary?: string[];
同时保留后端原始字段名映射：tags_summary?: string[] | null;
在 DTO 适配函数（如 mapBookDto 或 toBookDto）中：
若 raw.tags_summary 是数组且长度 > 0，则设置 tagsSummary = raw.tags_summary;
否则 tagsSummary 设为 undefined。
搜索所有 Book 列表/详情使用点（grep 'BookDto' frontend/src）：

确认主要数据来源组件：BookMainWidget、BookDisplayCabinet / BookShowcaseItem、列表行组件（如 BookRowCard 或等价组件）。
在这些组件 props 类型中允许解构 book.tagsSummary，为后续 Tag 徽标和 chips 展示做准备。
不在前端伪造 Tag 名称或数量：

统一约定：所有用于展示的 Tag 名称来自 BookDto.tagsSummary，前端不从 bookshelf 或其他地方拼装字符串。
Steps 2：展柜视图右上角 “2本” 字重调整
定位“2本”样式：

搜索 2本 或 本 + 统计元素所在组件，多半在 page.tsx 或其 module.css 中的 summary 统计。
查找负责该文本的 CSS 类，如 .sectionCount, .summaryCount, 或特定 span。
调整字体粗细：

在对应 CSS Module（例如 page.module.css 或书架头部统计样式文件）中，将该计数字体从 font-weight: 700/600 调整为 500 或 400。
保持字号与颜色不变，只降低字重，使“2本”视觉更轻。
Steps 3：BookFlatCard 支持“首个 Tag 徽标”替代 DRAFT
在 BookFlatCard.tsx：

为 BookFlatCardProps 新增可选 props：
tagNames?: string[]; // 完整 tag 名称数组
primaryTagName?: string; // 已选首 Tag
showStatusBadge?: boolean; // 是否仍显示原来的 status 文本，默认 false 用于展柜/列表
在组件内计算首 Tag：
const allTags = tagNames ?? book?.tagsSummary ?? [];
const firstTag = primaryTagName ?? allTags[0];
调整右上角 badge 渲染逻辑：
当前：resolvedStatus 存在时渲染 badge 显示状态文本（如 DRAFT）。
修改为：
若 firstTag 存在：渲染 badge，文本为 firstTag；
否则若 showStatusBadge !== false && resolvedStatus：仍渲染原状态文本（用于某些 admin 场景）；
否则：不显示 badge。
在 BookFlatCard.module.css：

复用现有 .badge 样式，但稍作调整以更贴近 bookshelf Tag chip：
字重从 600 降到 500 或 400；
如需要，可新增 .tagBadge 继承 .badge，仅调整背景色/圆角，颜色 token 参考 bookshelf Tag 样式（silk-blue / outline 胶囊）。
在 BookFlatCard 中去除 hover overlay 的“说明 + 查看详情”文本（此前已移除说明文本）：

保留 hoverOverlay 容器，用于后续 icon-only 操作（下一步中扩展）。
Steps 4：BookShowcaseItem / BookDisplayCabinet 传入 Tag 与 PIN
在 BookShowcaseItem.tsx：

从 book 解构：
const tagNames = book?.tagsSummary ?? [];
const primaryTag = tagNames[0];
渲染 BookFlatCard 时增加：
tagNames={tagNames}
primaryTagName={primaryTag}
showStatusBadge={false} // 避免无 Tag 回退到 DRAFT
确保 pinned 状态透传：
现在已从 book?.is_pinned ?? isPinned 计算 resolvedPinned，要保证 resolvedPinned 仍然用于 PIN 丝带显示（后续步骤）。
检查 BookDisplayCabinet.tsx：

它是 BookShowcaseItem 的 re-export，无需额外逻辑，但其他调用它的地方（如 BookMainWidget）要确保 book 包含 tagsSummary。
Steps 5：Grid/List Hover 行为改为 icon-only（编辑 / 删除 / PIN）
在 BookFlatCard 中扩展 hover 操作 API：

在 props 中新增：
onOpen?: () => void;
onEdit?: () => void;
onDelete?: () => void;
onTogglePin?: () => void;
在 hoverOverlay 内部：
取消渲染摘要文本；改成一个靠右或居中的 icon 按钮组容器（例如 div 使用新 class .hoverActions）；
使用 Lucide icons：Eye, Pencil, Trash2, Pin（或 Bookmark 复用现有 icon）；
每个图标按钮：
type="button" className={styles.hoverIconButton}
onClick 调用对应回调，并 e.stopPropagation() 以防触发卡片整体点击；
设置 aria-label 如 “查看详情”“编辑”“删除”“PIN / 取消 PIN”。
在 BookFlatCard.module.css 中新增 hover 图标样式：

.hoverActions：右下或右上对齐的水平图标行，gap 8px；
.hoverIconButton：24x24 圆形浅色背景、图标颜色为 #e5e7eb，hover 时背景加深、图标变亮；
保持 overlay 的渐变背景（顶部透明、底部深色）不变。
在 BookShowcaseItem 中绑定事件：

从 props 新增可选回调：
onOpen?, onEdit?, onDelete?, onTogglePin?
将这些回调透传给 BookFlatCard。
BookDisplayCabinet 的上层（通常是 BookMainWidget 或书架页面）负责实现这些回调，以调用路由跳转或 mutation hooks。
LIST 视图 hover 行为统一：

查找书籍列表行组件（例如 BookRowCard.tsx 或类似）：
若已有 emoji 或文字按钮组合，改为与展柜一致的 Lucide icon-only 工具条；
确保 PIN 按钮行为一致（同样调用 onTogglePin，不在行组件内部修改状态）。
Steps 6：PIN 视觉——3D 卡左侧“丝带”与 List 行 PIN 图标
在 BookFlatCard.tsx 结构中：

利用已有 resolvedPinned 值（或从 props 解构 isPinned），当为 true 时，在 .bookBody 内增添一个新的绝对定位元素：
<span className={styles.pinRibbon} aria-hidden />
位置建议：
贴合卡片左侧中部，高度略小于卡片高度；
稍向外突出 2px，形成“绕书一圈”的视觉错觉。
在 BookFlatCard.module.css 中定义 .pinRibbon：

position: absolute; left: 0; top: 14px; bottom: 14px; width: 6px;
背景使用 silk-blue 强调色渐变，如：background: linear-gradient(180deg, #4f46e5, #22c55e);
border-radius: 0 4px 4px 0;
可选在中间用 ::after 伪元素做小 “PINNED” 文本或图标，但注意字号极小、避免抢戏。
处理 Bookmark 图标：

目前左上角 pinBadge 使用 Bookmark 图标：
可以保留以强化“可 Pin”语义；
或在 pinned 时隐藏 pinBadge，只保留左侧丝带和 hover 工具条中的 Pin icon（在 VISUAL_RULES 中说明具体选择）。
在 List 行组件中：

若已有 pinned 显示（小图标），保持不变；
若没有，则在书名右侧或状态区增加一个只读 Pin 图标（与 Bookshelf 列表一致），当 book.is_pinned 为 true 时显示。
Pin 行为逻辑：

上层容器（通常是 BookMainWidget 的某个 hook）负责：
调用后端 togglePin 或 updateBook use-case 修改 is_pinned；
更新 Query 缓存并保持 pinned 书在列表中的排序规则（通常 pinned 先于未 pinned）。
Steps 7：List 模式中 Tag chips 布局（对齐 Bookshelf Tag 样式）
找到 Book 列表行组件（例：BookRowCard.tsx 或 BookListItem.tsx）：

在展示书名和状态的区域下方或右侧，新增 Tag chips 容器：
const tags = book.tagsSummary ?? [];
仅渲染前 3 个标签：tags.slice(0, 3)；
若总数 >3，则在末尾追加 +N chip（N 为剩余数量）。
样式对齐：

参考 Bookshelf 列表 tag 的样式文件（如 frontend/src/features/bookshelf/ui/BookshelfTagChips.module.css）：
复用或抽取公共样式 class，如 .tagChipSmall；
字号约 11–12px，边框浅蓝/灰、背景略带色；
间距与 Screenshot 3 一致：标签略向下缩进，形成一行矩形胶囊。
无 Tag 情况：

列表中不显示 chip 行，也不显示 -- 无标签 -- 文本，以减少噪音；
若设计需要，可以在 hover 时显示 “No tags” tooltip，但不在主 UI 显示。
Steps 8：后端 / API 层：为 BookDto 补充 tags_summary
在 Python 后端（大致路径 app 下的 Book 相关 use-case 与 DTO）：

找到 BookDto 或等价 Pydantic schema。
为其新增可选字段：
tags_summary: list[str] | None = None
在序列化逻辑中，将 DB 层的 Tag 关联转换为最多 N 个 tag 名称列表。
在书籍列表 / 详情用例：

在 ListBooksUseCase 中：
查询 books 时 join Tag 关联表（如 book_tags），按 tag 排序；
使用 array_agg(DISTINCT tag.name) 或 ORM equivalent 聚合为 tags_summary；
限制 N（如 3~5），超出由 UI 显示 “+N”。
在 GetBookUseCase 中：
同样返回完整 tags_summary，以便 detail 页后续使用。
Hexagonal 端口说明：

在 Book 相关 Port 接口说明中（如 BookQueryPort）：
明确列表/详情方法的返回 DTO 中可选包含 tags_summary 字段；
将其归类为“Read model 装饰字段”，不要求 Domain Book 实体本身持有。
避免违反 Tag 聚合规则：

不在 Book Domain 中冗余 Tag 文本；只在查询层（projection）使用；
Tag 的增删改仍通过 Tag 模块 / 关联表接口完成，而不是通过 Book 更新接口直接修改 tags_summary。
Steps 9：DDD_RULES.yaml 更新计划
在 “Domain 3: Book” 或现有 Book 相关 policy 区域中新增：

POLICY-BOOK-TAGS-SUMMARY（示意要点）：
Book 聚合通过 Tag 关联暴露 tags_summary 只读列表，用于 UI 展示；
tags_summary 是最多 N 个 Tag 名称的快照，不持久化在 Book 实体字段中；
新增/删除 Tag 必须经由 Tag 模块完成，tags_summary 由查询层自动投影。
扩展现有 POLICY-BOOK-GALLERY-SHELF-STRIP / POLICY-BOOK-VIEW-MODES：

补充说明：
Book 展柜/Grid 视图右上角的状态徽标优先显示 tags_summary[0]；
若 Book 无 Tag，则状态徽标可为空，不再强制展示 “DRAFT” 文本；
Domain status 仍用于权限和生命周期判断（编辑、删除、PIN 的可用性）。
PIN 行为规则：

在 pinned 相关 policy（如 POLICY-BOOKSHELF-DASHBOARD 扩展段）追加 Book 子条目：
描述 Book 的 is_pinned：
仅影响列表排序和分段（例如 pinned 区域）；
不改变 Book 的成熟度或生命周期；
对 Basement / Legacy 书籍，is_pinned 修改应受限（只读）。
Steps 10：HEXAGONAL_RULES.yaml 更新计划
在 book_maturity_segmentation_strategy 附近新增 book_tags_summary_strategy：

内容要点：
ListBooks / GetBook 端口允许返回 tags_summary: list[str] 作为 read-model 扩展；
该字段来源于 Tag 模块：通过 join TagAssociation 计算；
Port 调用方（如 REST Adapter）不得自行构造或篡改 tags_summary。
在 book_gallery_strip_adapter / book_view_modes_adapter 部分：

加入说明：
展柜/Grid Adapter 使用 tags_summary[0] 渲染右上角 Tag 徽标；
hover 工具条中的操作（edit/delete/pin）必须调用对应 UseCase：
UpdateBookUseCase（编辑 & Pin）
DeleteBookUseCase 或软删除 use-case（删除）
OpenBookWorkspace（查看详情）。
PIN 相关 Hexagonal 行为：

在 book_gallery_shelf_strip 或 pinned 相关策略内：
明确 UpdateBookUseCase 在处理 is_pinned 时遵循与 Bookshelf 相同的约束；
Adapter 仅通过布尔字段传递，不自行调整排序；排序逻辑由 QueryService / Repository 层控制。
Steps 11：VISUAL_RULES.yaml 更新计划
在 book_gallery_visual_rules 小节中扩写：

“右上角徽标”：
RULE：展示首个 Tag 名称（tags_summary[0]），字体 weight = 500，背景色继承 Tag chip 配色；
若无 Tag：不显示文本徽标，仅保留背景卡边框；
“hover 操作条”：
RULE：hover 时在卡片右下角显示 icon-only 工具条（Eye / Pencil / Trash / Pin），不出现文本说明；
图标尺寸 16–20px；圆形浅色背景；悬停时背景略亮；
legacy / archived / basement 书籍灰化对应图标并禁用点击。
在 book_maturity_visual_rules 或相邻视觉规则中加入 PIN 带状纹理说明：

RULE：is_pinned = true 时，在 3D 卡左侧渲染一条 silk-blue 带状纹理：
宽度 4–6px，高度略小于卡片；
可以叠加轻微阴影，强调“已固定”状态；
若还使用 Bookmark 图标，应说明两者同时存在或互斥的视觉决策。
在 book_preview_cards_phase_2 或 Tag 相关视觉段落中：

描述 List 模式下 Tag chips 的呈现：
每行最多显示 3 个 chips，超出显示 “+N”；
样式沿用 Bookshelf tag 组件：浅色边框、圆角胶囊、小字号；
Tag 行放置在书名下方，保持行高紧凑。
Steps 12：ADR-102 更新计划（新 ADR 内容结构）
在 ADR 中找到或新建 ADR-102-*.md，推荐标题：
ADR-102-book-gallery-tags-and-pin-visual-unification.md

建议结构：

Title / Status / Date

标题：Book 展柜 Tag 徽标与 PIN 视觉统一
Status：Accepted
Date：2025-11-27
Context

当前 Book 展柜 / 列表 视图的现状：
右上角 DRAFT 状态徽标、hover 摘要文字、PIN 仅在部分视图可见；
Tag 模块已经存在于 Library / Bookshelf 中，但 Book 仅在后端有 Tag 关联，无前端只读展示；
User 需求：用 Tag 替换 DRAFT，统一 hover icon-only，增加 PIN 丝带，并与现有 Bookshelf Tag/PIN 视觉一致。
Decision

概要：
为 Book read-model 扩展 tags_summary 字段；
展柜/Grid 视图右上角徽标展示首个 Tag 名称；
hover overlay 改为 Lucide icon-only 工具条（查看 / 编辑 / 删除 / PIN）；
is_pinned 通过 3D 卡左侧丝带和行视图 Pin 图标强化展示。
Consequences

正面：
书卡与 Bookshelf Tag/PIN 体验一致，信息密度更高；
Tag 系统真正贯穿 Library → Bookshelf → Book 三层；
负面 / 风险：
ListBooks 查询增加 Tag join 与聚合，有一定性能开销；
需要同时更新三份规则文件，短期内增加维护成本。
实施要点：
前端组件和 CSS 需同步更新；
后端 UseCase 和 DTO 要扩展；
Basements / Legacy 的 PIN 修改和危险操作需要通过 A11y & 权限策略限制。
Status & Follow-up

Status：Implemented in v3.x
Follow-up：
未来可能增加 Book 层 Tag 编辑对话框，复用 Bookshelf Tag 编辑 UX；
根据真实数据量评估 Tag 聚合查询是否需缓存或索引优化。
Steps 13：边界与测试建议
边界场景：

Book 无 tags：
展柜右上角不显示 Tag 徽标；
List 行不显示 Tag chips 行。
多 Tag：
后端 tags_summary 最多提供 N 个；
前端最多渲染前 3 个，其余折叠为 “+N”。
Basement / Legacy：
hover 上隐藏或禁用编辑、删除、PIN 按钮；
仅保留查看详情 icon。
回归测试点（实现后建议）：

Bookshelf Dashboard 上的 Bookshelf Tag / PIN 不受影响；
/admin/books/{bookId} 工作区 tabs 功能正常；
Block Editor 与 Book Preview Cards 的交互（点击卡片进入详情）仍然工作；
Pagination & filtering 不受新字段影响（tags_summary 为附加字段）。
如果你愿意，下一步可以指定从哪个部分先开始实施（前端 UI、后端 DTO、还是规则文件/ADR），我可以帮你把对应部分再拆成更细的“逐文件修改 checklist”。