Status: ✅ Completed — 2025-12-06

先给一个结论：
从你提供的 dump 片段看，后端已经有完备的 Basement 域模型（books + basement_entries + basement_books 视图 + create_library_basement() 等），但是当前 UI 只展示了 summary，没有把这些“可恢复书”和所属书架分组展示出来。也就是说：“书确实可以被移动到 Basement，但现在的前端看不到、后端也缺少一个专门给 UI 用的分组查询接口”。

下面给你一份分步骤的中文计划，专门针对“Basement 页面无法看到各个书架和其中具体书”的问题。

一、数据库侧：确认 Basement 数据模型与当前行为

你已经给了 dump，我这边可以确认几件事：

有 books 表，带 soft_deleted_at、previous_bookshelf_id、moved_to_basement_at 等字段，用于软删除和记录来源书架。
有 basement_entries 表，包含：
book_id
library_id
bookshelf_id
previous_bookshelf_id
各种 snapshot 字段（title、summary、block_count 等）
moved_at / created_at
有 basement_books 视图：专门用来聚合当前在 Basement 中的书。
有 create_library_basement() trigger，用来保证 libraries.basement_bookshelf_id 和 Basement 书架的一致性。
结合我们刚刚跑的 backfill 脚本：

现在 libraries 的 basement_bookshelf_id 已经补齐；
以后新建 library 时 trigger 会自动补 Basement 书架；
“删除（移动到 Basement）”时，应该会在 books + basement_entries / basement_books 里留下记录。
这说明 数据库这层已经具备实现“回收站视图”的所有原材料，缺的只是“合适的查询 + 展示”。

二、后端计划：补一层专门面向 Basement 页的 API

目标：让 Basement 页能够“按书架分组，看到每个组里的书”。

设计一个干净的 DTO 结构

后端暴露给前端的结构建议长这样：
[
  {
    "bookshelf_id": "shelf-uuid",
    "bookshelf_name": "某书架名（或 Basement 默认名）",
    "deleted_count": 3,
    "books": [
      {
        "book_id": "book-uuid",
        "title": "书名快照",
        "summary": "摘要快照（可选）",
        "moved_at": "2025-12-06T12:34:56Z",
        "previous_bookshelf_id": "之前所在书架"
      }
    ]
  }
]

基于 basement_books / basement_entries 写 SQL / Query

第一步：按 bookshelf_id 分组统计：
SELECT
  bookshelf_id,
  COUNT(*) AS deleted_count
FROM basement_entries
WHERE library_id = :library_id
GROUP BY bookshelf_id
ORDER BY deleted_count DESC, bookshelf_id;

第二步：按某个 bookshelf_id 拉取所有书：
SELECT
  be.book_id,
  be.title_snapshot,
  be.summary_snapshot,
  be.moved_at,
  be.previous_bookshelf_id
FROM basement_entries AS be
WHERE be.library_id = :library_id
  AND be.bookshelf_id = :bookshelf_id
ORDER BY be.moved_at DESC;

或者也可以用 basement_books 视图，如果视图里已经 join 好了 books / shelves。

在后端加两个 endpoint（示意）

比如在 backend/api/app/routers/basement.py 之类：

GET /libraries/{library_id}/basement/bookshelves
返回“每个 Basement 书架 + 删除数量”的列表。
GET /libraries/{library_id}/basement/books + ?bookshelf_id=...
返回指定 Basement 书架下的所有删书。
实现时直接用 SQLAlchemy 或 text SQL，从 basement_entries / basement_books 读就可以，不改 schema。

三、前端计划：改造 Basement 页面，真正展示“可恢复书架 + 书”

目标：从“只有几个统计卡片”升级为“左侧书架分组 + 右侧书列表”。

左侧：可恢复书架列表

用刚才的 GET /libraries/{id}/basement/bookshelves 数据；
渲染为一个列表：
显示 bookshelf_name + deleted_count；
当前选择的书架高亮；
点击后触发重新加载右侧的书列表。
右侧：当前书架的删书列表

请求 GET /libraries/{id}/basement/books?bookshelf_id=xxx；
显示：
书名（用 title_snapshot）；
删除时间（moved_at）；
原来所在书架（可选，用 previous_bookshelf_id 反查书架名字或直接展示一个标签）。
保持与现有 summary 卡片兼容

可以继续保留顶部“删除书籍总数 / 分组数 / 失联书架数”；
但把“可恢复的书架：1个”下面那块空白区改为我们上面说的“列表 + 书”。
还原 / 彻底删除操作（下一步优化）

在上述基础上，再为每本书增加：

“还原到原书架”：根据 previous_bookshelf_id 和 library_id，把 books / basement_entries 的记录还原；
“彻底删除”：在 Basement 页对书做 hard delete（可选，取决于你的产品策略）。
四、排查现有 500 或“看不到书”的具体步骤

结合你给的 dump 和我们已经做的 backfill，接下来可以这样落地排查：

在 psql 里确认当前 Basement 有没有书
-- 当前库所有 basement_entries
SELECT *
FROM basement_entries
ORDER BY moved_at DESC
LIMIT 50;


