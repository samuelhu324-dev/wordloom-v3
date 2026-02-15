这个问题要先把「删」拆成几种含义，不然 basement 一下子就变成跨表地狱。

我先给一个总结版结论，再展开：

推荐做法：

Library / Bookshelf：只做归档（Archive），一般不进回收站，不做细粒度恢复。

Book：是跨层级删除恢复的主角，进全局 Basement，可整本恢复。

Block：在 Book 内有局部小回收站（local trash），只在本 Book 下恢复。

Basement：只是一个视图，把「被软删除的 Book + 被硬隐藏的 Block 快照」聚合起来，不是独立 Library。

一、先区分三种“删法”

软删除 / 回收站：用户还能找回来（Basement/Trash）。

归档 Archive：不再日常使用，但数据视为长期保留，不鼓励恢复到“活跃状态”。

硬删除 Hard delete：真的从数据库删掉（一般只有系统任务 / 开发工具做）。

不把三种混在一起，后面规则就会清晰很多。

二、按层级来定职责
1）Library / Bookshelf：建议只做「归档」，不做细粒度恢复

理由：

Library / Bookshelf 本质是“结构容器”，删除后恢复要连同所有子级一起弄回来，逻辑非常重。

行业上大平台（Notion / Confluence / GitLab 项目级别）大多是：

项目空间：可以 Archive / Deactivate；

真正的彻底删除通常只给管理员，且风险非常高。

建议规则：

Library：

用户界面只提供：Archive / Unarchive。

Archive 后：

不在默认列表显示；

里面的 Bookshelf / Book / Block 不再允许编辑（或只读）；

但搜索 / 引用仍然可以命中（像“历史档案”）。

Bookshelf：

同样只提供 Archive；

Archive 后，该 shelf 下的 Book 一起标记为「从属归档」，
但 Book 本身仍可在 Basement 中被单独恢复（见下）。

删除 Library / Bookshelf 的“真硬删”可以保留在后台管理脚本里，
正式产品里先不暴露给终端用户，这样省掉大量复杂的跨表恢复逻辑。

2）Book：跨层级删除恢复的主角（进 Basement）

这里是你真正需要“回收站”的层级，因为 Book 对用户来说是一个完整作品 / 文档单元。

推荐行为：

用户点「删除 Book」=

books.deleted_at 设定时间戳（软删除）；

所有 blocks 同时打上 deleted_at，但用一个 deleted_reason = 'book_deleted'；

在 UI 上，Book 进入 Basement 全局回收站，显示为：

标题 + 所在 Bookshelf + Library + blocks 数量等。

恢复 Book：

从 Basement 选中 → 「恢复」：

books.deleted_at = null；

同时所有 deleted_reason = 'book_deleted' 的 blocks 也恢复；

如果所属 Bookshelf / Library 已经 Archive，则：

保持上级的 archive 状态（默认），

或提供一个选项：“一起从归档恢复上级”。

关键点：

Book 是「结构 + 内容」绑定的最小单位，整个生命周期闭环都在这一级处理。

Basement 主要存 Book 级别的记录，这样用户的心智也简单：

“全局回收站 = 被删除的作品。”

3）Block：本 Book 内的小回收站，优先本地恢复

Block 数量巨大，你如果把所有 Block 也扔进全局 Basement，会瞬间炸裂（信息太多 + 跨表复杂）。

更实用的做法是：

在每个 Book 里搞一个局部 Trash 视图：

只显示该 Book 下 blocks.deleted_at != null 的条目；

支持单条 / 多条恢复；

支持彻底清空本书的 Block 回收站。

与 Book 删除联动：

如果 Block 是因为 Book 被删而软删除的，deleted_reason = 'book_deleted'；

用户恢复整本 Book 时，Block 一起回来；

如果是用户在 Book 里手动删的 Block，deleted_reason = 'user_deleted'，只在本书 Trash 里显示。

这样 Block 的恢复范围始终在原 Book 内，不会跨 Library / Bookshelf 跑来跑去，
逻辑跟大多数文档编辑器的「本页撤销 / 本页历史」类似。

三、Basement 视图本身的职责

既然你已经决定 basement 不是独立 Library，而是视图模式，那就更简单：

Basement = 这几个来源的聚合视图：

所有 books.deleted_at != null 的 Book（主要内容）。

（可选）所有被归档的 Bookshelf / Library 里，系统自动建议的“可清空内容”。

（备用）对未来 image / media 等「孤儿资源」的回收站入口。

在 Basement 里允许的操作：

恢复 Book（默认行为）

永久删除 Book（同时删除其 Blocks）

按 Library / Bookshelf / 时间 / tag 过滤

Block 一般不直接出现在 global Basement，只在本 Book 的局部 Trash 里管理，避免界面爆炸。

四、一张“谁可以删 / 恢复”的规则表（你可以直接抄进 RULES）
层级	用户操作	系统行为	恢复方式
Library	Archive	libraries.archived_at 设定时间；隐藏在主列表	在“已归档 Library”列表里恢复
Library	Delete(真删)	只通过后台脚本/管理员工具，不在前端提供	不支持（需要备份恢复）
Bookshelf	Archive	类似 Library，archived_at 设定；下属 Book 被标记为从属归档	在“已归档 shelf”列表里恢复
Bookshelf	Delete(真删)	同上，暂不暴露给普通用户	同上
Book	Delete	deleted_at 设定；blocks 同步软删除；出现在 Basement	从 Basement 一键整本恢复
Book	Permanent del	只能在 Basement 执行；彻底删记录和 blocks	不可恢复
Block	Delete	deleted_at 设定；只在本 Book 的 Trash 视图出现	在本 Book 内单条/多条恢复
Block	Permanent del	在本 Book 的 Trash 页面“清空”时执行	不可恢复
五、这套规则的“麻烦度”与收益

复杂度上：

代码层面：就是在四个表加 deleted_at / archived_at 和 deleted_reason，
加两三个视图（Basement + per-book Trash） + 几个 service 方法（delete/restore cascade）。

只要你清楚谁是“父”，谁同步软删 / 同步恢复，就不会太乱。

收益上：

用户心智简单：

“作品（Book）被删了 → 去 Basement 找。”

“某段翻译弄丢了 → 在当前 Book 的小回收站找。”

“整个空间不再用了 → Archive Library 就好，不担心数据丢失。”

你在和面试官 / 用户讲解时，也能讲出一套很清楚的故事：

Wordloom 有三层防线：
归档保护空间结构、Basement 保护作品、局部回收站保护细节。

如果你之后想，我可以帮你把这一套写成一个 Plan_16_VaultDesign 的简版规则段落，直接贴到你现有的 RULES/ADR 体系里，这样你以后改代码就有“契约文本”可以对照。