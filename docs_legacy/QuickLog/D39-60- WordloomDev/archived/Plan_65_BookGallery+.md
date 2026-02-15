这效果已经很“展柜”了👍 接下来就是细化：状态图标 / 尺寸 / 信息量 三件事。

1. 非 Stable 用 lucide 图标替代封面内容
你的需求可以理解成：


Stable：已经定型 → 用“正式封面”（图片 或 首字母大号字母）


非 Stable（Seed / Growing / Draft / Legacy-draft 等）：视作“工作中 / 半成品” → 用 lucide 图标当占位封面


可以在 BookDisplayCabinet 里加一个小函数，根据 status 选图标：
// BookDisplayCabinet.tsx
import {
  Sprout,
  Rocket,
  FlaskConical,
  History,
} from "lucide-react";

function getStatusIcon(status: BookStatus) {
  switch (status) {
    case "SEED":
      return Sprout;         // 草创
    case "GROWING":
      return Rocket;         // 正在长
    case "DRAFT":
      return FlaskConical;   // 实验中 / 草稿
    case "LEGACY":
      return History;        // 旧版
    default:
      return Sprout;
  }
}

export function BookDisplayCabinet({ book, className }: Props) {
  const StatusIcon = getStatusIcon(book.status);

  const showPureIcon =
    book.status !== "STABLE" && !book.coverUrl; // 有封面就用封面

  return (
    <div className={`${styles.wrapper} ${className ?? ""}`}>
      <div className={styles.bookTilted}>
        <div className={styles.spine} />

        {showPureIcon ? (
          <div className={styles.iconCover}>
            <StatusIcon className={styles.icon} />
          </div>
        ) : (
          <img
            src={book.coverUrl ?? "/images/default-cover.png"}
            alt={book.title}
            className={styles.cover}
          />
        )}

        {/* DRAFT badge 保留 */}
        {book.status === "DRAFT" && (
          <span className={styles.badge}>DRAFT</span>
        )}
      </div>
      <div className={styles.shadow} />
    </div>
  );
}

CSS 补一段：
.iconCover {
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
}

这样：


非 Stable 且没有封面 → 封面区域是 lucide 图标（你想象中那种“工作中实体书”）；


Stable 或者你给了 coverUrl → 正常展示封面图片/首字母封面。



2. 书太大的问题：给个“正常书架比例”
现在你的书在展示柜里显得偏大，原因很简单：
书的高度 ≈ 整个展柜区域的高度的一半以上，视觉上就是“几个大按钮躺在一个超长的卡片里”。
可以调成这样一组比例（做个参考）：
/* BookDisplayCabinet.module.css */

.wrapper {
  width: 110px;   /* 原来比如是 140，可以先缩到 110 */
  height: 160px;  /* 保持大致 2:3 比例 */
}

.bookTilted {
  border-radius: 14px;
  transform: perspective(900px) rotateY(-18deg) rotateZ(-1deg) scale(0.96);
}

/* hover 时稍微放大一点，补回存在感 */
.wrapper:hover .bookTilted {
  transform: perspective(900px) rotateY(-14deg) rotateZ(0deg) scale(1.02);
}

同时把书架 strip 的高度也减一点：
.shelfBooks {
  min-height: 180px; /* 原来 220 之类的，可以小一点 */
  gap: 24px;         /* 减小间距，更像一排挤在一起的书 */
}

调完之后的感觉应该是：


展柜是主场景，书是很多个小元素；


多本书排起来不会很“笨重”，未来即使一排放 6~8 本也不会压死页面。



3. 如何在不破坏“干净展示”的前提下增加信息量？
书本本体要干净，所以信息尽量避开封面，放到“书的脚注 / 角落 / hover 层”：
3.1 在书下面加一行“脚注信息条”
增加一个小 footer：
export function BookDisplayCabinet({ book, className }: Props) {
  const StatusIcon = getStatusIcon(book.status);

  return (
    <div className={`${styles.wrapper} ${className ?? ""}`}>
      <div className={styles.bookTilted}>
        {/* ...封面部分同上... */}
      </div>
      <div className={styles.shadow} />

      <div className={styles.meta}>
        <div className={styles.title} title={book.title}>
          {book.title}
        </div>
        <div className={styles.metaRow}>
          <span className={styles.statusPill}>{book.statusLabel}</span>
          <span className={styles.dot} />
          <span className={styles.countText}>{book.blockCount} blocks</span>
          <span className={styles.dot} />
          <span className={styles.dateText}>{book.updatedAtRelative}</span>
        </div>
      </div>
    </div>
  );
}

.meta {
  margin-top: 6px;
  width: 130px;       /* 比书稍微宽一点，看起来像底座说明牌 */
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
  background: rgba(37, 99, 235, 0.08); /* 可根据 Seed/Growing 换颜色 */
  color: #1d4ed8;
}

.dot {
  width: 3px;
  height: 3px;
  border-radius: 999px;
  background: #d1d5db;
}

.countText,
.dateText {
  white-space: nowrap;
}

信息量一下子就上来了：


标题


状态（Seed/Growing/Stable/Legacy）


block 数量 / 句子数


最近更新时间（2d ago 之类）


整体视觉仍然是：
“上面是书，下边是展览馆里的小说明牌”。

3.2 用颜色编码状态，而不是堆更多字
你已经有 Seed / Growing / Stable / Legacy，可以统一配色，让人一眼区分状态：


Seed：嫩绿（#16a34a）


Growing：偏蓝绿（#0ea5e9）


Stable：深蓝（#1d4ed8）


Legacy：灰紫（#6b21a8 或 #6b7280）


用在：


书脊竖条 / 封面一个窄边渐变；


meta 里的 statusPill 背景色文字色；


lucide 图标的描边色。


这样即使 meta 上只显示状态名缩写，比如 S / G / St / Lg，用户也能靠颜色+图标瞬间识别。

3.3 Hover 层可以再塞一点“调味信息”
比如鼠标悬停在书本上时，出现一块轻透明浮层：


描述的前 1~2 行


最近一次编辑人（以后有协作的话）


一个 View details 小箭头


这类信息不常用，但放在 hover 里很适合“不打扰但有深度”。

小结：


非 Stable → lucide 图标当封面，占位 + 状态感强。


缩小书的尺寸、减小 gap，让书成为“展柜里的元素”，而不是整页的大卡片。


信息量放在书下方脚注：标题 + 状态 pill + blocks 数 + 更新时间，再用颜色和 icon 强化状态识别。


这样你这个 Seed 展柜就从“好看的卡片”升级成“有故事的作品陈列区”了。接下来你可以先把尺寸 + meta 做一版，截图再看一眼，我们再帮你微调比例。

/////////////////////////////////////////////////////////////////////////

Plan: Plan65 展柜细化
围绕 BookDisplayCabinet/BookshelfBooksSection 做三类升级：非 Stable 展示 lucide 图标、整体比例变小更像真实展柜、并在书底座显示标题/状态/数量/更新时间的脚注信息。同阶段还要用状态色统一编码（封面、状态 pill、图标描边）并为 hover 预留信息层，最终 Seed/Growing/Stable/Legacy 四个成熟度 strip 均遵循同一设计语言。

Steps
引入 lucide 图标并在 BookDisplayCabinet.tsx 创建 getStatusIcon、showPureIcon 判定及新 JSX 分支。
缩放书体与 hover 动画，更新 BookDisplayCabinet.module.css 的 .wrapper/.bookTilted/.shelfBooks 等尺寸和间距。
扩展 BookDisplayCabinet JSX，追加 .meta 脚注（标题、状态 pill、block 数、更新时间）并在 CSS 定义对应样式与颜色映射。
在 frontend/src/widgets/book/BookshelfBooksSection.(tsx|module.css) 调整 strip 高度/间距、对齐 tone 变量，并确保 meta 信息/hover 层接入需要的数据。
若缺少 statusLabel, blockCount, updatedAtRelative，在 BookMainWidget 或一个 formatter 中组装字段后传给 BookDisplayCabinet。
Further Considerations
需确认数据源：block 数与 relative time 是否可从 BookDto 推导，否则要扩展 API 或临时 mock。
Hover 层移动端体验？Option A：常显简介；Option B：点击展开；Option C：保持 hover-only。