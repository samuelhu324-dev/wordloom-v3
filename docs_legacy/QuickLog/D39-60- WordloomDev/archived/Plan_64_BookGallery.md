要做出**“陈列很多书”的画面感**，可以按“三层结构”来改：

页面 → 一个“陈列区模块”

陈列区 → 一条“书架条 / 展品台”

书架条上 → 多本斜着的小书（你现在的 BookCard 升级版）

下面我给你一套可以直接抄的结构 + 样式思路，你可以按你的文件名改。

1. 结构：先做一条“书架条”

在 bookshelf 详情页，把书的区域改成类似这样（伪代码 TypeScript / JSX）：

// BookshelfBooksSection.tsx

interface BookshelfBooksSectionProps {
  books: Book[]; // 你原来用什么类型照用
}

export function BookshelfBooksSection({ books }: BookshelfBooksSectionProps) {
  return (
    <section className={styles.bookshelfSection}>
      <header className={styles.bookshelfHeader}>
        {/* 左侧图标 + 标题 + 描述，沿用你现在的结构 */}
      </header>

      <div className={styles.shelfStrip}>
        <div className={styles.shelfBoard} />

        <div className={styles.shelfBooks}>
          {books.map((book, index) => (
            <BookDisplayCabinet
              key={book.id}
              book={book}
              className={styles.bookSlot}
              data-index={index}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

2. 书架底座 + 背景：让书“站”在东西上
/* BookshelfBooksSection.module.css */

.bookshelfSection {
  margin-top: 24px;
}

.shelfStrip {
  position: relative;
  padding: 32px 40px 56px;
  border-radius: 24px;
  background: radial-gradient(circle at top, #ffffff 0, #f3f4f6 40%, #e5e7eb 100%);
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(148, 163, 184, 0.15);
  overflow-x: auto;
}

/* 书架木板 / 展台 */
.shelfBoard {
  position: absolute;
  left: 32px;
  right: 32px;
  bottom: 18px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(to bottom, #cbd5e1, #94a3b8);
  box-shadow:
    0 8px 18px rgba(15, 23, 42, 0.25),
    inset 0 2px 0 rgba(255, 255, 255, 0.6);
  z-index: 0;
}

/* 书阵列 */
.shelfBooks {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-end;
  gap: 32px;
  min-height: 220px; /* 和书高度差不多 */
  padding-bottom: 10px;
}

/* 单本书的插槽，让它靠着书架站着 */
.bookSlot {
  flex: 0 0 auto;
}


这样一来：

整块白卡变成“陈列区”；

底部有一条略深的“木板”/“金属台”；

书是站在木板上，而不是飘在白底上。

3. 让书“更像一本本站着的书”而不是按钮

你已经有第一版斜书了，在这个基础上改一下：

// BookDisplayCabinet.tsx
import styles from "./BookDisplayCabinet.module.css";

interface Props {
  book: Book;
  className?: string;
}

export function BookDisplayCabinet({ book, className }: Props) {
  return (
    <div className={`${styles.wrapper} ${className ?? ""}`}>
      <div className={styles.bookTilted}>
        <div className={styles.spine} />
        <img
          src={book.coverUrl ?? "/images/default-cover.png"}
          alt={book.title}
          className={styles.cover}
        />

        {book.status === "DRAFT" && (
          <span className={styles.badge}>DRAFT</span>
        )}
      </div>
      <div className={styles.shadow} />
    </div>
  );
}

/* BookDisplayCabinet.module.css */

.wrapper {
  position: relative;
  width: 140px;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 书本本体 */
.bookTilted {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
  transform-origin: left center;
  transform: perspective(900px) rotateY(-18deg) rotateZ(-1deg);
  box-shadow:
    0 10px 24px rgba(15, 23, 42, 0.35),
    10px 0 16px rgba(15, 23, 42, 0.2);
  background: #1d4ed8;
}

/* 书脊 */
.spine {
  position: absolute;
  left: -12px;
  top: -4px;
  width: 22px;
  height: 108%;
  border-radius: 18px 0 0 18px;
  background: linear-gradient(to right, #020617, #111827, #1e293b);
  box-shadow:
    inset -2px 0 4px rgba(15, 23, 42, 0.75),
    0 0 0 1px rgba(15, 23, 42, 0.6);
  transform: skewY(-8deg);
}

/* 封面图 */
.cover {
  position: relative;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* DRAFT 小徽章 */
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

/* 地面投影，让书挨着“木板”站着而不是悬空 */
.shadow {
  margin-top: 6px;
  width: 60%;
  height: 10px;
  border-radius: 999px;
  background: radial-gradient(circle at center, rgba(15, 23, 42, 0.3), transparent 70%);
  filter: blur(2px);
}

4. 把“单张大卡片”改成“多本书陈列”的感觉

即使现在只有 1 本书，布局也先按“一排多本”的方式来设计：

shelfBooks 使用 display: flex; gap: 32px;，预留出摆很多本的空间；

未来有多本时，可以用 :nth-child() 给一点微妙的角度变化，比如：

.shelfBooks > :nth-child(2n) .bookTilted {
  transform: perspective(900px) rotateY(-16deg) rotateZ(0deg);
}

.shelfBooks > :nth-child(3n) .bookTilted {
  transform: perspective(900px) rotateY(-20deg) rotateZ(1deg);
}


肉眼效果会像是一排手动摆过位置的书，稍微乱一点，反而更有“真实陈列”的感觉。

5. 页面背景层次的小建议

你这页整体是大白底 + 顶部统计条，其实只要很轻的两笔就能让“书架”更有存在感：

给整个 bookshelf 内容区加一个淡淡的纵向渐变：
background: linear-gradient(to bottom, #f9fafb, #eef2ff);

或者只对“该书架的书籍”这块外层容器做渐变 + 轻阴影，让人一眼看出：
“上面是文本信息，下半块是实体书陈列”。

总结一下关键点：

给书一个“物理环境”：有书架板、有投影、有陈列区背景；

布局从“一个大卡片”变成“一排多本书的 strip”；

书本身稍微 3D + 有书脊 + 小徽章，但不要占满全屏；

即使现在只有一册，也先按“可以摆很多本”的样子来搭架子，以后自然会渐渐被填满。

这样迭几轮，你这个页面就会从“列表卡片”升级成“Seed 作品展台”，气质会完全不一样。

//////////////////////////////////////////////////////////////////////////

Plan: Book Gallery Strip Refactor（Bookshelf 详情页）
将当前“成熟度分区 + 卡片列表”升级为“陈列区 + 书架条 + 斜着的小书”，并在三套 RULES + ADR 中留档。

Steps
梳理现状与目标映射

组件入口：确认 bookshelf 详情页仍通过 page.tsx 渲染 BookMainWidget；记录其目前职责：成熟度统计条 + Seed/Growing/Stable/Legacy 四段 + 水平 BookPreviewList。
现有 3D 卡片：定位已存在的“斜书”实现（当前 Book Preview UI 层里已经有 Phase 2 的 3D/水平滚动实现，参考 VISUAL_RULES module_book_ui_preview_layer），标记可复用的 props（封面、标题、状态、点击行为）。
目标结构：用 Plan_64 的“三层结构”统一命名：
页面层：Bookshelf 详情页中的“书籍陈列区模块”；
模块层：单个 BookshelfBooksSection（包括 Header + 陈列 strip）；
strip 层：shelfStrip + shelfBoard + shelfBooks + 多个 BookDisplayCabinet。
设计组件拆分与文件落点（遵守 FSD）

BookDisplayCabinet（单本斜书展示组件）
建议放在：BookDisplayCabinet.tsx + BookDisplayCabinet.module.css。
职责：
接收 book: BookDto（或已有 BookPreviewCardProps 等类型），可选 className。
只管视觉：倾斜变换、书脊、封面图（复用 /public/images/default-cover.png 或现有默认封面）、DRAFT 徽章、阴影。
点击行为全部通过上层传入（如 onSelectBook），自身保持“纯展示 + 可选 wrapper onClick”。
Props 草案：
book: BookDto（至少包含 id, title, cover_url/coverUrl, status）；
className?: string;
onClick?: (bookId: string) => void.
BookshelfBooksSection（陈列区 + 一条书架条）
建议放在：frontend/src/widgets/book/BookshelfBooksSection.tsx + BookshelfBooksSection.module.css。
职责：
仅负责“该书架的书籍”的一块视觉陈列区：上方保留/复用现有标题与说明（可沿用 Seed · 草创 等文案），下方是一条 shelfStrip。
接收 books（按成熟度过滤后的一部分，或直接所有 active 书），决定如何排序/分组到 strip；
内部结构参考 Plan_64：
<section className={styles.bookshelfSection}> 外层；
<header className={styles.bookshelfHeader}>：左侧图标+标题+描述，沿用目前 BookMaturityView 里的 Seed section 头部样式，或轻量简化版；
<div className={styles.shelfStrip}>：渐变背景 + 圆角 + 阴影；
<div className={styles.shelfBoard} />：底部木板/展台；
<div className={styles.shelfBooks}>：display:flex; align-items:flex-end; gap:32px; overflow-x 支持一排多本；
BookDisplayCabinet 通过 className={styles.bookSlot} 挂载在 strip 上。
Props 草案：
books: BookDto[];
onSelectBook?: (id: string) => void;
可选 title/description/icon 若未来支持多段陈列区。
与 BookMainWidget 和成熟度视图的集成方式

入口组件：继续使用 BookMainWidget.tsx 作为 bookshelf 详情“书籍区”总控。
数据层保持不变：
仍通过 useBooks(bookshelfId) 拉书；
仍使用 buildBookMaturitySnapshot 计算 snapshot，供顶部“完成度”统计条使用（progress + Seed/Growing/Stable/Legacy 计数）。
布局层改造：
顶部：保留当前 summaryBar（完成度 + counters）；
其下：把“该书架的书籍 + +NEW BOOK + 新建表单”作为陈列区的 Header（已完成初步移动到 summaryBar 下，可以继续细化）；
再往下：
Option A（推荐，简单接 Plan_64）
选取某个成熟度（例如 seed + growing 或所有 active）合并为一组 stripBooks；
使用 BookshelfBooksSection 渲染 strip；
保留原来的四段 MATURITY_SECTIONS 作为“详情区”，放在 strip 之后（或折叠成 tabs）。
Option B（更大胆）
将四个成熟度区简化为统计文字 + 链接，主要视觉集中在单条 strip 上；
适合 bookshelf 页面定位为“陈列展台”，而不是“成熟度工作台”。
行为保持现有：
点击 strip 中任一本书，复用当前 onSelectBook 行为；
+NEW BOOK 仍使用现在的 create flow（Title + Summary 表单 + mutation），创建后：
strip 自动出现新书（React Query 刷新）；
保证默认成熟度（seed）下新书立即在 strip 中排第一或最后一位（由业务决定）。
CSS 与视觉规则细化（对应 Plan_64）

BookshelfBooksSection.module.css 关键类：
.bookshelfSection: 与当前卡片间距对齐（上下 margin-top: 24px，宽度跟随 container）；
.shelfStrip:
渐变背景 radial-gradient(circle at top, #ffffff 0, #f3f4f6 40%, #e5e7eb 100%)；
border-radius: 24px;，box-shadow 参考 Plan_64；
overflow-x: auto; padding: 32px 40px 56px;;
.shelfBoard:
绝对定位在底部，椭圆形木板；
线性渐变+内外阴影，营造立体感；
.shelfBooks:
display:flex; align-items:flex-end; gap:32px; min-height:220px; padding-bottom:10px;；
加 scroll-snap-type:x mandatory 可选增强滚动体验；
.bookSlot: flex:0 0 auto;，可预留 data-index 做 nth-child 微调角度。
BookDisplayCabinet.module.css 关键类：
.wrapper: 固定宽高（例如 140×200）+ 水平居中；
.bookTilted:
transform-origin:left center; transform:perspective(900px) rotateY(-18deg) rotateZ(-1deg);；
圆角 + 强阴影；
.spine: 左侧书脊，略微 skewY(-8deg)；
.cover: object-fit:cover;；
.badge: 右上角 DRAFT 徽章；
.shadow: 下方 radial-gradient 阴影，与 shelfBoard 产生“贴着木板”的错觉；
可通过 .shelfBooks > :nth-child(2n/3n) .bookTilted 做轻微角度扰动，模拟“手动摆过”的真实感。
主题对齐：
颜色优先用现有 tokens.css 中的中性色变量（如 --color-bg-secondary, --color-border-soft, --color-shadow-lg），只在必要时硬编码少量渐变；
阴影深度参照 VISUAL_RULES 中卡片阴影等级，避免单独新体系。
RULES 三文件的更新要点（只改文档，不碰后端契约）

DDD_RULES.yaml
在 Book Domain 或 UI-FLOW/visual policy 附近新增一条策略，例如：
POLICY-BOOK-GALLERY-SHELF-STRIP:
说明 Book Gallery 仅属于 UI 聚合层；
声明：
Book/Bookshelf 聚合不因“陈列区视觉”新增字段（例如位置、角度、木板颜色）；
陈列顺序仍由 UI/Query 层基于已有字段（created_at / last_activity / maturity）组合；
若未来需要“展位顺序”，必须新增专用枚举/字段并通过 ADR 评审。
HEXAGONAL_RULES.yaml
在 module_book_ui_preview_layer 或 book_maturity_segmentation_strategy 下追加：
描述 Book Gallery strip 是“Application/UI Adapter”对 Book 列表的一个视图，不引入新端口；
明确：
复用现有 /api/v1/books?bookshelf_id=... 与 maturity segmentation；
Gallery 只在前端分组/过滤，不增加新的 UseCase；
若未来需要“展台配置”（例如只展示 Stable 书），将通过 Query 参数或新 UseCase 暴露，禁止前端自行筛选出与后端契约矛盾的视图。
VISUAL_RULES.yaml
在 module_book_ui_preview_layer 或新增 book_gallery_visual_rules 区块：
记录：
三层结构（页面 / 陈列区模块 / 书架条）；
“木板 + 投影 + 渐变背景”的存在目的：强调“实体书陈列”而非列表；
交互规则：
Gallery strip 为只读导航视图，点击进入 Book 工作区 /admin/books/{bookId}；
保持与成熟度统计条配色协调，不喧宾夺主；
响应式约束：
小屏时 strip 可横向滚动，但保留同一视觉等级；
多本书时最多显示 3–4 本在首屏，其余通过滚动进入视野。
ADR-100：Book Gallery 决策文档模板

文件名与路径：

assets/docs/ADR/ADR-100-book-gallery-bookshelf-strip.md。
结构（模仿 091–099）：

标题区
# ADR-100: Bookshelf Book Gallery Strip (Plan64)
元信息表格：
Status: Accepted / Proposed（根据你当前阶段选择）
Date: 2025-11-27 (或实际日期)
Deciders: （列出主要决策人/你自己）
Related docs:
Plan_64_BookGallery.md
VISUAL_RULES.yaml#book_gallery_visual_rules
DDD_RULES.yaml#POLICY-BOOK-GALLERY-SHELF-STRIP
HEXAGONAL_RULES.yaml#module_book_ui_preview_layer
Context
说明：
现状：Bookshelf 详情页书籍区域以成熟度分区 + 列表卡片为主，视觉更像数据表；
目标：为 Seed–阶段作品提供更“作品展台 / 书架条”感觉，提高一眼感知的“有很多书被陈列”的氛围；
已有：Book Preview Phase 2 已交付水平滚动/3D 卡片；
范围：仅影响前端 UI 聚合层，不改后端端点。
Decision
采用 Plan_64 的三层结构：
页面内增加 BookshelfBooksSection 模块；
模块内有 shelfStrip + shelfBoard + shelfBooks；
使用 BookDisplayCabinet 渲染斜书；
顶部成熟度 summaryBar 保留，用于状态反馈；
Gallery strip 默认展示当前 Bookshelf 下的 active 书（可选 Seed/Growing/Stable 组合策略）；
不在 Domain 中存储陈列顺序或角度。
Consequences
Positive：
视觉上更符合“书架/作品展”的心智；
便于后续扩展多本书的轻微角度变化；
保持与 Book Workspace tabs 设计一致（点击即进入 /admin/books/{bookId}）；
Negative / Trade-offs：
实现复杂度略高：需要新增 2 个 UI 组件和一套 CSS；
在低性能设备上可能有些 3D/阴影成本，需要按 VISUAL_RULES 控制动画简化。
Implementation Notes
指定最终组件路径、命名和与 BookMainWidget 的关系；
说明不会新增 API，仅消费现有 useBooks hook；
标记要同步更新 DDD/HEXAGONAL/VISUAL 三份 RULES。
Rollout & Follow-up
阶段性上线策略（如先只对 Seed bookshelf 启用再推广）；
兼容方案：保留原列表视图代码一段时间以便回滚；
未来扩展：支持多条 strip（按成熟度/标签拆分陈列区）。
Further Considerations
选型问题：Strip 中默认展示哪些成熟度（仅 Seed / Active 全部 / 可配置）你希望我先按哪一种写进 ADR-100 说明？
是否要在 Book Workspace /admin/books/{bookId} 中同步使用 BookDisplayCabinet 作为侧边小预览，以保持视觉一脉相承？

////////////////////////////////////////////////////////////////////////

Book Gallery 改造计划

梳理现状与数据流
page.tsx 继续作为入口，确认仅渲染 BookMainWidget 与 breadcrumb，不动数据契约。
BookMainWidget 保留 useBooks、buildBookMaturitySnapshot、summaryBar 进度条逻辑，为新增 strip 提供书本数组与成熟度统计。
拆分新组件
frontend/src/features/book/ui/BookDisplayCabinet.tsx(.module.css)：只负责单本斜书外观，props 含 book: BookDto、className?、onClick?。CSS 落地书脊、倾斜、徽章、阴影，并预留 data-index 做 nth-child 角度扰动。
frontend/src/widgets/book/BookshelfBooksSection.tsx(.module.css)：包装 header + strip。header 复用现有 Seed 文案/图标结构，strip 内含 .shelfStrip 渐变背景、.shelfBoard 木板、.shelfBooks flex 容器以及 .bookSlot。
整合 strip 与成熟度视图
在 BookMainWidget 中：
summaryBar 下加入 BookshelfBooksSection，传入 snapshot.groupedBooks 合并后的 active 书（Seed/Growing/Stable）；
strip 点击回调复用原 onSelectBook。
原 BookMaturityView 保留但下移，成为 strip 之后的“深入信息区”；若后续要切换到多条 strip，可复用 BookshelfBooksSection。
交互与状态
+NEW BOOK 与创建表单保持当前实现；创建成功后 BookshelfBooksSection 自动看到新书（TanStack Query 失效/刷新）。
空数据时 strip 显示灰色提示（“尚无书籍，请先创建”），并隐藏木板阴影避免空白。
响应式：≤768px 时 strip 允许横向滚动并维持 32px 间距；阴影/变换降低强度以减轻性能压力。
视觉细节
.shelfStrip 使用 radial-gradient(circle at top, #fff 0, #f3f4f6 40%, #e5e7eb 100%)、border-radius:24px、双层阴影（外投影 + 1px outline）。
.shelfBoard L/R:32px、height:14px、linear-gradient + inset highlight，z-index 0。
.shelfBooks align-items:flex-end; gap:32px; min-height:220px; padding-bottom:10px; overflow-x:auto; scroll-snap-type:x mandatory（可选）。
BookDisplayCabinet 的 .bookTilted transform:perspective(900px) rotateY(-18deg) rotateZ(-1deg)；.shadow 用 radial-gradient 表现贴合木板。
回滚与验证
保留旧 BookPreviewList 代码路径，feature flag（或临时开关）允许快速回退。
手动验证：Seed 只有一本时 strip 仍有展台感；多本时 nth-child 角度扰动形成“人工摆放”效果。
RULES 同步要点

DDD_RULES.yaml 新增 POLICY-BOOK-GALLERY-SHELF-STRIP：
Book/Bookshelf 聚合不保存陈列顺序、角度等纯视觉信息；
Gallery 依据现有 maturity/created_at 排序，由 UI 负责；
若未来需要展位配置，需先扩展 UseCase + DTO 并走 ADR。
HEXAGONAL_RULES.yaml 在 module_book_ui_preview_layer 下补充：
Book Gallery strip 属于 UI Adapter，对 /api/v1/books?bookshelf_id= 的现有输出做视觉组合；
不新增端口/用例；
明确 Query 过滤（active/seed/stable）必须与后端契约一致，禁止前端伪造。
VISUAL_RULES.yaml 新增 book_gallery_visual_rules：
描述三层结构（页面 → 陈列区 → 书架条）；
记录渐变背景、木板、投影、3D 书脊等视觉元素与响应式要求；
交互规范：点击书进入 /admin/books/{bookId}；strip 仅展示用途，成熟度详情仍在下方区块；
性能守则：移动端减低阴影、保持 60fps。
ADR-100 结构草案 (assets/docs/ADR/ADR-100-book-gallery-bookshelf-strip.md)

标题/元信息
# ADR-100: Bookshelf Book Gallery Strip (Plan64)
表格：Status=Accepted、Date=2025‑11‑27、Deciders=…、Related Docs=Plan_64、三份 RULES。
Context
现有 bookshelf 详情只呈现成熟度卡片，缺乏“陈列很多书”氛围；Book Preview Phase 2 已有水平滚动/3D 能力；Plan_64 目标是营造展台。
Decision
采纳三层结构 + BookshelfBooksSection + BookDisplayCabinet；
Gallery strip 默认展示 active 书并配合 summaryBar；
Domain 不新增字段，仅前端视觉实现。
Consequences
Pros：展现力提升、内聚 Book 工作区导航；
Cons：前端复杂度、性能风险；需维护旧视图回退。
Implementation Notes
列出组件/文件路径、复用 useBooks、strip 布局细节、回滚策略。
Rollout & Follow-up
上线节奏（例如先在 Seed-heavy 书架启用）；
未来扩展：多条 strip、配置化展示、nth-child 角度策略抽象。
