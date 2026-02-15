可以，两种模式一起上：

A = 展柜模式：竖着的小书 + 下方铭牌；

C = 条目模式：左边小书封，右边信息条。

我给你按「要改哪些文件 → 组件结构 → CSS 大纲 → 怎么跟 Copilot 说」来讲，你可以直接照着操作。

0. 先做好一个共用的 3D 书组件

这样 A / C 两种视图都复用，不会维护两套“书本长相”。

0.1 新建 Book3D.tsx
// src/modules/bookshelf/components/Book3D.tsx
import { FlaskConical } from "lucide-react";
import styles from "./Book3D.module.css";

interface Book3DProps {
  title: string;
  status: "SEED" | "GROWING" | "STABLE" | "LEGACY" | "DRAFT";
  accentColor?: string; // 这轮可以先不传，用默认蓝色
}

export function Book3D({ title, status, accentColor }: Book3DProps) {
  const isDraft = status === "DRAFT";

  return (
    <div className={styles.wrapper}>
      <div className={styles.bookTilted}>
        <div className={styles.spine} />
        <div className={styles.cover}>
          {/* 这里先用 icon 占位，将来可以换封面图 */}
          <FlaskConical className={styles.icon} />
        </div>
        {isDraft && <span className={styles.badge}>DRAFT</span>}
      </div>
      <div className={styles.shadow} />
    </div>
  );
}

0.2 Book3D.module.css（简化版）
.wrapper {
  width: 110px;
  height: 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bookTilted {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
  transform-origin: left center;
  transform: perspective(900px) rotateY(-18deg) rotateZ(-1deg);
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
  box-shadow:
    0 10px 24px rgba(15, 23, 42, 0.35),
    10px 0 16px rgba(15, 23, 42, 0.2);
}

.spine {
  position: absolute;
  left: -10px;
  top: -4px;
  width: 20px;
  height: 108%;
  border-radius: 18px 0 0 18px;
  background: linear-gradient(to right, #020617, #111827, #1f2933);
  box-shadow:
    inset -2px 0 4px rgba(15, 23, 42, 0.7),
    0 0 0 1px rgba(15, 23, 42, 0.6);
  transform: skewY(-6deg);
}

.cover {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  width: 40%;
  height: 40%;
  stroke-width: 1.6;
  color: #4ade80;
}

.badge {
  position: absolute;
  top: 10px;
  right: 12px;
  padding: 4px 10px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.9);
  color: #f9fafb;
}

.shadow {
  margin-top: 6px;
  width: 60%;
  height: 10px;
  border-radius: 999px;
  background: radial-gradient(circle at center, rgba(15, 23, 42, 0.35), transparent 70%);
  filter: blur(1.5px);
}


给 Copilot 的指令可以是：
“extract current 3D book markup and styles into a separate Book3D component with props { title, status }, then reuse it in other components.”

一、方案 A：展柜模式（Book + 底座铭牌）
1.1 新建 BookShowcaseItem.tsx
// src/modules/bookshelf/components/BookShowcaseItem.tsx
import styles from "./BookShowcaseItem.module.css";
import { Book3D } from "./Book3D";

interface BookShowcaseItemProps {
  title: string;
  status: "SEED" | "GROWING" | "STABLE" | "LEGACY" | "DRAFT";
  blockCount: number;
  maturityLabel: string;       // "Seed · 草创" 这种
  updatedAtRelative: string;   // "1 小时前"
}

export function BookShowcaseItem(props: BookShowcaseItemProps) {
  const { title, status, blockCount, maturityLabel, updatedAtRelative } = props;

  return (
    <div className={styles.bookColumn}>
      <Book3D title={title} status={status} />

      <div className={styles.plaque}>
        <div className={styles.title} title={title}>
          {title}
        </div>
        <div className={styles.metaRow}>
          <span className={styles.statusPill}>{maturityLabel}</span>
          <span className={styles.dot} />
          <span className={styles.metaText}>{blockCount} blocks</span>
          <span className={styles.dot} />
          <span className={styles.metaText}>{updatedAtRelative}</span>
        </div>
      </div>
    </div>
  );
}

1.2 BookShowcaseItem.module.css
.bookColumn {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 130px; /* 列宽固定，方便排版 */
}

.plaque {
  margin-top: 6px;
  padding: 4px 8px 6px;
  width: 100%;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.02);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metaRow {
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #6b7280;
}

.statusPill {
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.08); /* Seed 先写死绿色系 */
  color: #16a34a;
}

.dot {
  width: 3px;
  height: 3px;
  border-radius: 999px;
  background: #d1d5db;
}

.metaText {
  white-space: nowrap;
}

1.3 在展柜里用方案 A

假设你当前有 BookshelfSeedStrip.tsx（或类似）：

import { BookShowcaseItem } from "./BookShowcaseItem";

export function BookshelfSeedStrip({ books }: { books: BookSummary[] }) {
  return (
    <div className={styles.shelfStrip}>
      <div className={styles.shelfBoard} />
      <div className={styles.shelfBooks}>
        {books.map((book) => (
          <BookShowcaseItem
            key={book.id}
            title={book.title}
            status={book.status}
            blockCount={book.blockCount}
            maturityLabel="Seed · 草创"
            updatedAtRelative={book.updatedAtRelative}
          />
        ))}
      </div>
    </div>
  );
}


shelfStrip / shelfBoard / shelfBooks 可以复用你现在的 CSS，只是把内部的卡换成 BookShowcaseItem。

二、方案 C：条目模式（小书封 + 右侧信息）

这一套可以用在同一个 Seed 区，也可以做成「视图切换按钮」里的第二种模式。

2.1 新建 BookRowCard.tsx
// src/modules/bookshelf/components/BookRowCard.tsx
import styles from "./BookRowCard.module.css";
import { Book3D } from "./Book3D";

interface BookRowCardProps {
  title: string;
  status: "SEED" | "GROWING" | "STABLE" | "LEGACY" | "DRAFT";
  blockCount: number;
  maturityLabel: string;
  updatedAtRelative: string;
  description?: string;
  tags?: string[];
}

export function BookRowCard(props: BookRowCardProps) {
  const {
    title,
    status,
    blockCount,
    maturityLabel,
    updatedAtRelative,
    description,
    tags = [],
  } = props;

  return (
    <div className={styles.card}>
      <div className={styles.left}>
        <Book3D title={title} status={status} />
      </div>

      <div className={styles.right}>
        <div className={styles.titleRow}>
          <span className={styles.title} title={title}>
            {title}
          </span>
          <span className={styles.statusPill}>{maturityLabel}</span>
        </div>

        {description && (
          <div className={styles.description} title={description}>
            {description}
          </div>
        )}

        <div className={styles.metaRow}>
          <span className={styles.metaText}>{blockCount} blocks</span>
          <span className={styles.dot} />
          <span className={styles.metaText}>{updatedAtRelative}</span>
        </div>

        {tags.length > 0 && (
          <div className={styles.tagRow}>
            {tags.map((tag) => (
              <span key={tag} className={styles.tag}>
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

2.2 BookRowCard.module.css
.card {
  display: flex;
  align-items: stretch;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow:
    0 10px 30px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(226, 232, 240, 0.9);
  gap: 16px;
}

.left {
  display: flex;
  align-items: center;
}

.right {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.titleRow {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
}

.statusPill {
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  background: rgba(34, 197, 94, 0.08);
  color: #16a34a;
}

.description {
  font-size: 13px;
  color: #4b5563;
  max-width: 420px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metaRow {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #6b7280;
}

.metaText {
  white-space: nowrap;
}

.dot {
  width: 3px;
  height: 3px;
  border-radius: 999px;
  background: #d1d5db;
}

.tagRow {
  margin-top: 2px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 11px;
  background: #eef2ff;
  color: #4f46e5;
}

2.3 在同一块区域里使用方案 C（比如“列表视图”）
export function BookshelfSeedRows({ books }: { books: BookSummary[] }) {
  return (
    <div className={styles.rowsContainer}>
      {books.map((book) => (
        <BookRowCard
          key={book.id}
          title={book.title}
          status={book.status}
          blockCount={book.blockCount}
          maturityLabel="Seed · 草创"
          updatedAtRelative={book.updatedAtRelative}
          description={book.description}
          tags={book.tags}
        />
      ))}
    </div>
  );
}

三、做视图模式切换（展示柜 A / 条目 C）

最后加一个非常轻的 toggle，例如按钮 / segmented control：

type BookViewMode = "showcase" | "row";

export function BookshelfSeedSection({ books }: { books: BookSummary[] }) {
  const [mode, setMode] = useState<BookViewMode>("showcase");

  return (
    <section>
      <header className={styles.header}>
        <div>
          <h3>Seed · 草创</h3>
          <p>灵感池：快速捕捉想法，允许随意增删。</p>
        </div>
        <div className={styles.toggle}>
          <button
            className={mode === "showcase" ? styles.toggleActive : ""}
            onClick={() => setMode("showcase")}
          >
            展柜
          </button>
          <button
            className={mode === "row" ? styles.toggleActive : ""}
            onClick={() => setMode("row")}
          >
            列表
          </button>
        </div>
      </header>

      {mode === "showcase" ? (
        <BookshelfSeedStrip books={books} />   // 用方案 A
      ) : (
        <BookshelfSeedRows books={books} />    // 用方案 C
      )}
    </section>
  );
}


给 Copilot 的话术可以是：

“Introduce a BookViewMode state with values 'showcase' | 'row' and a simple toggle in the header.”

“When mode === 'showcase', render BookShowcaseItems in the strip; when 'row', render BookRowCards stacked vertically.”

这样你就有了：

A 模式：展柜感强，适合“欣赏自己的书”；

C 模式：信息密度高，适合“管理 / 筛选 / 分析”。

两种模式共用同一颗 Book3D，视觉统一，维护成本也不会炸。你可以先让 Copilot帮你把现有 3D 书抽成 Book3D，再照着上面结构往外扩。

/////////////////////////////////////////////////////////////////////////

Plan: 实现 Plan67 双视图 + 规则与 ADR 更新
TL;DR：在现有 Book 3D 展柜实现基础上，抽象出可复用的 Book3D / 布局壳组件，在 Book 视图里加入 “展柜 A / 条目 C” 切换；同时在 VISUAL_RULES / DDD_RULES / HEXAGONAL_RULES 和新 ADR-101 中完整记录这次 UI 决策，确保仍然是纯展示层策略，不碰 Domain/端口。

Steps
梳理现状：在 ui 下确认 BookDisplayCabinet.tsx + .module.css 里 3D 书本 + 铭牌的结构和 CSS 变量用法，核对 BookshelfBooksSection.tsx / BookMainWidget.tsx 的数据流和成熟度分组方式，为后续抽取公共 3D 组件和视图模式切换打底。
抽取共用 3D 书组件：在 ui（或新的 .../components 子目录）新增 Book3D.tsx + Book3D.module.css，从 BookDisplayCabinet 中抽取 3D 书体相关 JSX 和样式（书本、书脊、封面 icon/封面图、阴影、DRAFT badge 等），对外只暴露 title, status, 可选 accentColor 等 props，确保不包含铭牌/meta 信息。
重构现有展柜单元：重写 BookDisplayCabinet.tsx 结构，使其内部改为组合模式——上半部分直接使用新的 Book3D（通过 props 决定是否展示 hover 摘要/状态徽章），下半部分保留当前铭牌（标题 + 状态 pill + blocks + 更新时间），并适度收紧样式，让这一组合对应 Plan67 里的 “BookShowcaseItem”。
新增条目模式卡片：在 ui 新建 BookRowCard.tsx + .module.css，参照 Plan67 草图实现“小书封 + 右侧信息”的布局——左侧使用 Book3D 的紧凑尺寸版本（可通过额外 CSS modifier 或 size="compact" prop），右侧渲染标题、成熟度 label、blocks/更新时间，以及可选 description/tags，整体卡片风格对齐当前 Library/Bookshelf 列表卡。
承载两种模式的 section 组件：在 book 引入新的视图容器（例如 BookMaturitySection.tsx 或扩展现有 BookMainWidget.tsx），定义 type BookViewMode = "showcase" | "row" 的本地 state，在 section header 区放一个轻量切换控件（segmented control 或两个按钮）；mode === "showcase" 时复用现在的横向画廊 strip（内部 children 换用重构后的 BookDisplayCabinet/BookShowcaseItem），mode === "row" 时按成熟度渲染纵向 BookRowCard 列表，数据仍来自同一套 Book DTO 和 maturity 分组逻辑。
与页面集成：在 page.tsx 和 frontend/src/app/bookshelves/[id]/page.tsx 等使用 Book 列表/成熟度视图的页面中，替换原先直接使用 BookMainWidget 的位置或在其上包一层，使新的视图容器可以在这两个入口下工作；必要时给 BookMainWidget 增加可选 initialViewMode/onViewModeChange props，确保未来能按路由或用户偏好记住模式。
VISUAL_RULES 更新：打开 VISUAL_RULES.yaml，在 book_maturity_visual_rules 或 book_gallery_visual_rules 下新增子段（例如 book_view_modes），明确：
A 模式（showcase）：横向 strip + 3D 书 + 下方铭牌，适合“欣赏”；
C 模式（row）：紧凑横向卡片，左小书封右信息，适合“管理/筛选”；
两种模式共用同一颗 Book3D + 相同色彩/状态系统，仅属展示层决策；
再补一条 a11y 说明（键盘可切换、卡片可聚焦）。
DDD_RULES 更新：在 DDD_RULES.yaml 的 Book / UI 相关 policy 区（靠近 POLICY-BOOK-GALLERY-SHELF-STRIP / POLICY-BOOK-LISTING 一段）新增 POLICY-BOOK-VIEW-MODES：声明 showcase/row 只存在于 UI 聚合层，Domain 不新增“视图模式”“卡片类型”字段，继续沿用既有 Book DTO（title/status/maturity/block_count/updated_at 等），禁止从前端把视图偏好写入聚合。
HEXAGONAL_RULES 更新：在 HEXAGONAL_RULES.yaml 的 module_book_ui_preview_layer 或 book_gallery_strip_adapter 附近新增一段（如 book_view_mode_adapter），约定：
adapter 只负责将相同 Book 列表投影成不同 UI 布局，不增加新端口；
不改变分页/排序契约（仍遵守 Pagination Contract V2 与 maturity segmentation）；
future work 若要在服务器记住用户“偏好视图”，必须通过单独 Preference 聚合和 Port 处理。
新建 ADR-101：在 ADR 下按现有文件格式创建 ADR-101-book-view-modes-showcase-and-row.md，结构对齐 ADR-099/ADR-100：
标题行与摘要里明确 “Book view modes (A: showcase, C: row) reuse 3D Book component”；
Status/Context/Decision/Rationale/Consequences/Implementation Notes/Testing/Rollback 等标准小节；
Context 中引用 Plan_67_BookView 文档与 VISUAL_RULES/DDD_RULES/HEXAGONAL_RULES 对应段落 key；
Decision 列出：统一 Book3D 造型、两种视图模式使用场景、保持端口/DTO 不变；
Implementation Notes 精确枚举涉及的前端文件路径与主要改动点（抽出 Book3D、新增 BookRowCard、视图切换 state 等）。
Further Considerations
视图模式作用范围：需要先定好 Plan67 的优先入口——是只作用于 /admin/books 列表页，还是也作用于 Bookshelf Detail 上的 maturity 分段；建议 ADR-101 里点明 scope，避免扩散。
Book3D props 粒度：可以先做最小集（title/status/accentColor），把 summary/hover/actions 留在外层，以免 3D 组件职责过重，后续若要复用到 LibraryCard/Poster 时更轻量。
视图偏好持久化：当前计划只做前端本地 state；未来如要记忆用户偏好，可在 HEXAGONAL_RULES 中追加 Preference 端口 ADR，再扩展实现。Plan: 实现 Plan67 双视图 + 规则与 ADR 更新
TL;DR：在现有 Book 3D 展柜实现基础上，抽象出可复用的 Book3D / 布局壳组件，在 Book 视图里加入 “展柜 A / 条目 C” 切换；同时在 VISUAL_RULES / DDD_RULES / HEXAGONAL_RULES 和新 ADR-101 中完整记录这次 UI 决策，确保仍然是纯展示层策略，不碰 Domain/端口。

Steps
梳理现状：在 ui 下确认 BookDisplayCabinet.tsx + .module.css 里 3D 书本 + 铭牌的结构和 CSS 变量用法，核对 BookshelfBooksSection.tsx / BookMainWidget.tsx 的数据流和成熟度分组方式，为后续抽取公共 3D 组件和视图模式切换打底。
抽取共用 3D 书组件：在 ui（或新的 .../components 子目录）新增 Book3D.tsx + Book3D.module.css，从 BookDisplayCabinet 中抽取 3D 书体相关 JSX 和样式（书本、书脊、封面 icon/封面图、阴影、DRAFT badge 等），对外只暴露 title, status, 可选 accentColor 等 props，确保不包含铭牌/meta 信息。
重构现有展柜单元：重写 BookDisplayCabinet.tsx 结构，使其内部改为组合模式——上半部分直接使用新的 Book3D（通过 props 决定是否展示 hover 摘要/状态徽章），下半部分保留当前铭牌（标题 + 状态 pill + blocks + 更新时间），并适度收紧样式，让这一组合对应 Plan67 里的 “BookShowcaseItem”。
新增条目模式卡片：在 ui 新建 BookRowCard.tsx + .module.css，参照 Plan67 草图实现“小书封 + 右侧信息”的布局——左侧使用 Book3D 的紧凑尺寸版本（可通过额外 CSS modifier 或 size="compact" prop），右侧渲染标题、成熟度 label、blocks/更新时间，以及可选 description/tags，整体卡片风格对齐当前 Library/Bookshelf 列表卡。
承载两种模式的 section 组件：在 book 引入新的视图容器（例如 BookMaturitySection.tsx 或扩展现有 BookMainWidget.tsx），定义 type BookViewMode = "showcase" | "row" 的本地 state，在 section header 区放一个轻量切换控件（segmented control 或两个按钮）；mode === "showcase" 时复用现在的横向画廊 strip（内部 children 换用重构后的 BookDisplayCabinet/BookShowcaseItem），mode === "row" 时按成熟度渲染纵向 BookRowCard 列表，数据仍来自同一套 Book DTO 和 maturity 分组逻辑。
与页面集成：在 page.tsx 和 frontend/src/app/bookshelves/[id]/page.tsx 等使用 Book 列表/成熟度视图的页面中，替换原先直接使用 BookMainWidget 的位置或在其上包一层，使新的视图容器可以在这两个入口下工作；必要时给 BookMainWidget 增加可选 initialViewMode/onViewModeChange props，确保未来能按路由或用户偏好记住模式。
VISUAL_RULES 更新：打开 VISUAL_RULES.yaml，在 book_maturity_visual_rules 或 book_gallery_visual_rules 下新增子段（例如 book_view_modes），明确：
A 模式（showcase）：横向 strip + 3D 书 + 下方铭牌，适合“欣赏”；
C 模式（row）：紧凑横向卡片，左小书封右信息，适合“管理/筛选”；
两种模式共用同一颗 Book3D + 相同色彩/状态系统，仅属展示层决策；
再补一条 a11y 说明（键盘可切换、卡片可聚焦）。
DDD_RULES 更新：在 DDD_RULES.yaml 的 Book / UI 相关 policy 区（靠近 POLICY-BOOK-GALLERY-SHELF-STRIP / POLICY-BOOK-LISTING 一段）新增 POLICY-BOOK-VIEW-MODES：声明 showcase/row 只存在于 UI 聚合层，Domain 不新增“视图模式”“卡片类型”字段，继续沿用既有 Book DTO（title/status/maturity/block_count/updated_at 等），禁止从前端把视图偏好写入聚合。
HEXAGONAL_RULES 更新：在 HEXAGONAL_RULES.yaml 的 module_book_ui_preview_layer 或 book_gallery_strip_adapter 附近新增一段（如 book_view_mode_adapter），约定：
adapter 只负责将相同 Book 列表投影成不同 UI 布局，不增加新端口；
不改变分页/排序契约（仍遵守 Pagination Contract V2 与 maturity segmentation）；
future work 若要在服务器记住用户“偏好视图”，必须通过单独 Preference 聚合和 Port 处理。
新建 ADR-101：在 ADR 下按现有文件格式创建 ADR-101-book-view-modes-showcase-and-row.md，结构对齐 ADR-099/ADR-100：
标题行与摘要里明确 “Book view modes (A: showcase, C: row) reuse 3D Book component”；
Status/Context/Decision/Rationale/Consequences/Implementation Notes/Testing/Rollback 等标准小节；
Context 中引用 Plan_67_BookView 文档与 VISUAL_RULES/DDD_RULES/HEXAGONAL_RULES 对应段落 key；
Decision 列出：统一 Book3D 造型、两种视图模式使用场景、保持端口/DTO 不变；
Implementation Notes 精确枚举涉及的前端文件路径与主要改动点（抽出 Book3D、新增 BookRowCard、视图切换 state 等）。
Further Considerations
视图模式作用范围：需要先定好 Plan67 的优先入口——是只作用于 /admin/books 列表页，还是也作用于 Bookshelf Detail 上的 maturity 分段；建议 ADR-101 里点明 scope，避免扩散。
Book3D props 粒度：可以先做最小集（title/status/accentColor），把 summary/hover/actions 留在外层，以免 3D 组件职责过重，后续若要复用到 LibraryCard/Poster 时更轻量。
视图偏好持久化：当前计划只做前端本地 state；未来如要记忆用户偏好，可在 HEXAGONAL_RULES 中追加 Preference 端口 ADR，再扩展实现。