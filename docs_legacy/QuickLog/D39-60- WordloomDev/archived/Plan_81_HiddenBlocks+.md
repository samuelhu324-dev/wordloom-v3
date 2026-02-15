A. 先用样式做到「看起来不像一坨卡片」

目标：视觉上是一整张纸，中间是一串段落，block 只是你心里的概念。

1. 去掉「卡片」感，只留段落感

现在每个块都有一块白底 + 较大圆角，看起来像一张一张卡。

可以改成：

每个 block 外层容器仍然有一点 padding: 8px 0，但：

背景：和父容器同色（比如都是 #F8FAFC 这种），不要再加一层白底。

不要阴影，不要边框。

.block-container {
  padding: 8px 0;
  background: transparent;
  box-shadow: none;
  border: none;
}


这样多个 block 连在一起，视觉上就像一篇文档的多段文本。

2. 把 textarea 伪装成普通段落

给 textarea 做三个处理：

背景透明：

.block-textarea {
  background: transparent;
  border: none;
  box-shadow: none;
  resize: none;
  line-height: 1.7;
  font-size: 15px;
}


默认 不画边框，只有 focus 时在底部画一条淡淡的线：

.block-textarea {
  border-bottom: 1px solid transparent;
}
.block-textarea:focus {
  outline: none;
  border-bottom-color: #cbd5f5; /* 非常浅的蓝线 */
}


把 placeholder 的说明（“直接编辑，Enter / Ctrl+S…”）改成更短、弱化颜色，只在空的时候出现；一旦用户输入文字，就完全消失。

这样看过去的效果会变成：一列段落，中间没有框，只有正在编辑的那行底部有一条线——很像在 Word 里光标选中的那一段。

3. 操作 icon 只在 hover 时出现

你已经把钟表 / 删除移到右上角了，可以再狠一点：

.block-toolbar {
  opacity: 0;
  transition: opacity 0.15s ease;
}
.block-container:hover .block-toolbar,
.block-textarea:focus + .block-toolbar {
  opacity: 1;
}


平时整列只有文字，没有“每段都挂一排按钮”的压力；

鼠标移上去 / 光标在里面时，右上角静静地出现时钟和垃圾桶。

4. 把“新增文本块”按钮从内容里拿出去

现在 + 新增文本块 挂在块列表顶部，看起来很“块编辑 UI”。

可以改成：

顶部右侧：只留一个小按钮：+ 段落；

或者干脆取消按钮，只在文末显示一个浅浅的：

[ + 添加一段文字 ]


再高级一点：在 每两个 block 之间 hover 时出现一个小 ＋ 圆点（以后再做也行），就完全是 Notion 那套手感了。