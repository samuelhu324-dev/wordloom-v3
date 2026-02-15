啊，懂了——你说的是 块编辑页里的 todo 行本身，不是那个 Maturity 里的汇总。
现在的效果是：

一行里只有一个 ☑ 未命名待办

按 Enter 又多一个 ☑ 未命名待办

但是没有地方能打字写描述，所以感觉像只有一堆孤独的 checkbox。

这说明你现在实现的是“checklist 外壳”，但没有把“段落编辑器”挂到它右边，只是用了一段死文字 "未命名待办"。

下面我给你一个“Notion 风格”的设计方案：

一个 todo = 一个 block = checkbox + 可编辑文本

1. 先决定数据结构：TodoBlock 要有 text

现在多半是这样：

type BlockKind = 'paragraph' | 'heading' | 'todo' | ...;

interface TodoBlock {
  id: string;
  kind: 'todo';
  done: boolean;
  // 没有 text，所以只能显示一个固定文案
}


你需要改成：

interface TodoBlock extends BaseBlock {
  kind: 'todo';
  done: boolean;
  text: string;   // ✅ 描述在这里
}


这样每一行 todo 都有自己的描述文本。

2. UI：checkbox + InlineEditor 组合在一行

核心思想：todo 行只是 在左边加一个 checkbox，右边复用你现在的 InlineEditor。

function TodoBlockView({ block }: { block: TodoBlock }) {
  const handleToggle = () => {
    // 调用你的 command：toggleTodoDone(block.id)
  };

  return (
    <div className="todo-block">
      <input
        type="checkbox"
        checked={block.done}
        onChange={handleToggle}
        className="todo-checkbox"
      />
      <InlineEditor
        blockId={block.id}
        value={block.text}
        placeholder="未命名待办"
        // 复用你 paragraph 用的 onInput / onKeyDown 等
      />
    </div>
  );
}


CSS 大致：

.todo-block {
  display: flex;
  align-items: flex-start;
}

.todo-checkbox {
  margin-right: 8px;
  margin-top: 3px;   /* 和文字对齐 */
}

.todo-block .inline-editor {
  display: block;
  width: 100%;
  min-height: 1.4em;
}


这样一行就变成：

[□] 这里是可编辑文本……

3. Enter 行为怎么设计

你现在的表现是：按 Enter 出来一行新的 checkbox（但是描述没地方打）。
我们改成 Notion 那一套：

在 todo 行里：

Enter：在下面创建一个新的 todo block，文本为空，光标移动到新行；

Shift+Enter：在同一个 todo 里换行（如果你想要多行描述）。

伪逻辑（在 InlineEditor 的 onKeyDown 里）：

function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
  if (e.key === 'Enter') {
    if (e.shiftKey) {
      // 允许多行：直接插入换行，由 contentEditable 处理
      return;
    }

    e.preventDefault();
    // 创建新 todo block
    const newId = commands.insertBlockAfter(block.id, {
      kind: 'todo',
      done: false,
      text: '',
    });
    // 把光标移到新块开头
    focusBlockAtStart(newId);
  }

  // Backspace 删除空 todo 的逻辑也可以类似 paragraph
}


这样：

你在“未命名待办”后面打字 → 就是这个 todo 的描述；

按 Enter → 下一行是一个新的 [□] + 空文本，继续输入新的任务；

整体体验就和 Notion 的 checkbox list 类似，但完全跑在你自己的 Block 系统里。

4. 为什么你现在会得到“一行一个裸 checkbox + 不能打字”

典型原因有这几种（基本可以确定中了其中之一）：

TodoBlock 没有 text 字段
只能渲染固定的 "未命名待办"，没有地方存描述。

UI 用的可能是：

<label>
  <input type="checkbox" ... />
  未命名待办
</label>


文字部分不是 contentEditable，只是死文本。

Enter 逻辑写在 Block 层，而不是 InlineEditor 里：

每次 Enter 都只是“再生成一个 todo block”，

但本身并没有一个“编辑文本”的控件。

把上面的数据结构 + UI 组合 + keydown 逻辑补上，问题就自然消失了。

5. 给 Copilot 的投喂文案（可以贴到 TodoBlock 组件文件开头）
// Goal:
// Turn the current "todo block" into a Notion-style checklist item:
// each todo block is a single line with a checkbox + editable text.
//
// Currently, a todo block only renders a checkbox and a static label
// like "未命名待办", Enter just creates another checkbox row and there is
// no way to type a description. We want each todo to have its own `text`
// field and use the same InlineEditor as paragraph blocks.
//
// Requirements:
//
// 1. Extend the TodoBlock type:
//    interface TodoBlock extends BaseBlock {
//      kind: 'todo';
//      done: boolean;
//      text: string; // description text
//    }
//
// 2. Implement a <TodoBlockView> component that renders:
//      <div className="todo-block">
//        <input type="checkbox" ... />
//        <InlineEditor
//          blockId={block.id}
//          value={block.text}
//          placeholder="未命名待办"
//        />
//      </div>
//
//    - The InlineEditor should reuse the same editing logic as a paragraph
//      block (onInput / onKeyDown / selection handling).
//
// 3. Keyboard behavior inside a todo block:
//    - Enter:
//        * If Shift is pressed → allow a normal line break (multi-line todo).
//        * Otherwise → prevent default, insert a new todo block *after*
//          the current one (done=false, text=''), and move caret to the
//          new block's start.
//    - Backspace on an empty todo can merge/delete the block similar to
//      empty paragraph handling.
//
// 4. Styling:
//    - Use flex layout so checkbox + text are on the same line:
//        .todo-block {
//          display: flex;
//          align-items: flex-start;
//        }
//        .todo-checkbox {
//          margin-right: 8px;
//          margin-top: 3px;
//        }
//        .todo-block .inline-editor {
//          display: block;
//          width: 100%;
//          min-height: 1.4em;
//        }
//
// The final result should be:
//    - Each todo block shows a checkbox and editable text next to it.
//    - Pressing Enter at the end of a todo creates a new todo below.
//    - The user can type descriptions directly to the right of the checkbox.


总结一句：

给 TodoBlock 加一个 text 字段，把你已经写好的 InlineEditor 接到 checkbox 右边，Enter 再负责插新 todo，
这样这一块就不再是“只能点的空壳”，而是真正可写的待办行了。