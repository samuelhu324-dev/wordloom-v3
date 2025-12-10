先总结一下：你说的 3 点都能做到，而且对现在结构影响不大，我会按你说的顺序和比例去调整。

一、颜色来源优先级调整（封面图 → 主题色）

目标顺序：
1）优先从 Library 的“封面图”/代表书架图上提取主色；
2）提取失败或没有封面图时，退回到 library.theme_color；
3）还没有就退回到我们现有的 hash 色（保证永不空）。
实现思路（前端版本，后端可以后续固化）：
在 LibraryDetailPage 里，读取 library.coverUrl（或你实际用的字段名），渲染隐形 <img>，onLoad 时用 Canvas 或 Vibrant 算一个主色，得到 $rgb 或 $hsl。
把这个主色写入 data-lib-theme 或 React state，更新一组 CSS 变量：--lib-h --lib-s --lib-l。
如果封面图加载失败 / 超时，则用 library.theme_color 转成 HSL 写入；再不行用已有的 deterministicColor。
书架卡片继续沿用「在 Library 主色基础上做轻微偏移」的逻辑，这样不同 Library 看起来完全不一样，每个 shelf 又有一点点自己的味道。
二、Bookshelves 网格改成“一行四个 + 1:1 封面”

当前：一行三张，16:9 横图，比例偏长。
目标：
Grid：grid-template-columns: repeat(4, minmax(0, 1fr));，在窄屏上用 media query 自动退到 2 列或 1 列。
封面区域统一用 1:1：
用一个 .cover 容器设 aspect-ratio: 1 / 1;（现代浏览器都支持），内部 position: relative。
书橱 PNG 用 object-fit: contain 居中；墙体渐变占满背景。
信息区高度不用加很多，整体卡片高度也会比现在略低一点，更接近“运营卡片”而不是照片墙。
一行四个会让指标横向扫描更顺手，再配合你的紧凑视图（未来），两种视图就一宽一窄，分工也更清晰。
三、其他细节：按你现在的反馈微调

你之前提的“每个 bookshelf 底色微调 + 状态滤镜（active / slowing / stale / cold）”的方案保持不变，只是在新 1:1 封面尺寸下重新调一下渐变的范围和强度，避免颜色太顶。
Pinned：可以考虑在 1:1 封面的四角加很细的内描边或顶部一条微亮色条；Archived / 冻结继续用去饱和 + 浅雾层。
顶部 Library 看板（总数 + 健康分布 + 进度条）已经有第一版，等色系稳定后再小调字体和间距。
四、按你的要求重新梳理一个中文实施计划

我按照「后端已基本就绪，当前重点在前端视觉与交互」来排：

Library 主色管线搭好

确定 Library DTO/实体里可用的字段：封面图 URL（或代表图片）、theme_color。
在 LibraryDetailPage：
增加一个小的 hook：useLibraryThemeColor(library)：优先封面 → 主题色 → hash。
通过 Canvas/Vibrant 从封面图提取主色（只在首次/封面变更时跑一次）。
把最终 HSL 写入页面根节点的 CSS 变量。
Bookshelf 卡片改为 1:1 封面 + 四列栅格

修改 BookshelfDashboardBoard 的 grid：桌面端 repeat(4, minmax(0, 1fr))，中小屏自动缩列。
重构 BookshelfDashboardCard 的封面：
使用 aspect-ratio: 1/1 的容器，内部叠：颜色墙 + 母书橱 PNG + 状态滤镜。
hover 时做轻微 scale 和阴影加强，保留你“拉出书架”的感觉。
每个 bookshelf 的微调色和健康度视觉

基于步骤 1 的 Library HSL：
定义 per-shelf 偏移（hash(id) → hue/sat/light 微调），用 CSS 变量或 inline style 带到卡片根节点。
健康度（active/slowing/stale/cold）通过 class 控制 saturate/brightness/grayscale，不再单独硬编码颜色，这样不会偏离 Library 主色。
Pinned / Archived 再叠一层语义化的描边 / 雾层。
紧凑视图（Compact）与顶部指标完善

实现 BookshelfDashboardRow：左侧小色条 + 文本一行，把指标压缩成运营句子。
BookshelfDashboardBoard 根据 viewMode 切换卡片/行。
顶部 Library 概览增加：成熟度条（Seed/Growing/Stable/Legacy）、健康分布迷你条或小图例。
体验与性能打磨

颜色提取增加缓存，避免反复 canvas 计算（比如用 localStorage 记住 libraryId → color）。
骨架屏：Dashboard 加载时先用纯主色渐变 + skeleton，而不是白板。
移动端检查：1:1 封面 + 四列在小屏下的断点策略。