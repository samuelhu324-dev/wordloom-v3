方案 B：继续用 flex，但再加一层“内层编辑器”
如果你现在这层就是「整行」；你又非常想让这一整块都是 flex（例如要和 TODO 的 checkbox 共用一套结构），那就把 editable 下沉一层：
<div className={styles.textBlockShell /* display:flex */}>
  {/* 左边可以是拖拽 handle / checkbox 等 */}
  <div className={styles.leadingIcon}>{/* ... */}</div>

  {/* 这个才是 contentEditable，display:block */}
  <div
    className={styles.textBlockContent}
    contentEditable
    suppressContentEditableWarning
    …
  >
    {children}
  </div>

  {/* 右边更多操作 */}
  <div className={styles.trailingActions}>{/* ... */}</div>
</div>

CSS：
.textBlockShell {
  display: flex;
  align-items: flex-start;
}

.textBlockContent {
  flex: 1;
  display: block;          /* 关键：不要是 flex/grid/inline-flex */
  min-width: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

只要保证「带 contentEditable 的那一层不是 flex」，你怎么包外壳都行。

丢给 Copilot 的说明（你可以直接复制过去）
// Bug: caret keeps jumping back to the beginning while typing
// in ParagraphEditor / HeadingEditor.
//
// Root cause (Chrome / Safari):
// - We turned the contentEditable element (.textBlockShell) into
//   `display:flex`.
// - When a contentEditable node is a flex container, Chrome/Safari will
//   re-wrap its children as flex items during reflow, which causes the
//   current selection to be lost and the caret to reset to the first child.
//
// Fix:
// - The element with `contentEditable` **must not** be a flex container.
// - Use one of these approaches:
//
//   Option A (simplest):
//     - Change `.textBlockShell` back to `display:block` (keep width:100%).
//     - If we still need flex layout for icons/actions, wrap it in an outer
//       `.blockRow` that is flex, and keep the editable div itself block-level.
//
//   Option B:
//     - Keep `.textBlockShell` as `display:flex`, but move `contentEditable`
//       onto an inner child `.textBlockContent`.
//     - `.textBlockContent` should be `display:block` and take `flex:1`.
//
// Goal:
//   After the change, typing A/B repeatedly in a long paragraph should not
//   cause the caret to jump back to the start anymore.

你按这个思路改掉「contentEditable + flex」的组合，光标乱跳的问题就会消失。剩下的，只是 CSS 怎么包壳子好看一点的审美问题了。
