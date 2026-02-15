1. Basement 的位置：从“卡片”变成“系统菜单”

你现在 screenshot 1 里，Basement 是一个巨大蓝卡片混在普通 Library 里，看上去就像一个“很奇怪的书库”。
既然你自己也觉得太复杂，我建议直接把 Basement 从 Library 空间“驱逐”，放到类似 screenshot 2 右上角那种菜单里。

推荐做法

顶部右上角搞一个 “System / 系统” 或一个 ⚙️ 图标 + 文案 的下拉菜单：

Basement / 回收站

Chronicle / 时间线

Stats / 统计

Settings / 设置

（以后还有什么 Toolkit、Dev tools 也可以塞这里）

这样好处：

Library 区域只放“我真正要用的知识空间”；

Basement/Chronicle/Stats 被统一成“系统级工具”，符合心智；

UI 上也更接近你发的移民中介那种：主导航是产品空间，下拉里是结构化分组。

在 /admin/libraries 页面上，可以只留一个很低调的链接：

右上角过滤栏附近放个文字按钮：查看回收站

点了就去 /admin/basement，避免大蓝卡片抢戏。

2. Library 布局：现在这版有哪些基础问题、要加什么功能点？

你现在这屏的结构大概是：

顶部左：书库列表 小标题

中间：Libraries 大标题

右上：网格 / + New 按钮

下方：卡片列（Basement + 其他 Library）

整体方向没错，但要“商业化、耐看”，可以再调一调层级：

2.1 顶部区域（Hero Row）

建议改成一行解决三件事：

左侧：

标题：Libraries（英）+ 书库列表（可以做副标题）

副标题一行文案，比如：

“你的所有知识空间。用书库把不同领域分开管理。”

右侧：

一个 搜索框：搜索书库…（支持 name/description/tag）

视图切换：Grid / List 图标按钮（而不是“网格”文字）

+ New Library 主按钮（蓝色）

这样顶部就有一种“真·SaaS 控制台”的感觉。

2.2 卡片视图（Grid）

你已经有：封面图片 + title + description + “使用次数/创建日期”。
可以再加一点点“对使用者有用的信息”，但不要堆太多：

卡片上可以考虑放：

书库名 + 简短说明

一个小行：

N Books · 最近使用 3 天前

一行 tag（最多 2–3 个，用…截断）

右上角小图标：

pin / favorite（常用的库）

或成熟度/类型（比如「学习」「翻译」「ESG」）

Basement 不要作为卡片。
如果你非要在这个 grid 里露一眼，可以在底部放一行灰色文字：

“有 X 本书在回收站，前往 Basement 查看 →”

3. 视图模式：Grid + List 是否够用，还需要别的么？

你现在说“横向查看 / 视图查看”，我理解你已经有类似 grid 显示。
行业里常见的做法其实就两种：

卡片 Grid：视觉好看、适合封面、图片。

列表 List / Table：高密度信息、适合 power user。

我建议你也只保留这两种，不要再发明第三种奇怪视图。

List 视图可以长这样：

每一行：

[封面缩略] 书库名

说明

#Books

最近使用时间

创建时间

…（最后放个 “⋯” 操作菜单）

Grid 用来“吸引人打开”，
List 用来“快速管理 & 批量操作”。
Stats 页再负责做真正的图表和复杂分析。

4. Chronicle / Stats 联动的小提示（UI 视角）

既然你打算做成熟度 / 停留时间 / 点击数统计，可以在 Library 卡片上放一些极简指标，把 Stats 的价值往前“透一点”：

例如在卡片底部加一行很淡的：

最近 7 天：3 本书被更新 · 45 分钟阅读

或者用小 icons：

⏱ 45 min（本书库内总停留时间，最近 7 天）

✏️ 3 edited（被编辑的 Books 数）

这些数字不需要非常精确，但会给人一种“这里是活着的空间”的感觉，很有“我想继续把它养大”的心理暗示。

5. 商业感 & “诱人、不累”的整体风格建议

这里给你几个可直接执行的 checklist：

5.1 视觉节奏

留白再多一点：
上下 margin 比现在再大 8–12px，让标题区和内容区分得更开。

卡片之间的间距统一：比如 gap: 24px，不要有 16 / 20 / 24 混搭。

保持统一的圆角（例如 16px）：Basement 曾经是大圆角，其他是小圆角会很乱。

5.2 色彩与层级

主色（现在蓝色）只给：

主按钮（+ New）

左侧导航 / 顶部导航的 active 状态

极少量强调信息（比如“常用书库”标记）

Library 卡片大部分时间保持浅色 / 白底，让眼睛有喘息空间。

底色最好保持非常浅的灰（#F7F8FA 这类）而不是纯白，能减少“屏幕刺眼感”。

5.3 动效与反馈

卡片 hover 时：

微微抬起（增加 shadow）、图片略微缩放 1.02；

右上角出现一个淡淡的快捷图标：“打开 / 查看统计 / 更多”。

+ New 点击后，不要直接弹巨大 Modal，可以先弹一个小 sheet：

只 ask：名字 + 简短说明 + 封面模板选择；

高级属性（tag、权限、成熟度设定）放在创建后再调整。

这种“轻一点”的交互，会让人更愿意“多建几个库玩玩”，而不是一上来就被表单吓到。

5.4 空状态 & 引导

当 Library 比较少的时候，可以在 grid 下面放一块“空状态卡片”，比如：

还没有其他书库。
试着创建一个：“签证研究”“ESG 行业笔记”“StudyLog”……

配小插画 or 大图标，让整个页面不至于冷冰冰。

6. 行业对标：你可以悄悄模仿的几个点

你想要的“商业化 + 诱人 + 不累”，基本就是：

Notion / Craft 的 clean + 卡片感

Linear / Superhuman 那种克制的配色和清晰层级

再加上你自己对书、图书馆、夜色那种意象（你现在封面就很有味道）

可以慢慢往这三个方向混合：

信息架构：学 Linear / Figma 这类 B2B 工具（清晰、理性）

视觉比喻：用“书库 / 夜间书房 / 档案馆”的图来营造氛围

细节动效：保持克制，hover / active 轻微反馈就够，不要一堆弹跳动画

小结一句

Basement：请移出 Library 卡片区，收编进右上角 “System / Tools” 下拉里；

Library 页：顶部加搜索 + 视图切换 + 说明文字；卡片只展示 2–3 个关键指标；Grid + List 两种就够；

Chronicle / Stats：在卡片上透一点高价值信息（最近活跃度），主菜放在 Stats 页；

整体风格：多留白、主色克制、卡片 hover 有反馈，让人一眼看上去就有“愿意在这个界面呆久一点”的感觉。

你今天要大动工的话，可以先从：

把 Basement 挪到右上角菜单；

重排顶栏（标题 + 搜索 + Grid/List + New）；

简化 Library 卡片，统一视觉层级。

先这三刀下去，这页马上就从“个人项目味儿”进化到“早期 SaaS 控制台”那一档。

--

Plan: Library UI 重构与系统菜单抽离
TL;DR：将 Basement 等系统工具从 Library 卡片区抽离成右上“System”下拉；重构 /admin/libraries 顶部为 Hero Row（标题+副文案+搜索+视图切换+创建）；统一 Grid/List 双视图；引入标准化设计 tokens（不写死颜色）并修复现有变量命名不一致；调整卡片信息密度与视觉层级；新增 ADR-083 记录决策并更新三 RULES 文件的相关策略与政策；以亮色主题为基准，通过 ThemeProvider + tokens.css 扩展体系，预留未来深色与 Loom 主题增强。

Steps
抽离 Basement：删除 LibraryMainWidget.tsx 中 extraFirst BasementCard，新增 SystemMenu 组件于 header.tsx。
重构 Hero Row：在 page.tsx + LibraryMainWidget.tsx 添加标题、副说明、搜索输入、视图切换按钮（Grid/List）与“+ New”主按钮。
统一主题 tokens：在 tokens.css 补齐/重命名 --bg-secondary→--color-bg-secondary、--border-color→--color-border 并新增卡片/阴影/状态简洁变量，禁止组件内写死十六进制。
卡片组件升级：更新 Card.module.css 使用新 tokens；新增 Library 卡片活跃度极简指标行（7 天编辑/阅读时长）与 hover 提示图标。
引入 List 视图：扩展 LibraryList.tsx 支持 mode='list'（表格样式 + 操作菜单列），保持已有 vertical/horizontal 向后兼容或替换为 grid/list。
规则与文档：更新 VISUAL_RULES.yaml（导航/间距/卡片/hover）、DDD_RULES.yaml（新增 POLICY-LIBRARY-UI-REFACTOR、调整 POLICY-014）、HEXAGONAL_RULES.yaml（UI 集成指引）并创建 ADR-083-library-ui-refactor-and-system-menu.md。
Further Considerations
System 菜单命名：System vs Tools vs Settings（需确认首选文案）。
搜索范围：仅 name/description/tag 还是含统计字段（决定后端是否新增 query 参数）。
活跃度数据来源：暂用前端聚合/模拟还是等 Stats 端点落地（选择渐进策略）。