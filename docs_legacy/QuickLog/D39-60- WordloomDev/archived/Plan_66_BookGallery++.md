1. 书名为什么突兀 & 怎么改

现在突兀的原因是：

书本是 3D + 投影，但文字是平的、直接贴在大背景上；

文字宽度和书的宽度没有对齐，视觉上像是“随手放的标签”；

文字行距、间距和上面的 3D 感不在一个“体系”里。

调整思路（推荐）

给每本书做一个“小铭牌”，和书绑定在一起：

铭牌宽度 ≈ 书宽度或略宽 8px

放在书正下方 6–8px

有非常浅的底色 + 圆角 + 一点点阴影

结构类似：

<div className={styles.bookColumn}>
  <div className={styles.bookTilted}>…</div>
  <div className={styles.shadow} />
  <div className={styles.plaque}>
    <div className={styles.title} title={book.title}>{book.title}</div>
    <div className={styles.metaRow}>
      <span className={styles.statusPill}>Seed · 草创</span>
      <span className={styles.dot} />
      <span className={styles.metaText}>{book.blockCount} blocks</span>
      <span className={styles.dot} />
      <span className={styles.metaText}>{book.updatedAtRelative}</span>
    </div>
  </div>
</div>


样式：

.bookColumn {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 120px; /* 统一列宽 */
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


这样书 + 铭牌是一体的“小展品”，而不是上面一块、下面一行散着的字。

2. 封面颜色怎么和 Library 主题契合，又不容易翻车

不要直接“从封面图提取主色 + 直接用”，那样非常容易翻车（过亮、过饱和、偏灰）。
比较稳妥的做法是：

2.1 给每个 Library 一个“安全主题色 token”

比如在 Library 元数据里只存一条：

library.accentColor = "#2563eb";  // 一条主色


然后你在前端做“受限处理”：

把 hex 转成 HSL；

强制限制到一个安全区间，比如：

saturation: 35%–60%

lightness: 35%–55%

再根据这个 HSL 生成不同用途：

const coverStart = adjust(lightness - 5);
const coverEnd   = adjust(lightness + 5);
const spineColor = adjust(lightness - 15);
const iconColor  = adjust(lightness + 35);


这样：

不同 Library 还是有自己的“性格”（色相差异保留）；

但饱和度/明度永远不会离谱，UI 一定“合规”。

2.2 避免“状态”和“主题色”互相打架

建议：

封面主色来源于 Library 主题色

状态（Seed / Growing / Stable / Legacy） 用细节表示：

书脊上的细窄条颜色不同；

铭牌上的 statusPill 用不同色；

lucide 图标描边用不同色。

这样你不会出现“主题色 + 状态色 + 图标色三重混战”，整体会干净很多。

3. 展柜整体排布怎么更自然、更优雅

现在的感觉“不自然”的原因大概有三点：

展柜高度偏大，书集中在左上，下面大片空白；

书之间的关系是“横排一字”，有点死板；

书、铭牌、底部那条长长的 rail 之间的节奏还没统一。

给你一个稳定、安全的布局方案（偏“美术馆展柜”风格）：

3.1 展柜压低一点，书架板抬高一点

shelfStrip 高度改低一点，比如 220–240px；

木板（那条灰蓝长条）上移，让书的阴影刚好压在板上；

核心是：书群 + 铭牌占满中间三分之二，不要全挤在顶部。

3.2 左对齐 + 稍微错落

现在是有一点点错落了，再往前走半步：

.shelfBooks {
  display: flex;
  align-items: flex-end;
  gap: 24px;
  justify-content: flex-start; /* 左对齐，不要居中 */
}


然后给不同顺位一点点“表演”：

.shelfBooks > :nth-child(1) .bookTilted {
  transform: perspective(900px) rotateY(-18deg) rotateZ(-1deg);
}

.shelfBooks > :nth-child(2) .bookTilted {
  transform: perspective(900px) rotateY(-16deg) rotateZ(0deg) translateY(-4px);
}

.shelfBooks > :nth-child(3) .bookTilted {
  transform: perspective(900px) rotateY(-20deg) rotateZ(1deg) translateY(-2px);
}


错落幅度要非常小，肉眼感觉是“自然摆放”，而不是“刻意乱摆”。

3.3 给右侧留一块“呼吸空间”

你现在右侧是大空白，可以干一件很简单又高级的事：
在右边淡淡放一句 Seed 区的小描述 + 一个 lucide 图标（超浅灰）。

例如：

位置：展柜右上角，离书群有明显距离；

内容（很短的一句）：

“Seed：快速捕捉灵感，尚待整理。”

颜色：#cbd5e1 这种级别的灰，字体 12px 即可。

这样视觉效果是：

左半边：真实书本 + 铭牌（主角）

右半边：淡淡的“说明文字”，平衡留白

这就是你说的那种“不经意的美感”：看起来好像只是留白，其实有很弱的结构在支撑。

4. 小结：一套可落地的“安全改法”

综合一下，如果你现在只想做一次稳定升级，我建议这一轮做到：

书 + 铭牌绑定成一个展品单元：名字不再裸贴在背景上。

Library 主题色 → 受限 HSL → 封面渐变 + 书脊色 + 图标色，不直接用“原图取色”。

展柜高度下降、书群左对齐、轻微错落 + 右侧留一个淡淡文案区域。

做到这三点后，这个 Seed 展柜页会从“好看的组件”进化成“真的像一排实体书放在展台上”，而且和上层 Libraries 的卡片风格会统一很多，整个链路（Library → Bookshelf → Book）就有那种一脉相承的“合规美感”。