Shift+Enter 的“块内换行”不应该再加额外间距，行距 = 普通行高；
Enter 的“新块换行”才用 block gap token，多一点距离。

也就是：

同一段里无论是自动换行，还是你自己 Shift+Enter 换行，行与行之间的垂直距离应该一模一样；

只有「上一段结束 → 下一段开始」的时候，才多插一口气，让段落之间比行距稍微大一点。

这是 Word / Google Docs / Notion 一致的习惯。

1. 视觉标准怎么定？

假设你现在是：

font-size: 16px;
--wl-line-height-body: 1.6;   /* 你文件里就是这个 */


那一行文字的行高大概是：

行距 ≈ 16px × 1.6 ≈ 25–26px

A. Shift+Enter（段内软换行）

目标：行距 = 行高，不额外加 gap

同一段里面的所有行（包括 Shift+Enter 产生的）：

baseline 到 baseline 距离 ≈ 25–26px；

不使用任何 --wl-space-* token；

不要给 <br> 或内部 wrapper 加 margin-top / margin-bottom。

对应实现原则：

.bookEditor_paragraph {
  line-height: var(--wl-line-height-body); /* 1.6 */
}

.bookEditor_paragraph br {
  margin: 0;
  padding: 0;
}


或者你用 white-space: pre-wrap 的那条路，只要保证没有额外 margin即可。

B. Enter（新块 / 新段落）

目标：段落之间比行距略大一点，大约 1.1–1.3 倍行距

传统排版里，16px 字体、1.5–1.6 行高时，常见做法：

段距（段落间 baseline→baseline）≈ 行距 + 4–10px；

也就是大约 30–34px，肉眼能看出来「这里是分段」但不会很稀。

结合你自己的 token 梯子（你截图里是）：

--wl-space-1: 2px;
--wl-space-2: 4px;
--wl-space-2-5: 6px;
--wl-space-3: 8px;
...


可以定一条简单规则给 Copilot：

段内行距：只用 line-height。

段间距：row-gap: var(--wl-space-block-tight)，
且 --wl-space-block-tight 取 var(--wl-space-2-5)（6px）或 var(--wl-space-3)（8px）。

这样：

段内行距：约 26px；

段间距：26px + 6–8px ≈ 32–34px；

段间距 ≈ 1.2–1.3 × 行距 —— 很典型的「紧凑但清晰」阅读节奏。

你之前已经有：

.bookEditorShell .blockList {
  row-gap: var(--wl-space-block-tight);
}


只要确认 --wl-space-block-tight 取的是 6px 或 8px 就行。

2. 给 Copilot 的核对 / 指令

你可以直接这样跟 Copilot 说：

我们区分两种垂直距离：

段内行距 = line-height，用于普通换行和 Shift+Enter 软换行；

段间距 = 行距 + 一个 block gap token，用于 Enter 产生的新 block。

请检查：

Paragraph / List / Todo 内部，包含 Shift+Enter 渲染的 <br>，行与行之间只受 line-height 影响，不要给 <br> 或内部 span/div 加任何 margin-block。

.blockList 或外层容器使用 row-gap: var(--wl-space-block-tight); 控制块与块之间距离。

--wl-space-block-tight 的值设为 var(--wl-space-2-5)（6px）或者 var(--wl-space-3)（8px），在 16px 字体、--wl-line-height-body: 1.6; 的前提下，保证：

段内 baseline 间距 ≈ 26px；

段间 baseline 间距 ≈ 32–34px。

也就是说：Shift+Enter 产生的换行，视觉上和自然换行完全一样；只有 Enter 产生的新 block，才多出 --wl-space-block-tight 这一口气。

3. 快速自测方法

你手上这个界面，可以用 DevTools 这样查：

对着 Shift+Enter 那两行中的任意一行，用 DevTools 看 computed：

确认 line-height ≈ 24–26px；

中间没有任何 margin/padding。

在刚好两段之间移动鼠标，打开「布局 rect」看两行 baseline 的垂直距离：

如果是行高 + 6–8px，说明 block gap token 生效；

如果差不多一样，说明还有地方把 block gap 吃掉了。

只要保证这两层节奏分开，用户看到的就会很自然：
Shift+Enter = 同一段里「排版用换行」，Enter = 真的换了一个段落。