这个条目模式已经挺有“资源卡”味道了，现在看空主要有三个原因：

卡片太宽：内容都挤在左边，右边大片白；

竖向节奏偏松：上下 padding 多、行数少；

信息都贴在左上角，没有用到“中间”和“右侧”的位置。

所以解决思路不是“塞一堆新信息”，而是：
把原来就有的信息重新排布 + 稍微补一点很轻的辅助信息，把空间“撑起来”，而不是“填爆”。

我给你一个具体改造方案，方便你直接喂给 Copilot。

一步：先把卡片本身压紧一点
1. 卡片尺寸 & padding

现在看上去像 120px 高 + 24px padding 这种级别，可以改成：

.bookRowCard {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow:
    0 10px 30px rgba(15, 23, 42, 0.06),
    0 0 0 1px rgba(226, 232, 240, 0.9);
  gap: 16px;
  min-height: 80px; /* 控制在 80–88 之间 */
}

2. 列宽 & 总宽度

把整个列表区域加一个最大宽度，不要让卡片横跨整屏：

.bookList {
  max-width: 960px;   /* 或 880px */
  margin: 0 auto;
}


这样卡片会显得更紧凑，不会像一条“巨大白条”。

第二步：把一张卡拆成「左封面 / 中信息 / 右小面板」

结构：

<div className="bookRowCard">
  <div className="leftCover">
    <BookCover3D />
  </div>

  <div className="middleInfo">
    {/* 标题 + 一行副标题 + 一行灰色 meta */}
  </div>

  <div className="rightMeta">
    {/* 两三项垂直对齐的小统计 / 状态 pill */}
  </div>
</div>

leftCover

保持现在的缩略书封就好，高度控制在 60–72px，不要太大。

.leftCover {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}

第三步：中间信息区：三行刚刚好

目标：用三行填满纵向节奏，又不显得多。

JSX 示意
<div className="middleInfo">
  <div className="titleRow">
    <span className="title">{book.title}</span>
    <span className="statusPill">Seed · 草创</span>
  </div>

  {book.subtitle && (
    <div className="subtitle" title={book.subtitle}>
      {book.subtitle}
    </div>
  )}

  <div className="metaRow">
    <span className="metaText">{book.blockCount} blocks</span>
    <span className="dot" />
    <span className="metaText">{book.updatedAtRelative}</span>
  </div>
</div>

CSS 大致
.middleInfo {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;      /* 行距缩紧一点 */
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
  background: rgba(34, 197, 94, 0.08); /* Seed 绿 */
  color: #16a34a;
}

.subtitle {
  font-size: 13px;
  color: #4b5563;
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


这样一来：

标题行撑起上半部；

副标题（有就显示，没有就收起来）填中间；

meta 行（blocks + 时间）填下半部，整体变得充实但信息点其实没变很多。

第四步：右侧做一个「很克制的小统计柱」

不加会很空，加太多会变 Bookshelf。我的建议是：只放 2–3 个垂直排列的小项目，做成“侧边标尺”的感觉。

示例：

<div className="rightMeta">
  <div className="rightItem">
    <span className="rightLabel">使用</span>
    <span className="rightValue">{book.openCount}</span>
  </div>
  <div className="rightItem">
    <span className="rightLabel">状态</span>
    <span className="rightValueSoft">活跃</span>
  </div>
</div>


如果现在数据没那么多，你甚至可以先只放一个“进入”箭头：

<div className="rightMeta">
  <button className="openButton">
    查看
  </button>
</div>


CSS：

.rightMeta {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 4px;
  min-width: 80px;
}

.rightItem {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.rightLabel {
  font-size: 10px;
  color: #9ca3af;
}

.rightValue {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}

.rightValueSoft {
  font-size: 12px;
  color: #4b5563;
}

.openButton {
  padding: 4px 10px;
  font-size: 11px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #4b5563;
}


**关键点：**右侧永远只占一小块，不堆横向 icon 行，这样不会变成“mini dashboard”，只是一点“补充信息”。

第五步：整体紧凑但不挤的几个小手段

行间距用 gap: 2px，不要用默认 4–8px，全局看卡片会“收一点”；

取消卡片内部的多余空行，比如 title 下不要再额外 margin-top: 4px；

列表上下卡片之间的间距控制在 8–10px 左右，避免“上下浮空”。

给 Copilot 的一句话指令示例

你可以差不多这样说（英文有利于它理解）：

Make the BookRowCard more compact but not crowded:

Limit the card height to around 80–88px and reduce vertical padding.

Split the content into three zones: leftCover, middleInfo, rightMeta.

In middleInfo, use three lines: title + small status pill, optional one-line subtitle, and a grey meta line like 0 blocks · 2 小时前.

In rightMeta, right-align 1–2 small vertical stats or a subtle “查看” button, so the right side no longer feels empty.

Add max-width: 960px; margin: 0 auto; to the list container to avoid super-wide white bars.

照这个方向走，Book 条目页会变成：

信息比现在丰富、排布更“满”，

但又明显比 Bookshelf 那个战斗型列表轻很多，
整个层级感就清晰了：这里是选书和欣赏，不是 KPI 控制台。