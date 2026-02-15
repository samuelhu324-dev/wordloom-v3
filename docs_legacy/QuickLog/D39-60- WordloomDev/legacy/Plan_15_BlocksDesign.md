好，终于杀到 真正的 block 页面 了，这一页要做舒服，你后面所有“爱不爱在 Wordloom 里写东西”基本就看它了。

我按这几个层次来讲：

整体布局：Book 页面骨架

Block 模型：通用 block + title block 怎么铺路

写作体验：怎么让人“想在里面干活”

和其他 Book / 书架联动 & 左侧标题视图

1️⃣ 整体布局：Book 页面骨架

先把大结构定下来，不然 block 长啥样都很散。

建议：经典三栏 + 顶部 header

┌────────────────────────────────────────────────────────────┐
│ Breadcrumb:  Library / Bookshelf / Book name      [Chronicle]│
│ Book Title（TitleBlock）                          [Move][⋯] │
└────────────────────────────────────────────────────────────┘
┌─────────────左：大纲────────────┬──────中：Block Editor──────┬────右：抽屉/对比────┐
│  Section list by title / Hn    │  所有 Block 纵向排列         │  相关 Book / 对比视图 │
│  - 1. DevSystemMigration       │  - Title block              │  - 当前书的 meta      │
│  - 2. UIDesign                 │  - text / checklist / …     │  - 同书架其它 Books   │
│  - 3. ...                      │  - …                        │  - 参考书只读预览     │
└────────────────────────────────┴─────────────────────────────┴───────────────────────┘


上面 header：

breadcrumbs（能点回 Bookshelf / Library）；

Book 名 + 状态（Seed/Growing/Stable）+ 少量操作按钮（Move / Open Chronicle）。

左侧：基于 title blocks / heading block 的大纲视图（类似你现在 v2 的小标题，但更纯净）。

中间：唯一的编辑区，所有 block 的家。

右侧：可折叠抽屉：

用来做“临时拿别的 Book 出来对比”/ 显示相关 Book 列表 / 未来扩展引用。

这套布局跟 Notion / Linear / 现代 IDE 很像，好处是用户一看就知道怎么玩，不需要重新学习。

2️⃣ Block 模型：通用 block + TitleBlock 怎么铺路

你现在要的是 “通用 block + title block，后面所有类型都能从这俩长出来”，那就别上来造二十个实体。

2.1 通用 Block 核心字段

逻辑上先只认一种基础模型：

Block:
- id
- book_id
- type: "title" | "text" | "todo" | "quote" | "code" | ...
- content: 富文本 / markdown-ish 字符串
- props: json（checkbox 状态、语种、代码语言等）
- order: 排序
- parent_id: 可选（以后支持嵌套）


TitleBlock 只是 type = "title" 的 block：

约束：一个 Book 至多一个，且必须在 order=最前。

UI 上：渲染得像页面标题，而不是普通段落。

2.2 第一批真的要实现的 Block 类型（先小后大）

为稳、简单，可以只上 3–4 种：

title：Book 标题（必有）。

text：普通富文本段落（你现在 v2 里最长用的那种）。

todo：勾选项（props 里一个 checked: boolean）。

heading（可选）：如果你希望左侧大纲更细，可以把小标题单独做成 block 类型。

后面什么“图片 block / 引用块 / 代码块 / Loom block”统统延后，但数据结构现在就留好 type + props 的口，不需要再改 schema。

3️⃣ 写作体验：怎么让人愿意长期在里面干活？

这个是“心理 +操作”的组合，最关键的是顺手。

3.1 编辑区的基本交互

尽量对齐行业的“肌肉记忆”：

Enter 新建同类 block，Shift+Enter 换行；

/ 打开 block menu：

/todo 转成 todo；/h1 转 heading；

左侧小“拖拽手柄”+“⋯”菜单：

拖动整个 block 调整顺序；

菜单里有 Duplicate / Turn into / Delete；

Ctrl+[ Ctrl+] 调整缩进（以后支持层级时直接用）。

这些行为越贴近 Notion/Obsidian，你自己的上手阻力就越小。

3.2 视觉 & 排版：让眼睛不累

宽度：中间编辑区固定一个“阅读宽度”（不要拉到全屏），左右留空白。

字体：正文选一套“耐读”的衬线/无衬线组合，你现在的 Wordloom 系就不错；

层级感：

title block 字号最大；

heading 次之；

block 之间留统一间距，todo 稍紧一点，看起来像一组任务；

分隔线/空行处理：用 block 自己表示分隔（如 divider），避免出现“三个空行”的乱感。

3.3 小工具：降低“启动门槛”

顶部/底部悬浮的“快速插入区域”：

像你 v2 里的“+ 检查点 / + 文本框 / 图片 / 标签”，

不用一模一样，但要留一排常用插入按钮。

Book 内搜索（Ctrl+F）直接定位到 block，并在左侧大纲高亮。

自动保存 + 保存提示（不用显式点“保存”，但给个“已保存到 xx:xx”的小提示）。

这些都是心理安慰：“我在这边折腾，不会丢”。

4️⃣ 和其它 Book / 书架的联动 + 左侧标题视图

你提的几个关键点：

“方便跳转书架、偶尔从抽屉里拿别的书架的书进行对比查看；左侧希望有一个按 title 查看顺序的视图。”

4.1 左侧：基于标题的“大纲视图”

可以这么设计：

数据来源：

type = "title" 的 block；

type = "heading" 的 block（如果你有）。

结构：

一级：1. DevSystemMigration、2. UIDesign…

子级：heading 的层级（H2/H3）。

功能：

点击跳转 & 滚动到对应 block，编辑区有轻微高亮；

当前所在标题自动在左侧高亮（根据滚动位置）；

支持拖拽调整排序（等价于重排标题所在的 block 顺序）。

这样你比现在 v2 的那种“章节盒子”更干净，也更接近书的真实结构。

4.2 右侧抽屉：和其它 Book 联动

不要把 cross-book 逻辑揉进中间编辑区，全部丢去右侧抽屉，这样结构更干净。

抽屉可以分几个 tab（以后逐渐填）：

Related：同 Bookshelf 里、相同 tag / 相似标题的 Book 列表：

StudyLog_D39-41

StudyLog_D42-45

点击默认在“右侧只读预览”打开，而不是直接离开当前 book。

Compare：

选一个 Book 后，右侧显示一个简化版阅读视图（只读）；

中间是你正在编辑的 Book，两边可以滚动对比。

这很像你现在的“多 record 卡片”，但视觉上要轻很多。

Bookshelf：

列出当前 Bookshelf 下的所有 Books 简要列表；

让你可以在不回上一页的情况下快速切另一本（编辑模式）。

4.3 快捷跳转到书架/Library

header breadcrumbs 必须可点：

Library A / Bookshelf StudyLog / Book D39-41；

同时在书名旁边，给一个小 “↗ Back to shelf” 的 icon，
这就是你说的“偶尔要跳回书架看全局”。

5️⃣ 一句话打包这个 Book 页设计

可以把你要做的总结成一句话：

Book 页面是一块三栏工作台：
左边是基于标题的大纲，中间是一条通用 block 流，右边是拿来横向对比和跳书用的抽屉；
数据层只需要通用 Block + TitleBlock，就可以支撑以后所有类型扩展。

先按这个骨架做最小 MVP：

实现 title / text / todo 三种 block；

左侧大纲只认 title；

右侧抽屉先只做 “同书架其他 books 列表 + 点击只读预览”。

等你用着顺手了，再一点点往里加高级 block 和 Chronicle 联动。这样既稳，又不会把自己锁死。