实施总计划（Plan44 书架页改造）

总体目标：把当前“封面墙”升级为“运营看板”：展示书架结构指标 + Chronicle 活跃度 + 健康度，并支持舒适/紧凑两种视图与排序筛选。

阶段划分：

数据侧准备
后端 API & DTO
前端组件与布局重构
颜色与封面墙实现
指标计算（Chronicle 聚合）
紧凑视图与交互补完
测试与性能微调
文档与 RULES/ADR 补充
1. 数据侧准备
指标需求：

bookCounts: total / seed / growing / stable / legacy
editsLast7d / viewsLast7d
lastActivityAt
health (active | slowing | stale | cold)
数据来源：

bookCounts: 直接按 bookshelf_id group + status 聚合
editsLast7d: Chronicle event_name in (BOOK_EDITED, BLOCK_UPDATED...) 近 7 天 count
viewsLast7d: event_name = BOOK_OPENED 近 7 天 count
lastActivityAt: 最近一条该书架下任一 Book 的 Chronicle 事件 occurred_at
health 规则（初版可硬编码）：
active: lastActivityAt ≤ 2d
slowing: 2d < lastActivityAt ≤ 7d
stale: 7d < lastActivityAt ≤ 21d
cold: > 21d 或无事件
2. 后端 API & DTO
新增 DTO: BookshelfSummary
新增接口: GET /api/v1/libraries/{library_id}/bookshelves?sort=...&filter=...&view=...

排序选项：

recent_activity (lastActivityAt DESC)
most_books (bookCounts.total DESC)
most_stable (bookCounts.stable DESC)
most_active (editsLast7d + viewsLast7d DESC)
longest_idle (lastActivityAt ASC NULLS LAST)
筛选：

statusFilter: all | active | stale | archived | pinned
view: comfortable | compact
输出：{ items: BookshelfSummary[], totalCount: number }

3. 前端组件结构

// 入口页面（重构现有页）
<BookshelvesDashboard libraryId={...} />

// 头部区
<BookshelfHeader
  library={librarySummary}
  filters={filters}
  onFiltersChange={setFilters}
/>

// Pinned 区
<PinnedShelves shelves={pinned} viewMode={viewMode} />

// 普通列表区
<BookshelfList shelves={others} viewMode={viewMode} total={totalCount} />

// 单卡（舒适）
<BookshelfCard shelf={shelf} />

// 紧凑行
<BookshelfRow shelf={shelf} />

// 封面
<ShelfCover themeColor={shelf.themeColor ?? library.themeColor} />

4. 颜色与封面墙实现
主色提取策略：

优先 bookshelf.themeColor
否则 library.themeColor
否则用封面图（或默认图）运行主色提取（ColorThief / Vibrant）
得到 hex 后应用 CSS 变量 --wall-color
轻微调色：HSL 提升亮度 +5%，降低饱和度 -8% 作为背景墙；原 PNG 不变
颜色提取（懒加载）：

封面进入视口（IntersectionObserver）时才提取颜色并 setState
5. Chronicle 聚合逻辑
后端新增查询函数：

bookshelf_activity_stats(library_id, bookshelf_ids[], since_days=7)
实现方式：

先查出该 bookshelf 的所有 book_id
events where book_id in (...) and occurred_at >= now() - interval '7 days'
分 event_name 分类计数
lastActivityAt = max(occurred_at)
health 根据规则映射
6. 紧凑视图
行内布局字段顺序：
Icon | Name | Books total | Seed/Grow/Stable/Legacy | Edits7d | Views7d | Health | LastActivity (相对时间)

视觉：

行高 ~48px
字号减小
zebra 背景：偶数行 var(--row-alt-bg)
悬停高亮背景轻微提升亮度
7. 测试与性能
后端：

聚合函数返回完整指标
排序正确性（各排序模式下第一条断言）
健康度边界测试（刚好 2d / 7d / 21d）
前端：

hook: useBookshelvesDashboard 测试分页 + 排序参数拼接
颜色提取：mock 图像数据 URL，验证延迟设置 --wall-color
组件截图测试（紧凑 vs 舒适）
性能：

大量书架时将 Chronicle 统计并行批量查询一次，避免 N+1
可选缓存：Redis key bookshelf_stats:{id} TTL 5m
8. 文档同步
更新 VISUAL_RULES 增加 bookshelf_dashboard_visual_rules
DDD_RULES 增加 BookshelfSummaryPolicy（禁止在 Bookshelf 表写编辑/浏览计数）
HEXAGONAL_RULES 增加 bookshelves_dashboard_read_model 段落
若需要新增 ADR（可选）：ADR-094-bookshelf-dashboard

样板图（ASCII Wireframe）
舒适模式卡片（16:9 封面 + 指标串）：

+-------------------------------------------------------------+
| +-------------------+  | AAA 学习  PINNED        ⋯ |        |
| |     Shelf PNG     |  | Books 12 · Seed 3 · Grow 5 ·        |
| |   (wall-color)    |  | Stable 3 · Legacy 1                 |
| |                   |  | ✏ 9/7d · 👁 21/7d · 🕒 Active       |
| +-------------------+  | [查看书籍] [+ 新书]                 |
+-------------------------------------------------------------+
(hover: PNG scale 1.03, shadow deepen, wall-color lighten)

紧凑模式行：

┌─────────────────────────────────────────────────────────────┐
| ○  AAA  Books 12  S/G/St/L: 3/5/3/1  ✏9  👁21  🕒 Active  2d |
└─────────────────────────────────────────────────────────────┘
(○ = 小圆图标或颜色条; zebra stripe every other row)

页面整体布局：

[ 返回 ] Library 名称      Seed | Growing | Stable | Legacy  进度条
排序: ▾ 最近更新  筛选: ▾ 全部状态  视图: 舒适/紧凑  [新建书架]

Pinned Shelves
[卡片][卡片][卡片][卡片]

其他书架 (总数 42)
[卡片][卡片][卡片]
[分页 / 加载更多]

颜色层示意：

<div class="shelf-cover" style="--wall-color:#d9c7b2">
  <div class="wall"></div>
  <img src="/img/shelf.png" class="shelf-png" />
</div>

.wall: background: linear-gradient(
  135deg,
  hsl(var(--wall-h), var(--wall-s), calc(var(--wall-l) + 5%)),
  hsl(var(--wall-h), var(--wall-s), calc(var(--wall-l) - 3%))
);

样板代码片段
BookshelfSummary（TS）：
export type BookStatus = 'seed' | 'growing' | 'stable' | 'legacy';

export interface BookshelfSummary {
  id: string;
  name: string;
  description: string | null;
  kind: 'study' | 'translation' | 'archive' | 'misc';
  isPinned: boolean;
  isArchived: boolean;
  coverUrl: string | null;
  themeColor: string | null;
  bookCounts: {
    total: number;
    seed: number;
    growing: number;
    stable: number;
    legacy: number;
  };
  editsLast7d: number;
  viewsLast7d: number;
  lastActivityAt: string | null;
  health: 'active' | 'slowing' | 'stale' | 'cold';
}

颜色提取（前端示例）：
import Vibrant from 'node-vibrant';

export async function extractMainColor(url: string): Promise<string | null> {
  try {
    const palette = await Vibrant.from(url).getPalette();
    const swatch = palette?.Vibrant || palette?.Muted;
    return swatch ? swatch.getHex() : null;
  } catch {
    return null;
  }
}

健康度计算（后端伪代码）：
def compute_health(last_activity_at: datetime | None, now: datetime) -> str:
    if last_activity_at is None:
        return 'cold'
    delta = now - last_activity_at
    days = delta.days + delta.seconds / 86400
    if days <= 2: return 'active'
    if days <= 7: return 'slowing'
    if days <= 21: return 'stale'
    return 'cold'


舒适卡片结构（React）：
export function BookshelfCard({ shelf }: { shelf: BookshelfSummary }) {
  return (
    <div className="shelfCard">
      <ShelfCover themeColor={shelf.themeColor} />
      <div className="info">
        <div className="titleRow">
          <h3>{shelf.name}</h3>
          <div className="tags">
            <span className="kind">{shelf.kind}</span>
            {shelf.isPinned && <span className="badge pinned">PINNED</span>}
            {shelf.isArchived && <span className="badge archived">ARCHIVED</span>}
          </div>
          <button className="menuBtn">⋯</button>
        </div>
        <div className="metrics">
          <span>Books {shelf.bookCounts.total}</span>
          <span>Seed {shelf.bookCounts.seed}</span>
          <span>Growing {shelf.bookCounts.growing}</span>
          <span>Stable {shelf.bookCounts.stable}</span>
          <span>Legacy {shelf.bookCounts.legacy}</span>
          <span>✏ {shelf.editsLast7d}/7d</span>
          <span>👁 {shelf.viewsLast7d}/7d</span>
          <span>🕒 {shelf.health}</span>
        </div>
        <div className="actions">
          <button>查看书籍</button>
          <button className="secondary">+ 新书</button>
        </div>
      </div>
    </div>
  );
}

CSS 片段：
.shelfCard {
  display: flex;
  gap: 1.2rem;
  background: var(--card-bg);
  border-radius: 12px;
  padding: 1.2rem;
  box-shadow: var(--shadow-sm);
  transition: box-shadow .2s, transform .2s;
}
.shelfCard:hover {
  box-shadow: var(--shadow-md);
}
.shelfCard .info { flex: 1; display: flex; flex-direction: column; }
.titleRow { display: flex; align-items: center; gap: .6rem; }
.metrics { display: flex; flex-wrap: wrap; gap: .8rem; font-size: .85rem; color: var(--text-dim); }
.badge.pinned { background: var(--accent-muted); }
.badge.archived { background: var(--warning-muted); }
.shelfCover { width: 180px; aspect-ratio: 16/9; position: relative; overflow: hidden; border-radius: 8px; }
.shelfCover .wall { position:absolute; inset:0; background: var(--wall-gradient); }
.shelfCover img { position:absolute; inset:0; width:100%; height:100%; object-fit: contain; }

下一步执行顺序建议（可直接开始）
后端：实现聚合查询与 BookshelfSummary DTO + 新接口。
前端：搭建 hooks（useBookshelvesDashboard）+ 组件骨架 + 舒适模式页面。
颜色：接入 Vibrant 提取逻辑 + IntersectionObserver。
Chronicle 聚合字段真实接线（临时假数据可先占位）。
紧凑模式行实现 + 视图切换。
排序/筛选交互 + 健康度显示。
测试与文档更新（RULES & 可选 ADR-094）。
需要我直接进入第 1 步编码时告诉我。

