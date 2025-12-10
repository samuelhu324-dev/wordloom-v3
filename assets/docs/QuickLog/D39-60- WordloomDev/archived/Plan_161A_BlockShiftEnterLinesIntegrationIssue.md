一、原因：你在「保存/重建」的某一环节把软换行弄丢了

浏览器这边的逻辑是这样的：

Enter：在 contenteditable 里通常是「新 block」——新的 <div> / <p>。

Shift + Enter：在同一个 block 里插入软换行，DOM 里表现为一个 <br> 标签。

你现在的现象是：

编辑态里 Shift+Enter 能看到两行 → DOM 里有 <br>。

一保存 / 刷新后变成一行 → <br> 在序列化 / 反序列化的过程中被吃掉了。

典型几种吃掉方式：

从 DOM 取文本的时候用的是 element.textContent，然后再做了
replace(/\s+/g, ' ') / .trim() 之类的「清理」——\n 被当成普通空白合并掉；

或者干脆把 innerHTML 里的 <br> 过滤出去了，只保留纯文本；

反向渲染的时候直接把字符串塞进一个正常的 <div>，CSS 又是 white-space: normal，
即使字符串里有 \n，浏览器也会把它当作空格处理 → 视觉上还是一行。

所以本质就是一句话：

编辑态的 <br> 没有被映射到「模型里的软换行」上，或者映射了但在显示时没按软换行渲染。

二、你要先拍板一个语义：Shift+Enter = 段内软换行

我们先约定好语义，方便 Copilot 照着实现：

每个 paragraph / list item 的内容模型是一个 string；

其中的 \n 表示「同段落内的软换行」（就对应编辑态的 <br>）；

不是新 block，只是一个段内多行文本。

三、给 Copilot 的改造方案（可以直接粘）
1. DOM → 模型：保留 <br>，转换成 \n

在保存 block 文本的那条链路上，一定有类似下面的 helper：

function extractTextFromParagraph(dom: HTMLElement): string {
  // 现在大概是这样：
  // return dom.innerText.trim()
  // 或者 return dom.textContent ?? ''
}


改成显式处理 <br>：

// editor/serializeParagraph.ts
export function extractTextFromParagraph(dom: HTMLElement): string {
  // 1. 克隆一份，避免直接改真实 DOM
  const clone = dom.cloneNode(true) as HTMLElement;

  // 2. 所有 <br> 统一替换成换行符占位
  //    这样 innerText / textContent 里就会有 '\n'
  clone.querySelectorAll('br').forEach((br) => {
    br.replaceWith('\n');
  });

  // 3. 用 innerText 拿到“用户看到的文字”，其中已经带了 '\n'
  let text = clone.innerText;

  // 4. 规范化换行 & 去掉多余的首尾空白，但不要把 '\n' 删掉
  text = text.replace(/\r\n/g, '\n');      // Windows → Unix
  // 这里可以去掉首尾空白，但不要用 /\s+/g
  text = text.replace(/\u00a0/g, ' ');     // nbsp → 空格
  return text.trimEnd();                   // 只剪掉结尾的空白，不动中间的 '\n'
}


然后让 Copilot把所有保存 paragraph / list item 文本的地方都换成调这个 helper：

const newText = extractTextFromParagraph(paragraphDom);
updateBlock(blockId, { text: newText });


同理：Todo item / Bullet item 如果也是 text model，一样走这个 helper。

2. 模型 → 视图：把 \n 渲染成真正的软换行

你的只读态 / 编辑态渲染大概类似这样：

// 现在可能只是普通 div
<div className={styles.paragraphText}>{block.text}</div>


让 Copilot在两边做二选一（任选其一即可）：

方案 A：分段渲染 + <br />
// components/ParagraphView.tsx
function renderParagraphText(text: string) {
  const parts = text.split('\n');
  return parts.map((part, index) =>
    index === 0
      ? part
      : [<br key={`br-${index}`} />, part],
  );
}

export const ParagraphView: React.FC<{ text: string }> = ({ text }) => {
  return (
    <div className={styles.paragraphText}>
      {renderParagraphText(text)}
    </div>
  );
};


注意让 Copilot 把 List/Todo 的文本渲染也改成同一个 helper，保持行为一致。

方案 B：用 CSS white-space: pre-wrap

如果你用的是纯文本节点渲染，可以直接让 CSS 帮你处理换行：

<div className={styles.paragraphText}>{block.text}</div>

/* bookEditor.module.css */
.paragraphText {
  white-space: pre-wrap; /* 保留 \n → 换行，多空格压缩 */
}


这样字符串里的 \n 会直接渲染成换行，而不会被合并成空格。

编辑态的 contenteditable 元素同样可以加 white-space: pre-wrap，
这样 “从模型恢复回 DOM” 时，Shift+Enter → \n → 视觉上仍然是多行。

3. 编辑态初始化：从字符串反填回 DOM

如果你的 ParagraphEditor 在 mount 时会根据 block.text 预填内容（例如通过 innerText = text 或 React children），也要保证 \n 还原为 <br> 或预留为真实换行。

两种方式对应前面的 A / B：

如果你走 <br> 路线：
初始化时把 \n 转回 <br>：

function textToHtmlWithBr(text: string): string {
  return text
    .split('\n')
    .map((line) => escapeHtml(line))
    .join('<br>');
}

editableElement.innerHTML = textToHtmlWithBr(block.text);


如果你走 white-space: pre-wrap 路线：
直接把字符串塞进 DOM，让浏览器自己处理：

<div
  contentEditable
  className={styles.paragraphEditor}
  style={{ whiteSpace: 'pre-wrap' }}
  suppressContentEditableWarning
>
  {block.text}
</div>

4. 跟 Copilot 说清楚的指令摘要（你可以直接贴给它）

Shift+Enter 在 Paragraph / ListItem / TodoItem 里表示段内软换行，我们要把它持久化为字符串中的 \n。

请实现一个 extractTextFromParagraph(dom: HTMLElement): string，按照下面步骤：

克隆 DOM；

把所有 <br> 替换成 '\n' 文本节点；

用 clone.innerText 获取文本，保留 \n；

规范化为 Unix 换行（\r\n → \n），去掉结尾多余空白，但不要删除中间的 \n。

所有保存段落 / 列表项文本的地方都改成调用这个 helper。

在视图层：

方案 A：实现一个 renderParagraphText(text: string) 把 \n 分割成多个片段，中间插入 <br />；

方案 B：视图容器增加 white-space: pre-wrap，直接渲染字符串文本即可。
任选其一，应用到 ParagraphView、ListItemView、TodoItemView 中。

确保 ParagraphEditor 初始化时能把 block.text 中的 \n 正确渲染成多行文本（对应选择的方案），这样保存→刷新→重新进入编辑，软换行不会丢失。

这样改完之后，Shift+Enter 生成的“块内多行”会：

编辑时：还是 <br>；

保存时：序列化成字符串里的 \n；

下次打开：从 \n 还原成多行，视觉上不会被压成一行。

四、当前实施计划（中文版速记）

1. 序列化 helper：新增 `frontend/src/modules/book-editor/model/inlineText.ts`，封装 `extractInlineTextFromEditable`，负责把 contenteditable DOM 克隆后将 `<br>` 替换为 `\n`，规范化换行并返回字符串；所有文本类 block 保存流程（Paragraph/List/Todo）统一调用。
2. 编辑核心接线：在 `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` 的 `handleInput` 中调用上述 helper；Shift+Enter 热键逻辑在 `frontend/src/modules/book-editor/model/keyboard.ts` 内只发出软换行事件，不再阻止浏览器插入 `<br>`；`BlockItem.tsx` 的 `handleSoftBreak` 变成 no-op，保证 DOM 中真实存在 `<br>`。
3. 视图渲染：`frontend/src/modules/book-editor/ui/bookEditor.module.css` 的 `.textBlockContent`、`.todoText`、`.blockDisplay` 等类统一启用 `white-space: pre-wrap`，让模型中的 `\n` 在阅读态直接渲染成多行。
4. 验证要点：
  - 手动在段落、无序列表、待办列表依次输入 “行1 + Shift+Enter + 行2”，保存并刷新，确认换行存在；
  - Slash 菜单 / 块操作条在多行文本里依旧正常；
  - `npm run type-check` 运行，若出现非本次改动导致的历史错误，记录在案并告知。