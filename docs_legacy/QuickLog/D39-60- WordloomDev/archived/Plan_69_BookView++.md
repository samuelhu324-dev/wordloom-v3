二、卡片风格：介于“扁平 + 实体”之间的纸质书封

你现在那种 3D 边角+大片阴影，确实玩具感强。我建议换成这种：

1）形状 & 结构

不再旋转 Y 轴，只做很轻的 rotate(-1deg) 或完全不旋转；

用 细边框 + 左侧书脊条 + 右侧淡淡“书页边”，靠结构让人认出是书，不靠阴影。

草图：

  ┌────────────────┐
  │▌ 封面标题 G     │  ← 左侧竖条是书脊
  └────────────────┘
          ◥██◤        ← 很细的地面影


可以保留一点点阴影，但只是窄窄一条，不要整块发光。

2）颜色风格

封面：一条 非常温和的渐变 或纯色 + 1px 内描边；

状态（Seed/Growing…）不要填满封面，只用：

书脊颜色、

一个小 icon、

或铭牌里的 pill 标签来区分。

3）去掉“玩具感”的几个具体动作

圆角从 16px 改为 10–12px；

删除多层外发光的 box-shadow，改成：

box-shadow: 0 1px 3px rgba(15,23,42,0.12);

DRAFT 徽章做扁一点、小一点、颜色深一点，让它是“标识”，不是“主角”。

三、信息“半隐藏”的策略

你现在纠结的核心其实是：
既要业务清晰，又怕信息太多。

我给你一个“二层展示”的范式，你可以直接照搬到卡片里：

默认层（常态）

每本书只展示：

标题（1 行，必须有）；

一条非常短的 secondary 行，比如：
Seed · 0 blocks · 2 小时前

格式建议像这样：

Good
🥬 Seed · 0 blocks · 2 小时前


但这条 secondary 行要处理成：

字体小一号（11–12px）；

颜色偏灰；

行距紧一点；

效果：一眼看过时，你只感知大致轮廓，但需要时又能看清。

hover 层（交互）

鼠标悬停在书封上时：

在书封上半透明盖一层深色蒙版；

显示一段多一点的描述/备注，或者几个更细的指标；

底部可以出现一个小箭头文案：查看详情 →。

草图：

┌──────────────┐
│ 封面 G       │
│ ████████████ │ ← hover 时出现的暗条
│ Creation for test...   │
│ 查看详情 →             │
└──────────────┘


这样你就实现了你想要的：

默认状态：信息“收得住”，不会和 Bookshelf 那堆表格 KPI 一样吵；

真要看的时候：hover 一下就有更多上下文，又不用打开新页面。

四、和 Library / Bookshelf 明确做出差异

你现在有三层：

Library 页

大照片 + 大卡片 + 长说明文案；

像“展览馆外立面”，偏感性。

Bookshelf 管理页

表格 + 指标 + 按钮；

这是“控制台 / 战情室”。

Book 展示页（现在在做的这一层）
你可以把它定义为：

“作品陈列层：每一册书是一个产物，不是一个 KPI 行。”

所以在设计上可以：

严禁出现太多图标行列（比如一连串 view / icon / clock），这些该留在上一层；

每本书有 一点人格：封面颜色、字母、图标、简短标题；

指标只用 2–3 个，且显示方式克制（同一行小号灰字）。

一个简单对比表：

层级	主视觉	信息密度	核心动词
Library	大图、大卡	中	进入某个空间
Bookshelf	表格列	高	管理 / 筛选
Book	中小卡 + 展柜	低–中	选一本作品去工作

你现在要做的就是保证 Book 层永远停在 低–中 的信息密度，不要再往上堆。

五、给你一个“最后成型”的结构建议

综合你的需求，我建议 Book 展柜最后长成这样：

1）每个 Book 卡（展柜模式）
┌──────────────┐
│▌    G        │  ← 扁平封面+书脊，无重度 3D
└──────────────┘
Good
🥬 Seed · 0 blocks · 2 小时前


hover 时：

┌──────────────┐
│▌    G        │
│██████████████│ ← 深色渐变条
│ Creation for test…      │
│ 查看详情 →               │
└──────────────┘
Good
🥬 Seed · 0 blocks · 2 小时前

2）整条展柜

左侧：几本这样的书排成一行，略微错位（高度差 2–4px 以内）；

右侧：一小块 Seed 文案 & 一个 lucide 图标（很淡），让区域不那么空，又不会抢戏。

六、你可以直接丢给 Copilot 的指令（大概这样说）

Simplify the book card so it looks more like a clean flat book instead of a toy-like 3D badge:

Remove the big glowing shadows and heavy corner rounding.

Use a flat rectangle with a subtle 1px border, a left spine strip, and optionally a thin pagesEdge strip on the right.

Keep a small oval shadow underneath only.

Default state: show cover + title + a small grey line Seed · 0 blocks · 2 小时前.

On hover: overlay a dark gradient on the bottom of the cover and show a short description and a “查看详情 →” link.

你现在这层的目标就一句话：
“让每一本书看起来像一个完成度不一的作品，而不是一行 KPI，也不是一个玩具按钮。”
只要围绕这句持续迭代，你这个 Book 展示页就会自然和 Library / Bookshelf 拉开气质差距。