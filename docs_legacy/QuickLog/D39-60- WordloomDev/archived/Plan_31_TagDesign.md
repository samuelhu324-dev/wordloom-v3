Tag 行（副身份 / 分类）——放在你现在 Description 的位置

用 1–3 个小 chip 概括这个 Library 的“类型 / 领域 / 语言对”；

这行是我们要重点改造的，下面详细说。

统计行 + 创建时间行（状态信息）

下面那两行 书架 / 图书 / 最近活动 / 浏览 + Created … 保持现在结构就很好，

它们是“状态/活动”，和 Tag 的“分类”是两个维度。

这样用户扫一眼卡片，信息顺序会是：

这是谁 → 属于什么类别 → 最近有多活跃 / 有多少内容

很像 Notion / Linear 那套结构。

> **2025-11-22 实装同步**：Admin → Libraries 的「新建 / 编辑书库」弹窗现已在“名称”下方提供 Tag 选择器，支持搜索或快速创建 1–3 个标签（低饱和 chip），与本设计稿所述的 Option A chips 行完全一致。保存后立即调用 `/libraries/{id}/tags` 替换关系，卡片、副标题以及列表视图同步渲染这些标签。
>
> **QA 速记**：
> 1. 新建书库 → 选择 1–3 个标签并保存，回到列表应立即看到 chips；
> 2. 编辑已有书库 → 清空标签再保存，确认卡片 Tag 行被置空；
> 3. 弹窗输入不存在的标签名，Enter 新建后保存，刷新页面应仍显示该标签；
> 4. 在 Grid/List 视图之间切换，Tag 行内容保持一致。

二、Tag 行怎么设计：低调 + 知识管理感
1. 布局

放在标题正下方，独占一整行；

左对齐，从标题的起始位置对齐往右排；

最推荐的样子是：

Labs              📌
翻译实验室   学习日志   EN-ZH

2. Tag 的样式建议

走“轻量 chip”路线，不要太花：

形状：小 pill，圆角比较大（比如 9999px）；

字号：比正文小半号，如 12px / 0.75rem；

颜色（推荐两种做法）：

方案 A：全部浅灰描边，文本颜色略深

边框：#E5E7EB（浅灰线）

背景：#F9FAFB（几乎白）

文本：#6B7280（灰）
→ 非常低调，整张卡还是靠封面和标题撑视觉，不会太“彩虹”。

方案 B：按“类型”有轻微色差（知识管理味更强一点）

领域类：浅蓝边 + 蓝字 翻译实验室

用途类：浅灰 学习日志

语言对：浅紫 EN-ZH
颜色都压得很轻，不要全饱和。

图标：可以只在第一个 Tag 上带一个小 icon，如：

📚 翻译实验室
后面的 Tag 就纯文字，避免太吵。

3. 数量 & 截断

每张卡最多展示 3 个 Tag；

超出的用一个 +2 chip 表示：

翻译实验室 学习日志 EN-ZH +2

鼠标 hover 在 Tag 行，tooltip 展示全部 Tag 列表。

这样行高固定，卡片不会因为 Tag 太多变得乱七八糟。

三、和行业对齐一下（顺便验证我们的方案）

几款典型产品的做法：

Notion 数据库 Gallery

卡片：封面 + 标题 + 若干属性（Status / Tag）的小行；

属性用的是小 chip 或文本，这一行和你要做的 Tag 行几乎一样。

Linear / Asana / ClickUp

卡片：标题 + 一行 labels（状态 / 类型 / 负责人）；

labels 都是低饱和色的 chip，不会抢走标题注意力。

你旧版 Wordloom（截图 1）

标题+说明下方放 Tag，很像“Day_XX 卡片”；

这次我们其实是把那套风格提升、简化之后应用到 Library 层。

所以我们现在这版“标题 + Tag 行 + 统计行”的布局，其实就是对齐了这类工具的标准做法，只是风格换成了 Wordloom 的“书房 + 档案”路线。

四、结合 Wordloom：Tag 推荐承担的“副标题”角色

既然你想用 Tag 替代副标题，那可以给自己约几条“Tag 的语义规则”（以后写 RULES.yaml 时可以写进去）：

一类 Tag 表示领域 / 主题

翻译实验室 ESG 法律 学习 …

一类 Tag 表示用途 / 模式

学习日志 客户档案 术语库 翻译项目 …

一类 Tag 表示语言 / 形式

EN-ZH ZH-EN 多语言

这一类甚至可以统一有个小 🌐 icon。

卡片 Tag 行通常选：

1 个领域 + 1 个用途 + 1 个语言对

比如：翻译实验室 学习日志 EN-ZH

这样一眼就知道：

这是个什么类型的空间 → 用来干嘛 → 针对什么语言/内容。

非常“知识管理系统”的味道。

五、List 视图也别忘了同步一下

横向列表那一版，建议：

第一列：小封面 + Title；

第二列：Tag 列，展示最多 3 个 chip（和卡片一致）；

Description 就不在列表里展示了，只在详情页 / tooltip。

这样两种视图的“副标题信息”都由 Tag 承担，用户在切视图时认知不会断裂。

总结一条可以写进设计文档的话

Library 卡片：标题下方使用一行低饱和的 Tag chips 作为“副标题”，每卡显示 1–3 个，代表领域、用途和语言对。Tag 视觉上轻量，不抢封面和标题的注意力；说明（description）退到详情页和 tooltip 中。

这一套既符合 Notion/Linear 等知识管理工具的行业习惯，又保留了 Wordloom 作为“翻译+档案书房”的安静、专业气质。

//////////////////////////////////////////////////////////////////////////////////

好问题，这块如果一开始不想清楚，后面很容易变成“标签垃圾场”。我分三块说：一个 tag 多长合适、tag 怎么贴 / 怎么管、Wordloom 里 seed/growing/stable/legacy 应该怎么定位，顺便对照一下业界做法。

一、一个 tag 最多写多少字比较合适？

这里有两个层面的“上限”：

1）界面上的“视觉上限”

成熟产品一般都遵循几个原则：

tag 本身尽量短：

中文：2–6 个字最舒服，8 个字已经很长了；

英文：1–3 个词，总长度 12–18 字母以内。

卡片展示时：

每个实体只展示 1–3 个 tag，多了就用 +2 这种聚合；

超长 tag 用省略号截断。

你可以在 UI 里直接做个硬规则，例如：

字符超过 16 个就不允许保存，给个提示：

标签过长，请控制在 16 字内。

展示时最多显示 10–12 个字符，其余用 …，hover 显示完整。

2）数据库/模型的“硬上限”

技术上可以给 tag 的 name 字段设个 长度限制：
比如 varchar(32) 或 varchar(64) 就够用了；

但用户能感觉到的是“16 字左右的软限制”，
你可以再宽一点存起来，UI 上截断即可。

推荐给 Wordloom 的规则：

设计规范：

「标签名建议 ≤ 8 个汉字 / ≤ 16 字母，超过拒绝或提示」；

数据库字段：

name varchar(64)，保证安全有余地。

二、tag 是怎么贴上去、怎么管理的？（业界通用模式）

成熟产品里，大致是这几层：

1）“怎么贴上去”：常见交互

多选下拉 + 搜索（Notion / Linear / Asana 都是这个）

点击“标签”区域 → 打开下拉列表；

输入时搜索现有标签；

按 Enter 选择 / 切换；

若没有匹配项：给一行 创建新标签 “xxx”，点一下就新建。

快速添加模式（Obsidian / VSCode）

直接在文本里写 #tag，系统自动识别；

这个更适合 block 内标签，对 Wordloom 可以留给之后高级用法。

在 Wordloom 的 Library/Book 卡片上，推荐先用多选下拉 + 搜索这种，够直觉，也方便你后面做过滤。

2）“怎么管理”：避免标签爆炸的机制

业界三个典型套路：

完全自由标签（free tag）

Obsidian / Evernote 早期：想叫啥叫啥；

好处：灵活；坏处：学习、学习/日志、学习日志 变成三个不同标签，灾难。

受控词表（controlled vocabulary）

例如状态：Todo / Doing / Done，用户不能乱增；

常见在“状态 / 阶段 / 类型”等字段上，通常用单选而不是多选；

混合方案：系统标签 + 用户标签

比如：

系统字段：Status、Priority（单选、固定枚举）；

用户字段：Tags（多选、小库）。

我建议 Wordloom：

Book 的 seed/growing/stable/legacy

这类是“生命周期状态”，

应该做成 单选枚举字段（Status），而不是普通 tag。

这个字段跟业务规则、统计强绑定（比如 Stable 才算完稿）。

另外再有一组用户可编辑的 tag

用来标记主题、项目、来源，比如：

法律 ESG 练习 客户A

这一组才是我们现在讨论“贴在卡片下面”的那些 Tag。

简化一句：
Status（seed/growing/stable/legacy）≠ Tag。
Status 是业务状态，Tag 是用户自己打的“分类/标签”。

3）集中管理页面（Tag Manager）

很多工具在设置里会给一个“标签管理”的页面，用来：

查看当前所有 tag 列表；

修改标签名；

合并标签（学习日志 和 学习/日志 合并为一个）；

设定颜色（如果你有彩色 chip）；

查看被多少 Library/Book 使用。

你可以以后在「Settings / 全局配置」里面做一个：

Tag 管理器

只对用户自定义 tag 起作用；

系统枚举（seed/growing…）在另外一处“系统规则”里管。

短期可以先不做管理器，用多选下拉创建 / 删除就够；
等 tag 数量多到你觉得乱，再开这个页面也不迟。

三、结合 Wordloom 现在的情况，我帮你拍个“临时规范”

你现在已有：

Block/Book 级别的 seed / growing / stable / legacy；

未来想在 Library / Book 上加 Tag 用来做“副标题”。

可以先把规则写成这样（以后写 RULES.yaml 也能直接抄）：

Status 字段（Book 专用）

类型：枚举，取值 = seed | growing | stable | legacy | archived（举例）

多选：❌ 不允许，必须单选；

用途：驱动统计、过滤（只查 stable）、删除策略等。

Tags 字段（Library / Book 通用）

类型：多选标签；

每条实体最多展示 3 个（超出用 +N）；

每个标签名建议 ≤ 8 汉字 / 16 字符；

创建方式：多选下拉，支持搜索；不存在时允许快速创建；

存储结构：

一张 tags 表：id, name, color, created_by, created_at...

一张中间表：book_tags(book_id, tag_id)、library_tags(library_id, tag_id)。

展示策略

Library 卡片：标题下方展示 Tags（chip），Status 别放在这里；

Book 列表 / 卡片：可以同时展示 Status（小彩点+文字）和 1–2 个 Tags。

这样你既对齐了行业里的“状态 + 标签”双轨模式，又保住了 Wordloom 里 seed/growing/stable 这些对翻译流程很重要的语义，不会跟一般 Tag 搅在一起变成一锅粥。

一句收尾：

tag 本质是“用户维度的分类”，要短、要少、要能合并；
seed/growing/stable 这种则是“系统维度的状态”，该进枚举，就别放进 Tag 堆里。
先把这两层分干净，后面无论做 Dashboard、Chronicle 还是搜索，都会舒服很多。

//////////////////////////////////////////////////////////////////////////////////

Status（seed / growing / stable / legacy）应该是 Book 这个聚合里面的“值对象 / 枚举字段”，属于 Book 所在那个领域，不是像 Tag 那样单独一个聚合。

你现在的结构可以这么理解：


Tag：已经有独立的 domain / 聚合（因为要跨 Library、跨 Book 复用，用户还能自己增删改）


Status：描述的是「这本 Book 的生命周期位置」，只和这本书本身的规则强相关


所以在 DDD 里它更像这两种东西之一：


Book 上的枚举字段
type BookStatus = "seed" | "growing" | "stable" | "legacy"
class Book {
  private status: BookStatus;
}



一个小 Value Object（值对象）


封装状态值 + 允许的流转规则：


class BookStatus {
  private readonly value: "seed" | "growing" | "stable" | "legacy";

  canTransitTo(target: BookStatus): boolean {
    // 比如：不能从 legacy 回到 seed
  }
}



这俩本质上都“算在 Book 聚合里”，属于 Library/Bookshelf/Book 这个 bounded context 的领域模型的一部分，而不是单独冒出来一个 StatusAggregate、StatusDomain。

为什么不把 Status 做成像 Tag 那样单独的聚合？
看你的用法：


seed / growing / stable / legacy 是 系统定义的生命周期；


这些值写进 DDD_RULES / SYSTEM_RULES，而且会驱动：


统计（只算 stable 的句子）


删除策略（legacy 才能被回收？）


工作流（growing → stable 需要满足某些完成条件）




这类东西有几个典型特征：


不是用户自由创建的（不会让用户自己发明一个 半熟 状态吧）；


跟 Book 的不变量/规则绑死，而不是跨很多领域共享；


状态的数量变化不频繁，更多体现为“规则更新”。


→ 在 DDD 里它就应该贴着 Book 待着，当作 Book 内部状态，而不是像 Tag 那样抽出去。
只有在这两种情况下，才值得考虑给 Status 一个单独的领域/聚合：


你以后要做“自定义工作流”：


每个 Library 可以定义自己的状态集合，比如：草稿 → 校对中 → 待客户确认 → 已发布；


用户可以在 UI 里配置这些状态，并拖拽排序；


不同 Library 的状态集合不一样。
⬅ 这时会长出一个 Workflow / StatusDefinition 聚合。




Status 本身有大量附加行为：


比如每个状态有 SLA、通知策略、权限规则……


变成一个“配置中心”。




按你现在的需求，完全用不到这么重。

帮你按层级摆一下位置，方便记到规则里
可以写进你的 DDD 说明文档，大致是：


Bounded Context：WordloomCore（Library/Bookshelf/Book/Block 所在域）


Aggregates：


Library


Bookshelf


Book


Block




Value Objects / Enums：


BookStatus（seed / growing / stable / legacy）


…（将来可能有 BlockRole 之类）




另外一个上下文：Tagging


Aggregate：Tag


中间表 / 关联：BookTag, LibraryTag


这是“用户自定义分类”的世界




一句话版关系：


Tag：自己一整个小宇宙，跨很多东西复用，已经是一个 domain / 聚合；


Status：Book 自己的“心情 / 生命阶段”，就是 Book 这个聚合的一部分，不单飞。


以后你在代码里也可以用这个原则：
“描述对象本身生命周期的东西 → 放在聚合里；
描述用户如何归类/找到这个对象的东西 → 放在 Tag / 外部聚合里。”
