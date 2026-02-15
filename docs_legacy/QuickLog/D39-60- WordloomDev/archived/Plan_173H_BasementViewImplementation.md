Status: ✅ Completed — 2025-12-06

Plan: 落地 Basement 视图（按书架展示已删除书）
基于你给的 DB 截图 + dump 和代码结构，目前情况是：

数据层已经 OK：basement_entries / basement_books 里确实有书（截图 1 已证实）。
后端已有“列出 Basement 里的书”的接口，但返回的是按书逐条的扁平列表。
前端 Basement 页面目前只做了 summary，没有把这些书按书架分组渲染出来，也没有复用原有“书卡/封面”的 UI。
下面是一个可以直接照着执行的落地计划，分「先用现有接口做出视图」和「需要时再扩展后端」。

Steps
前端：找到 Basement 页面和 Hook，并打开数据通路

在 src 下搜索 暂无删除内容 或 可供恢复的书架，锁定 Basement 页组件（例如 BasementPage.tsx / AdminBasementDashboard.tsx 之类）。
在该组件里找到用于拉取 Basement 数据的 hook（例如 useLibraryBasement），确认它最终是调用某个 API client（如 getLibraryBasementBooks(libraryId, page, size)），而返回值里已经包含：
items: BasementBookSnapshot[]（每本书的快照，含 book_id / title / summary / moved_at / bookshelf_id / previous_bookshelf_id 等）；
total_deleted, group_count, lost_shelves 等 summary 字段。
确认有没有单独拉“书架列表”的 hook（例如 useLibraryBookshelves(libraryId)），以及是否能从中拿到 bookshelf_id -> bookshelf_name、is_basement 等，用来做分组显示名。
前端：在当前页面内“按书架分组 + 渲染列表”

在 Basement 页组件中，把从 hook 拿到的 items 在前端做一次 groupBy(bookshelf_id 或 previous_bookshelf_id)：
如果 previous_bookshelf_id 有值，就优先用它表示“原始书架”；
否则退回 bookshelf_id；
对于 null 的情况，分到一个 “未标记书架” 分组。
使用 bookshelves 列表构建一个 Map<bookshelf_id, { name, kind, is_basement }>：
显示名优先用匹配到的书架 name；
找不到但有 ID 时，显示 “已删除书架 xxxx…”；
完全找不到 ID 的，显示 “未标记书架 #1/#2…”。
把分组结果映射为前端内部的 DTO，例如：
groups: { groupId, bookshelfName, deletedCount, latestDeletedAt, books: BasementBookForView[] }[]；
每个 BasementBookForView 至少包含：id, title, summary, movedAt, coverIcon / coverMediaId, previousBookshelfName。
修改页面 JSX：
顶部 summary 区保持现状；
“可供恢复的书架：X 个” 下方，渲染一个“左侧分组列表 + 右侧当前分组书列表”：
左：列出 groups 中每个 bookshelfName 和 deletedCount；
右：根据当前选中的 group 渲染该组里的 books。
前端：复用现有“书卡/封面”组件展示 Basement 里的书

在 ui 或类似路径下，找到目前用来在普通书架中渲染书的组件（例如 BookCard, BookListItem）。
在 Basement 页右侧列表中，直接复用该组件：
传入 title、coverIcon 或 coverMediaId（如果现在 Basement API 里没有这些字段，可以先只显示标题 + 删除时间）；
额外在卡片上显示 “删除时间：movedAt” 和 “来自：previousBookshelfName”。
如果现有 BasementBookSnapshot DTO 已经带了封面信息（如 cover_icon / cover_media_id），在 hook 的 mapping 里把这两个字段透传进 BasementBookForView，并传给书卡组件。
后端：在确保现有扁平接口可用基础上，再考虑是否需要“后端分组”

在 backend/api/app/... 下搜索 basement，定位路由文件（例如 basement_router.py / admin_basement_routes.py）：
确认已存在 GET /admin/libraries/{library_id}/basement/books 之类的接口，返回分页的 BasementBookSnapshot 列表。
如果前端通过现有接口分组已经可以满足需求（只是在界面上展示），可以暂时不改后端，专注前端视图；
只需要保证：删除书时会正确在 basement_entries / basement_books 中生成记录，这一点你通过 DB 已验证。
若未来需要后端直接返回“分组好的结构”，可以再新增一个 endpoint（非现在立刻要做）：
GET /libraries/{library_id}/basement/grouped：内部在 basement_entries 上 GROUP BY bookshelf_id，返回 [ { bookshelf_id, bookshelf_name, deleted_count, books: [...] } ]；
前端则可以直接使用，不再自己分组。
校验与迭代：对 LibraryLog 实测

启动前后端，打开 Basement 页，选中 LibraryLog：
确认 summary 区统计数量与 basement_books / basement_entries 中的行数一致；
左侧分组列表中能看到至少一条：包含你刚刚软删除的那本书所在的书架。
点击该分组，在右侧看到：
书名（title snapshot）；
删除时间（movedAt）；
有封面的话展示封面或封面占位；
来源书架名称。
若一切正确，再考虑在每本书上加“恢复”“彻底删除”按钮，调现有的 restore/hard-delete API 即可。
Further Considerations
建议优先用“前端分组 + 复用现有书卡组件”快速把视图做出来，不阻塞你当前测试；后端 server-side 分组是第二阶段优化。
中途如果你愿意，可以把 Basement 页对应的前端文件路径发给我，我可以进一步给出“在该文件第几块代码里插入分组逻辑和渲染结构”的更细步骤。