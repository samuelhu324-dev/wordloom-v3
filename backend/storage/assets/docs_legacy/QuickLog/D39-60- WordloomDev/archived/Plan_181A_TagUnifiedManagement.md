这套 Tag 体系的“正确做法”是——后端只有一个全局 Tag 域（tags 表 + 关联表），Library 负责产出面向 UI 的「库内标签摘要」，Bookshelf/Book 只拿 tag_id 或 tag 名称；前端则应该有一套统一的 Tag 视图/tooltip helper，所有 Library / Bookshelf / Book 的标签展示都复用它，而不是各写一份逻辑。

下面是一个可以落地的统一方案（以后实现即可）：

Plan: 统一 Tag 体系（后端 + 前端）
这套计划基于你 repo 里的 Tag 模块、LibraryTagSummary（backend/api/app/modules/library/schemas.py）、前端 tag hooks，以及 VISUAL_RULES 里 Plan176「book_tag_tooltip_rules」的约定。目标是：
1）所有真实标签数据只来自 Tag 模块（tags 表）；
2）库内展示用的描述/tooltip 统一走 Library 的 TagSummary；
- 第二轮迭代：移除硬编码双语 fallback，引入全局 Tag 搜索兜底路径（missing labels → `searchTags`），确保描述真源只能来自 Tag 模块/Library Summary，并在缓存失效时自动更新。
3）前端所有页面都用同一个“描述映射 + tooltip 格式化”工具，避免今天这个页面有说明、另一个页面没有的问题。

Steps
把「tooltip 文案/说明拼接」抽成一个前端 helper

位置建议：frontend/src/features/tag/ui/tagTooltip.ts（纯函数），或再配一个小 TagChip 组件。
逻辑：接收 { name, description }，输出：
展示文案（label-only / label + description）
tooltip 文本（如 {label} | {description}，用现有 i18n key：books.tags.label / books.tags.withDescription）
aria-label 文案
替换库里现有的各处手写逻辑：BookRowCard, BookFlatCard, LibraryTagsRow, 以后 Bookshelf 卡片也统一用它。
把「库内标签目录」升级为前端唯一的数据源

依托现有后端 LibraryTagsResponse（library_id + tags: LibraryTagSummary[]，包含 name/color/description）。
在前端提供一个标准 hook，例如：useLibraryTagCatalog(libraryId)（已经有 getLibraryTags，可以包一层）：
返回：
byId: Record<tagId, { name, color, description }>
byName: Record<normalizedName, { id, color, description }>
规则：任何需要“说明”的 UI（Library 页、Bookshelf 里展示书本、Book 卡片）都先用这个 hook 拿描述，而不是各自打 /tags。
约定一个统一的 TagViewModel，所有 UI 只认这一种

新建：frontend/src/entities/tag/viewModel.ts（类型而已）：
TagViewModel = { id: string; name: string; color?: string; description?: string }
提供 mapper 函数：
fromLibrarySummary(LibraryTagSummaryDto) -> TagViewModel
fromTagDto(TagDto) -> TagViewModel
forBook(tagsSummaryNames: string[], libraryCatalogMap) -> TagViewModel[]（最多 3 个）
Library 卡片、Bookshelf 卡片、Book 卡片全部走 TagViewModel + tagTooltipHelper → 不再各自拼字符串。
把「book / bookshelf 的 tagsSummary → 描述」逻辑统一到一个地方

现在 Book 卡片里有：自己根据 tagsSummary + tagDescriptionsMap 判断 tooltip，这块容易分叉。
做法：
在 BookMainWidget 层（和你现在为 /admin/books 做的很像），统一用 useLibraryTagCatalog(libraryId) 把 TagViewModel[] 算好，再下发：tagViewModelsByBookId 或简单的 tagDescriptionsMap（key 可以是 libraryId:tagNameLower）。
Bookshelf 详情页也一样：已知 library.id，直接用同一个 hook；BookDisplayCabinet / BookFlatCard 只负责展示，不再自己取 description。
这样就解释了你问的第二个问题：
过去 ARCHIVED 之所以“总能出文案”，是因为它在 Book ribbon 里是特殊常量，UI 本身就有一行描述；
普通 tag（DEV）如果没有走 LibraryTagSummary → 就看不到 description。统一走这条链路之后，两者都会正常显示描述。
后端侧：确认 Library 是「说明真源」，Tag 只是「字典」

保持现状：
Tag 模块：全局 tags（name/color/icon/description/level/usage），负责 CRUD + 关联。
Library 模块：有 LibraryTagSummary / LibraryTagsResponse，负责把「这个库里实际用到的 Tag」打包成 DTO。
在 DDD_RULES / HEXAGONAL_RULES 里写清楚：
Book DTO 只带 tags_summary: string[]（名字而已），永远不带 description；
谁要 tooltip，就必须去问 Library 的 LibraryTagsResponse 或对应端口，而不是给 Book 新加字段。
统一「创建/编辑时选标签」的流程（Library / Bookshelf / Book）

现在 Library 新建/编辑时已经有一套 Tag 选择逻辑：LibraryForm + TagMultiSelect + useTagSuggestions + useCreateTag。Bookshelf / Book 也有类似代码（比如 BookshelfTagEditDialog / BookEditDialog），但有重复。
把“从自由文本变成 tagId”那段流程（search → 找到就用 → 否则 create → 再用）抽成公共 helper：ensureTagIds(tags: { id?, name }[])，放到 model 下。
所有表单（Library / Bookshelf / Book）只：
通过这个 helper 拿一组 tag_ids，
然后调用各自的 update / replace-tags API（后端依旧只接受 ID）。
这样不管在哪个界面加/改 Tag，都走同一条链路，利于维护。
前端缓存策略：以「库」为单位缓存 Tag 描述

在 useLibraryTagCatalog(libraryId) 里约定一个 React Query key，比如：['library-tag-catalog', libraryId]，staleTime 较长（几分钟）。
当 /admin/tags 页面更新某个 Tag（改描述），在成功后调用：invalidateQueries(['library-tag-catalog']) 或带 libraryId 的变体，让 Library/Bookshelf/Book 界面 tooltip 能自动刷新。
这样 Tag 修改→Library 视图→Bookshelf/Book 视图是一条一致的刷新路径。
文档层补一条「Tag UI 规范」

在 VISUAL_RULES.yaml 已经有 book_tag_tooltip_rules 和 library_tag_tooltip_rules，可以再明确两点：
UI 一律用 TagViewModel + tagTooltipHelper；
高层组件（LibraryMainWidget, BookshelfMainWidget, BookMainWidget）负责准备好 TagViewModel 或 tagDescriptionsMap，低层卡片组件禁止再请求 API。
在 HEXAGONAL_RULES.yaml 的 module_tag / module_book_ui_preview_layer 下加个小段，说明 Tag 作为独立 BC，通过 LibraryTagSummary / Tag hooks 暴露给 UI。
如果你愿意，下一步我可以直接：

列出一个更具体的前端接口草稿（useLibraryTagCatalog 的返回结构、TagViewModel 类型、buildTagTooltip 函数签名），
然后按这个方案把 Library / Bookshelf / Book 三个页面的标签展示 refactor 一遍。

---

2025-12-08 实施进展

- 新增 `useLibraryTagCatalog`：统一通过 React Query 缓存 Library tag catalog，自动合并 inline + fetched 描述，供 BookMainWidget/Bookshelf 复用。
- 补充 `tagCatalog` helper（build/merge/resolve/findMissing）：BookRowCard、BookFlatCard、/admin/books 页面都改用同一套描述映射逻辑。
- 初步覆盖：Bookshelf 视图已经改为依赖 catalog hook，tooltip 现在与 Library 页一致；后续可以继续推进 TagViewModel/TagTooltip 组件化。
