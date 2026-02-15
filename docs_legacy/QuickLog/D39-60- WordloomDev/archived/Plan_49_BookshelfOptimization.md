0. Bookshelf 列表页的定位

这是 单个 Library 下所有 Bookshelf 的“审计工作台”视图。

目标：一眼看到每个书架的：

名字 + 标签

成熟度（Seed/Growing/Stable 分布的“概况”）

核心使用数据（总书本数 / 浏览数）

最近活动时间

1. 列表结构（每一行）

建议一行拆成两层信息：

第一行

封面：小缩略图（现在用 Library 封面 / 图标即可）

名称：Bookshelf.name

状态 pill：[ACTIVE] / [FROZEN]（一开始可以只用 ACTIVE）

标签区：最多展示 2–3 个 Tag chip，超出显示 +N

第二行（关键指标）

从左到右示例（图标只是示意，用 lucide 实现）：

📚 总书：total_books

🌱 Seed：seed_count

🌿 Growing：growing_count

📘 Stable：stable_count

👁 浏览次数：view_count

🕒 最近活动：Last activity: 1 day ago / 暂无活动

如果觉得一行太挤：Seed/Growing/Stable 可以只放一个“成熟度评分”字段，详细分布放到详情页。

2. Tag 规则（前端表现）

展示规则

每行最多显示 2–3 个 tag：

超出的用一个 chip 显示：+2

每个 tag 名称最长 12 字符，超出加 …：

法律条款学习笔记 → 法律条款学…

Tag 样式：小圆角 chip，浅灰/浅蓝边框 + 半透明背景，字体偏小。

Hover 行为

鼠标移到 Tag 上，显示 tooltip：

内容：Tag.name + Tag.description

如：

名：翻译

描述：与翻译实践相关的书架 / 书本

3. Tag 的后端/DDD 结构（简版）

聚合划分：

Tag 作为独立聚合：

tags 表：id, name, color?, description?

三个中间表：

library_tags (library_id, tag_id)

bookshelf_tags (bookshelf_id, tag_id)

book_tags (book_id, tag_id)

领域规则：

Library / Bookshelf / Book 只引用 tag_id，不自己存 tag 名。

Tooltip 文案只使用 Tag.description，不增加额外业务逻辑。

4. 状态 / 成熟度设计
4.1 Book 状态（成熟度）

Book 的 status（领域内定义）：

Seed：草创/灵感池

Growing：进行中/扩展中

Stable：已定稿/整理完成

Legacy（或 Basement）：历史、归档、被移出

4.2 Bookshelf 列表中的成熟度统计字段

每个 Bookshelf 聚合一个 summary：

total_books = 所有非删除 book 数量

seed_count

growing_count

stable_count

legacy_count（可选，先不展示在主列表也行）

列表页视觉上：

📚 total_books

🌱 seed_count

🌿 growing_count

📘 stable_count

其它放详情页或 tooltip。

5. Status（Active / Frozen）

领域层：

BookshelfStatus ∈ {ACTIVE, FROZEN}

前端表现：

在名称右边显示一个 pill：

ACTIVE → 绿色/灰绿小标签

FROZEN → 灰色小标签（后面再做）

页头的 Filter 加一个状态筛选：

全部 / 仅 ACTIVE / 仅 FROZEN

先别新增整列，只用 pill + 筛选就够。

6. 图标和 tooltip 规范

统一规则：

每个 lucide 图标组件统一收一个 title 或 aria-label，用于浏览器默认 tooltip。

文案示例：

🌱："Seed · 草创阶段书本数量"

🌿："Growing · 进行中书本数量"

📘："Stable · 已稳定书本数量"

📚："总书本数"

👁："浏览次数"

🕒："最近活动时间"

操作列里的图标（编辑/删除/详情等）同样加：

✏️："编辑书架"

🗑："删除书架（不可恢复）"

🔍："查看详情"

7. 交互与后续扩展

当前版本：

保持“单 Library 的 Bookshelf 列表”只做一件事：
让你快速扫描 &跳转到重要书架。

不做跨 Library 的图表/交叉分析（放到 LibraryLog / Overview）。

未来 可以在列表的顶部或另一个页面做：

按 tag / status / mature level 的筛选

简单的统计卡片（比如“本库中 Growing 书架/书本数量”）

你如果要直接给 Copilot 开工，可以配一句类似命令说明：

“请按以上字段和规则重构 Bookshelf 列表页：保留一行视图结构，左侧是封面 + 名称 + 状态 pill + 2–3 个 Tag，右侧是总书本数、Seed/Growing/Stable 数量和浏览次数，并为所有图标和 tag 加上 tooltip。”

这样它基本就能照着这份规格往下实现了。