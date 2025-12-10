好，咱们把这个问题拆开来做一个“工程级”的方案，而不是随缘取个怪颜色。

0. 目标先说清楚

对 Wordloom 来说，Library → Bookshelf → Book 这条线，封面取色要满足：

同一 Library 的 Book 看上去是一套（同色系），视觉上“这个家族的书在一个书架上”。

颜色要 稳定：

不会因为刷新页面乱跳；

不会因为封面图细微变化就突然变成另一个奇怪颜色。

颜色要 安全：

不会脏灰、太暗、太亮看不清；

字体对比度够。

未来可以支持“手动改色”，但现在可以先自动。

所以核心思路是：Library 本身拥有一套稳定的 Theme Color，Book 不再自己算，只是“消费”这个 Theme。

1. 设计总方案：LibraryTheme → BookCover
1.1 数据结构上新增 Library Theme

给 libraries 表加几列（你用什么 DB/ORM，就用对应写法）：

-- 例子：PostgreSQL
ALTER TABLE libraries
ADD COLUMN theme_h int,         -- 0–360
ADD COLUMN theme_s int,
ADD COLUMN theme_l int,
ADD COLUMN theme_source varchar(20) DEFAULT 'auto'; -- 'auto' | 'manual' | 'fallback'


也可以再备份一份 HEX 方便前端用：

ADD COLUMN theme_hex varchar(7); -- '#RRGGBB'


原则：

每个 Library 只有一个主色（HSL / Hex 都可），所有 Book cover 都从这里衍生。

主题色一旦写入 DB，就完全由它驱动，不要每个 Book 自己抽色。

1.2 取色来源优先级

用户手动选色（未来扩展）

用户在“编辑书库”时可以手动点一个颜色 → theme_source = 'manual'。

从封面图自动抽取（当前阶段主要做这个）

用户上传/更换 Library 封面时，后端跑一遍取色算法 → theme_source = 'auto'。

没有封面图 / 取色失败 → 回退 palette

用 Library ID 做 hash，从一组预定义安全色中选一个 → theme_source = 'fallback'。

2. 如何“稳定”地从封面取色
2.1 算法思路（用什么库都行）

后端（FastAPI）可以用 Python 的 colorthief 或类似库；

前端（Next.js）也可以用 node-vibrant、color-thief 在构建或上传时处理，但推荐放到后端，避免客户端卡顿。

伪代码（后端）：

from colorthief import ColorThief

def extract_theme_from_cover(image_path: str) -> tuple[int, int, int]:
    thief = ColorThief(image_path)
    # 取主色
    r, g, b = thief.get_color(quality=5)
    h, s, l = rgb_to_hsl(r, g, b)
    h, s, l = normalize_hsl(h, s, l)
    return h, s, l

2.2 “安全色”规范化（normalize_hsl）

这里是关键一步，负责把奇怪的图片颜色拉回到“UI 友好区间”。

建议规则（你可以写进 VISUAL_RULES.yaml）：

Hue h: 0–360 原样用就行，不限制色相。

Saturation s: 限制在 40–80 之间：

< 40 → 提高到 40（避免灰死）；

> 80 → 降到 80（避免荧光色）。

Lightness l: 限制在 35–65 之间：

< 35 → 提高到 35（太暗文字看不见）；

> 65 → 降到 65（太亮没层次）。

伪代码：

def normalize_hsl(h, s, l):
    s = max(40, min(s, 80))
    l = max(35, min(l, 65))
    return h, s, l


再把它存入 DB：

theme_hex = hsl_to_hex(h, s, l)
update_library_theme(library_id, h, s, l, theme_hex, source='auto')


这样：同一张封面图 → 始终同一主题色；
替换封面图 → 只在那一刻重算一次 theme。

3. Book 封面如何“消费” LibraryTheme

Book 完全不抽色，只接收 theme：

3.1 API / DTO 设计

GET /api/bookshelves/{shelfId}/books 返回时，加上 Library Theme：

{
  "bookshelfId": "...",
  "library": {
    "id": "...",
    "theme": {
      "h": 210,
      "s": 55,
      "l": 45,
      "hex": "#345a9b"
    }
  },
  "books": [
    {
      "id": "...",
      "title": "Good",
      "stage": "Seed",
      ...
    }
  ]
}


前端渲染 BookCard 时，直接拿 library.theme 来做样式。

3.2 BookCard 样式衍生规则（例子）

假设你用 CSS 变量 + Tailwind：

// BookCard.tsx (React)
type Props = {
  title: string;
  stage: 'Seed' | 'Growing' | 'Stable' | 'Legacy';
  theme: { h: number; s: number; l: number; }; // from library
};

export function BookCard({ title, stage, theme }: Props) {
  const { h, s, l } = theme;

  // 不同部位做轻微明度偏移
  const spine = `hsl(${h}deg ${s}% ${Math.max(l - 8, 20)}%)`;
  const cover = `hsl(${h}deg ${s}% ${l}%)`;
  const shadow = `hsl(${h}deg ${s}% ${Math.max(l - 15, 10)}%)`;

  return (
    <div className="book-card" style={{ '--spine': spine, '--cover': cover, '--shadow': shadow } as React.CSSProperties}>
      {/* 封面结构... */}
    </div>
  );
}


对应的 CSS（例）：

.book-card {
  --spine: hsl(220 60% 40%);
  --cover: hsl(220 60% 48%);
  --shadow: hsl(220 60% 32%);
}

.book-card .spine {
  background: var(--spine);
}
.book-card .face {
  background: var(--cover);
}
.book-card .shadow {
  background: radial-gradient(ellipse at center, var(--shadow), transparent);
}


状态（Seed / Growing / Stable / Legacy） 建议用 小标签 / 角标的统一语义色（比如绿、蓝、紫、灰），而不是改变整本书底色，这样：

书的整体色 = LibraryTheme，保证“同一书库感”。

状态信息用小元素表达，不破坏整体色系。

4. 没封面 / 取色失败时的稳定回退

要“稳定”，就不能随机。建议：

4.1 预定义一组安全色 Palette

比如放在 VISUAL_RULES.yaml / PALETTES.yaml：

library_fallback_palette:
  - "#3B82F6"  # blue
  - "#EC4899"  # pink
  - "#10B981"  # emerald
  - "#F59E0B"  # amber
  - "#8B5CF6"  # violet
  - "#0EA5E9"  # sky
  - "#F97316"  # orange
  - "#22C55E"  # green

4.2 通过 libraryId 做 hash 选色（保证稳定）

伪代码：

import zlib

def pick_fallback_color(library_id: str) -> str:
    palette = ["#3B82F6", "#EC4899", "#10B981", "#F59E0B",
               "#8B5CF6", "#0EA5E9", "#F97316", "#22C55E"]
    h = zlib.crc32(library_id.encode("utf-8"))
    idx = h % len(palette)
    return palette[idx]


然后：

theme_hex = pick_fallback_color(library_id)
h, s, l = hex_to_hsl(theme_hex)
update_library_theme(library_id, h, s, l, theme_hex, source='fallback')


这样：

每个 Library 即使没有封面，也有一个稳定的“品牌色”；

同一个 Library 在所有环境、所有刷新下颜色都一致。

5. 结合 Wordloom 的实际好处

视觉层面

Library 封面 → Library Theme → 所有 Book 沉淀在同一色系里；

Dashboard 里看 Libraries / Bookshelves / Books，会明显看到“这个区都是某个主题色”的连续性，显得很专业。

实现复杂度可控

取色只在：

创建 Library 时（有封面）

修改封面时
跑一次即可；

Book 渲染非常轻：只是消费 theme。

未来扩展

你以后要做 Theme 页面、让用户选择“书库主题色”
→ 其实就是改 theme_* 这几列。

而所有 Book、Dashboard、统计页都自动跟着换主题，不用改别的。

6. 一段可以直接喂给 Copilot 的简要需求说明（中文+一点代码）

你可以丢给 Copilot 的版本（写进一个 Plan_XX_LibraryTheme.md）：

目标：为 libraries 增加稳定的主题色（LibraryTheme），所有 Book 封面颜色从 LibraryTheme 衍生，不再单独取色。

DB 层：

libraries 表新增字段 theme_h int, theme_s int, theme_l int, theme_hex varchar(7), theme_source varchar(20)。

取色流程：

用户上传或更新 Library 封面图时，后台用 colorthief 从图片抽取主色 r,g,b，转为 HSL。

通过函数 normalize_hsl 将 s 限制在 40–80，l 限制在 35–65。

保存到 DB：theme_h/s/l/hex，theme_source='auto'。

如果没有封面图或取色异常，则使用 pick_fallback_color(library_id) 从预定义 palette 中选一个稳定颜色，theme_source='fallback'。

前端 API：

/api/bookshelves/[id]/books 返回时，在 library 字段中附带 theme（h,s,l,hex）。

前端渲染：

BookCard 组件接收 theme，通过简单偏移 l 值生成 --spine, --cover, --shadow 三个 CSS 变量。

状态（Seed/Growing/Stable/Legacy）使用统一的小 badge 颜色，不改变大面积底色。

这样做完，你后面可以很自然地把 主题色、状态、成熟度、Chronicle 事件 这些信号都“串”在一条视觉线上：
Library 像是一个宇宙的主色，Book 就是里面的星球，各自有阶段和故事，但一眼能看出“同一星系的”。