好，终于到软换行终章了 🎉
我们现在的目标是：在不动现有 Enter/keyboardDecider/退出逻辑的前提下，加一条独立又安全的 Shift+Enter→软换行通路，让 Copilot 按图施工就行。

我给你拆成一份可以直接「扔给 Copilot」的实施方案，你可以原样贴到注释 / TODO / PR 描述里。

一、行为规范（先写清“应该怎样”）

写给人、也写给 Copilot：

Shift+Enter 软换行规则

作用范围：

普通段落 block（paragraph）

列表项 / todo 项内部（list item / todo item）

效果：

只在当前 block 内插入软换行，不创建/删除任何 block，不触发 list/todo 退出逻辑

光标移动到换行后的行首

列表/todo 情况下：左边只保留一个点/勾选框，右侧文字变成多行，整体仍是一个 item

数据表示：

使用文本里的 \n 作为软换行标记（或者沿用底层编辑器已有的 soft-break API）

判空规则调整：

isEmpty / deleteGuard 判空时，只包含空格和 \n 的文本仍视为“空”

二、改动约束（告诉 Copilot 哪些不能乱碰）

也一起写明白：

实现 Shift+Enter 时 不要动：

keyboardDecider 中的 Enter / Backspace 流程

各种 *-exit / deleteBlockWithGuard / 退出逻辑

Shift+Enter 走一条独立分支：
在 ParagraphEditor（或 InlineEditor）里的 onKeyDown 最前面拦截并处理，然后 return，不要再往下传播。

三、具体实现步骤（给 Copilot 的施工指令）
Step 1：在 ParagraphEditor 拦截 Shift+Enter

伪代码结构（让 Copilot在对应文件里找 onKeyDown，补这个分支）：

function handleKeyDown(e: KeyboardEvent) {
  // 1. 最高优先级：软换行
  if (e.key === 'Enter' && e.shiftKey) {
    e.preventDefault();
    paragraphCommands.insertSoftBreak(); // 需要在 commands 里实现
    return;  // ✅ 不再往下走，避免触发 keyboardDecider / submit
  }

  // 2. 普通 Enter：交给 keyboardDecider 现有逻辑
  if (e.key === 'Enter') {
    return handleInlineEditorKeyDown(e);
  }

  // 3. 其他按键维持现状
}


要求点明：

位置要放在最前面，确保普通 Enter 的逻辑不会抢到 Shift+Enter；

处理完软换行以后必须 return，不然还会落到原来的 Enter 流程里。

ListEditor / TodoListEditor 只要复用 ParagraphEditor，这个效果会自动带过去，不需要额外分支。

Step 2：实现 insertSoftBreak 命令

让 Copilot去你现在管理文本的地方（Draft.js / useState(text) / 你自己的 Drafts 模型）加一个命令：

需求说明：

获取当前光标位置（offset）

计算新文本：
newText = text.slice(0, offset) + '\n' + text.slice(offset)

更新编辑器 state，并把光标移到换行后的 offset（原 offset + 1）

不触发任何 block 级别的 submit / create / delete

伪代码：

function insertSoftBreak() {
  const selection = editorState.selection; // 具体视你用的编辑库而定
  const offset = selection.startOffset;

  const text = getCurrentText();
  const newText = text.slice(0, offset) + '\n' + text.slice(offset);

  updateText(newText, offset + 1); // 更新文本并同步 selection
}


如果你底层用的是 Draft.js / Slate 之类，本身就有 RichUtils.insertSoftNewline() / Transforms.insertText(editor, '\n') 这种 API，可以让 Copilot直接调用，不自己拼字符串，但原则一样：

只是改 inline 文本，不动 blocks。

Step 3：渲染层支持 \n → 视觉换行

告诉 Copilot检查你现在的渲染方式：

如果是 <textarea> / <input>：
浏览器天然就会按 \n 换行，不用动。

如果是 <div contentEditable> / 自己渲染文字节点：
需要做其中一种处理：

在文本渲染元素上加 CSS：

white-space: pre-wrap;


或者在渲染时把 \n 映射成 <br />：

function renderText(text: string) {
  return text.split('\n').map((line, i) =>
    i === 0 ? line : (<><br />{line}</>)
  );
}


指令：任选其一，但要保证 \n 在 UI 里显示为同一条列表项里的多行文字。

Step 4：更新“判空逻辑”（isEmpty / deleteGuard）

因为你现在很多地方都有 isEmpty(text) 来决策“空列表最后一项是否退出”等，需要让 Copilot统一改成把软换行也当作空白处理。

让它去找类似：

const isEmpty = text.trim().length === 0;


改成：

const normalized = text.replace(/\s+/g, '');
const isEmpty = normalized.length === 0;


或等价写法，要求是：

文本只包含空格、\t、\n 等空白 → 视为“空”

这样就避免“用户只是按了几下 Shift+Enter，看起来是空行，但系统认为“有内容”导致 list/todo 退出行为怪异。

Step 5：加最小的测试 / 回归脚本

你可以让 Copilot帮忙在现有 vitest 测试里加几条，非常具体地写出来：

在 keyboardDecider / ListBlock / TodoListBlock 的测试里补 3 个用例：

段落软换行

初始文本 "abc|def"（| 为光标）

按 Shift+Enter → 文本变 "abc\n|def"，block 数量不变。

列表项软换行

list item 文本 "item|1"

按 Shift+Enter → 文本变 "item\n|1"，仍然是一个 list item，keyboardDecider 不被调用，list 不新增/删除 item。

空列表 + 软换行不退出

整个 list 只有一条空 item，

连续按 Shift+Enter 不触发 list-exit / deleteGuard，只是在同一个 item 里插入 \n。

退出规则仍然只由普通 Enter / Backspace 决定。

测试目的：保证：

Shift+Enter 不会走你的 block 级 Enter/Backspace 通路；

不会再出现“按软换行结果列表爆成两 para”这种玄学。

四、可以直接给 Copilot 的摘要文本

你可以把这段直接复制给 Copilot 作为指令（按你习惯再微调）：

任务：为 Wordloom 的 block 编辑器实现 Shift+Enter 软换行。要求：

行为：

适用于 paragraph / list item / todo item

只在当前 block 文本里插入 \n，不创建/删除 block，不触发 list/todo 退出逻辑

渲染时同一条列表项里的文字会换成多行（一个点撑起多排内容）

约束：

不修改 keyboardDecider 的 Enter/Backspace 分支

不修改 deleteGuard 的语义

Shift+Enter 必须在 ParagraphEditor 的 onKeyDown 顶部拦截并处理后 return

实现步骤：

在 ParagraphEditor / InlineEditor 的 onKeyDown 中添加：

若 e.key === 'Enter' && e.shiftKey：preventDefault()，调用 paragraphCommands.insertSoftBreak() 并 return

在 paragraphCommands 中实现 insertSoftBreak()：

获取当前 selection offset

在当前文本中插入 \n

更新文本 state，并把光标移动到换行后的 offset

在渲染层支持 \n：

对使用 div 渲染文本的地方，使用 white-space: pre-wrap; 或在渲染时将 \n 映射为 <br />

更新所有 isEmpty 辅助函数：

把只包含空白和 \n 的文本视为“空”，用于 list/todo 退出逻辑与 deleteGuard

增加 vitest 用例：

段落软换行（插入 \n，block 数不变）

list item / todo item 软换行（仍然一个 item，不触发 keyboardDecider）

空列表多次 Shift+Enter 不退出列表，只是插入空行

实现完成后，手动验证：

段落 / 列表 / todo 中 Shift+Enter 都是“同一块里换行”，不会多生成 block

普通 Enter / Backspace 行为和当前版本一致。

这样，你这条“软换行分支”就能独立接上现有的键盘架构，不会把刚刚好不容易理顺的 Enter/退出逻辑再搅浑。
剩下就是让 Copilot按这个剧本写代码，你只需要看它有没有乖乖遵守“只动 ParagraphEditor + commands + 渲染层”这三个点。