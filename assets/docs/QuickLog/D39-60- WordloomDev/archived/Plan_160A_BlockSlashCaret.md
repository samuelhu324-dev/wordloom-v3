目标

Slash 菜单在当前 caret 附近弹出，而不是跑到左上角。

菜单相对于 BlockEditor 外层容器 定位（而不是整个窗口）。

实现思路：

BlockEditor 有一个 editorRootRef，指向包住所有 block 的 DOM。

当按下 / 并决定要弹菜单时：

用 window.getSelection() 拿当前 caret 的 Range；

用 getBoundingClientRect() 拿到 caret 的 viewport 坐标；

再减去 editorRoot 的 getBoundingClientRect()，变成相对于编辑器容器的坐标；

把这个 {x,y} 存到 state 里，当作菜单的 anchor。

Slash 菜单是一个 position: absolute 的 div，挂在 editorRoot 里面，用这个 {x,y} 定位。

一、BlockEditor 里增加状态 & ref

文件：BlockEditor.tsx（或你现在的主编辑器组件）

const BlockEditor: React.FC<BlockEditorProps> = (props) => {
  const editorRootRef = React.useRef<HTMLDivElement | null>(null);

  const [slashMenuState, setSlashMenuState] = React.useState<{
    open: boolean;
    x: number;
    y: number;
  }>({
    open: false,
    x: 0,
    y: 0,
  });

  // ... 其它 state & hooks


编辑器最外层容器记得挂上 ref，并且 position: relative：

  return (
    <div
      ref={editorRootRef}
      className={styles.bookEditorShell}
    >
      {/* block list / timeline 等都在这里面 */}
      {/* Slash menu 也放在这里 */}
      {slashMenuState.open && (
        <SlashMenu
          x={slashMenuState.x}
          y={slashMenuState.y}
          onClose={() => setSlashMenuState(s => ({ ...s, open: false }))}
        />
      )}
    </div>
  );
};

/* bookEditor.module.css */
.bookEditorShell {
  position: relative; /* 关键：给内部绝对定位提供参考 */
}

二、写一个专门算 caret 位置的 helper

文件：可以单独 editor/getSlashMenuAnchor.ts，也可以直接放在 BlockEditor.tsx 里。

export function getSlashMenuAnchor(editorRoot: HTMLElement): { x: number; y: number } | null {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;

  const range = selection.getRangeAt(0);

  // 防止 selection 在编辑器外面
  const startNode = range.startContainer;
  if (!editorRoot.contains(startNode)) {
    return null;
  }

  // 我们只关心 caret 位置，如果选了一段文字，先折叠到末尾
  if (!range.collapsed) {
    range.collapse(false);
  }

  // 有些场景 getClientRects 是空的，兜底用 getBoundingClientRect
  const rects = range.getClientRects();
  const caretRect = rects.length > 0 ? rects[0] : range.getBoundingClientRect();

  if (!caretRect) return null;

  const editorRect = editorRoot.getBoundingClientRect();

  // 把 viewport 坐标转换成 editor 内部坐标
  const x = caretRect.left - editorRect.left;
  const y = caretRect.bottom - editorRect.top;

  // 稍微往右下偏移一点，不要贴着文字
  const OFFSET_X = 0;
  const OFFSET_Y = 4;

  return {
    x: x + OFFSET_X,
    y: y + OFFSET_Y,
  };
}


注意点已经帮你写死了：

selection 不在 editor 里就直接返回 null；

非 collapsed selection 折叠到末尾；

getClientRects 为空时用 getBoundingClientRect() 兜底；

统一用 editorRect 做坐标系。

三、在 / 的 keydown 里调用这个 helper

你现在应该已经有类似这样的逻辑（伪代码）：

const handleKeyDown = (event: React.KeyboardEvent) => {
  // ... 其它快捷键

  if (event.key === '/' && !event.shiftKey && isCaretInEmptySegment()) {
    event.preventDefault();
    // 这里以前只是打开菜单，现在顺便算坐标
  }
};


升级为：

const handleKeyDown = (event: React.KeyboardEvent) => {
  // ... 其它快捷键

  if (event.key === '/' && !event.shiftKey && isCaretInEmptySegment()) {
    event.preventDefault();

    const root = editorRootRef.current;
    const anchor = root ? getSlashMenuAnchor(root) : null;

    setSlashMenuState(prev => ({
      open: true,
      x: anchor?.x ?? 16, // 如果没拿到，就给个兜底位置
      y: anchor?.y ?? 16,
    }));

    return;
  }

  // ... 其它逻辑
};


给 Copilot 的指令要点：

handleKeyDown 里 先做 event.preventDefault() 再算坐标再 setSlashMenuState；

不要在每次 keydown 都重新算坐标，只在真正要打开菜单那一刻算一次。

四、Slash 菜单组件的样式（跟上坐标）

组件：SlashMenu.tsx

interface SlashMenuProps {
  x: number;
  y: number;
  onClose: () => void;
}

export const SlashMenu: React.FC<SlashMenuProps> = ({ x, y, onClose }) => {
  return (
    <div
      className={styles.slashMenu}
      style={{
        position: 'absolute',
        left: x,
        top: y,
        zIndex: 1000,
      }}
    >
      {/* 这里渲染 Todo / Bullet List / Quote 等列表 */}
    </div>
  );
};

/* bookEditor.module.css 或单独 slashMenu.css */

.slashMenu {
  min-width: 240px;
  max-height: 320px;
  padding: 6px 4px;
  border-radius: 8px;
  background: var(--color-surface, #fff);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
  overflow-y: auto;
}

五、给 Copilot 的“翻译版指令”

你可以直接复制下面几句给 Copilot，当 task 描述用：

「在 BlockEditor.tsx 里，给外层 .bookEditorShell 添加 ref={editorRootRef} 和 position: relative；新增 slashMenuState { open, x, y }。」

「实现一个 getSlashMenuAnchor(editorRoot: HTMLElement) 函数，使用 window.getSelection().getRangeAt(0)，如果 selection 不在 editorRoot 内则返回 null；若 Range 非 collapsed，调用 range.collapse(false)；使用 range.getClientRects()[0] 或 range.getBoundingClientRect() 获取 caretRect，然后用 caretRect.left - editorRect.left 和 caretRect.bottom - editorRect.top 计算相对坐标。」

「在 handleKeyDown 里拦截 '/'，在满足 !event.shiftKey && isCaretInEmptySegment() 时，event.preventDefault()，调用 getSlashMenuAnchor(editorRootRef.current!)，用结果更新 slashMenuState 打开菜单。」

「将 SlashMenu 渲染为 editorRoot 内部的一个 position: absolute 容器，使用 left: slashMenuState.x; top: slashMenuState.y 来定位。」

这样丢给它，它就应该照着堆代码了。

如果你按上面这个版本改，Slash 菜单就会稳定地跟在 caret 下方，不会再神秘地跑去页面左上角；之后要再细调美观、动画、对齐，就只是 CSS 小事了。

六、落地记录（2025-12-04）

- `frontend/src/modules/book-editor/model/getSlashMenuAnchor.ts` 已实现纯函数版本的定位 helper，强制 collapsed caret + editorRoot.contains 检查，selection 不命中时直接返回 null。
- `BlockList` 作为外层 shell 新增 `editorRootRef` + `slashMenuState { open, x, y, blockId, onSelect }`，并将 `.bookEditorShell` 设置为 `position: relative` 以承载绝对定位菜单。
- Slash 触发链路：`ParagraphEditor` 只在 `!event.nativeEvent.isComposing && event.key === '/'` 时触发；`BlockItem` 把 blockId + 绑定好的 `handleQuickActionSelect(action, 'slash')` 往上抛，BlockList 统一调用 `getSlashMenuAnchor()` 计算坐标。
- 新增 `frontend/src/modules/book-editor/ui/SlashMenu.tsx`，在 shell 内部使用 `position: absolute` 渲染 quick actions 分组；ESC / 点击外部都会调用 `onClose`，行为与旧 `QuickInsertMenu` 保持一致。
- 旧 `QuickInsertMenu` 只在 plus 菜单使用，Slash 路径全部切换到 `SlashMenu`，避免双定位模型混用；`handleQuickActionSelect` 支持 `triggerOverride` 以保留 transform 逻辑。
- 当前版本只在打开时计算一次坐标，并提供 16px 兜底；如果超出编辑区域尚未翻转，上层 TODO：可在后续版本添加简易 overflow 翻转逻辑。