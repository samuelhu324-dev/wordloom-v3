0. 前提 & 范围

已存在：

BlockEntity 模型（包含 id / bookId / index / kind / content / createdAt / updatedAt / deletedAt?）。

BlockKind 枚举，目前至少有：'paragraph' | 'heading' | 'bulleted_list' | 'numbered_list'。

「块编辑」页面采用「展示态 + 编辑态」模式，每个 block 由 BlockRenderer 负责渲染。

本次目标：在现有系统上新增以下 BlockKind，并完成基础编辑器 + 展示器：

todo_list

callout

quote

divider

image

image_gallery

1. 数据模型扩展（后端 + 前端共享类型）
1.1 更新 BlockKind

在公共类型文件里，把 BlockKind 扩展为：

export type BlockKind =
  | 'paragraph'
  | 'heading'
  | 'bulleted_list'
  | 'numbered_list'
  | 'todo_list'
  | 'callout'
  | 'quote'
  | 'divider'
  | 'image'
  | 'image_gallery';

1.2 为每种 kind 约定 content 结构

注意：content 字段仍然是 JSON；这里是约定 schema，方便前后端共用。

export interface TodoListContent {
  items: {
    id: string;           // 前端生成 uuid
    text: string;         // 暂时纯文本，后续可升级 RichText
    checked: boolean;
    isPromoted?: boolean; // true 时推到 Book 级 TODO
  }[];
}

export interface CalloutContent {
  variant: 'info' | 'warning' | 'danger' | 'success';
  text: string;
}

export interface QuoteContent {
  text: string;
  source?: string;
}

export interface DividerContent {
  style?: 'solid' | 'dashed';
}

export interface ImageContent {
  imageId: string;       // 媒体库 id
  url: string;           // 预览地址
  caption?: string;
}

export interface ImageGalleryItem {
  id: string;
  url: string;
  caption?: string;
  indexLabel?: string;   // 1 / 2 / 3 之类标号
}

export interface ImageGalleryContent {
  layout: 'strip' | 'grid';
  maxPerRow?: number;
  items: ImageGalleryItem[];
}


后端 blocks 表不用改结构，只需要保证 content 正确序列化这些结构。

2. TODO List Block（todo_list）
2.1 后端

允许创建 kind = 'todo_list' 的 block，content 为上面定义的 TodoListContent。

API 不需要新接口，复用现有：

POST /blocks：创建 todo_list；

PATCH /blocks/{id}：更新整个 content；

DELETE /blocks/{id}：软删除。

2.2 前端展示组件：TodoListDisplay

位置：在 BlockRenderer 下新建：

function TodoListDisplay(props: {
  block: BlockEntity<TodoListContent>;
  onToggleItem(id: string): void;
  onTogglePromote(id: string): void;
  onEnterEdit(): void;
}) { ... }


行为：

渲染为一列 checkbox 列表：

左侧是 checkbox（checked 对应 item.checked）；

文本使用普通段落样式；

在 block 右上角工具栏下面，可以额外放一个小图标/标签显示「Todo」。

checkbox 勾选时：

直接在前端更新 content.items 中对应项的 checked；

立刻调用一次 PATCH /blocks/{id}（轻量请求）；

如果 isPromoted === true，同时调用一个 updateBookTodoFromBlock 的 helper，把状态同步到 Book 级 TODO Tab（见 2.4）。

2.3 前端编辑组件：TodoListEditor

v2 先做一个简单可用版本，不做富文本。

接口：

function TodoListEditor(props: {
  block: BlockEntity<TodoListContent>;
  onChangeContent(content: TodoListContent): void;
  onExitEdit(save: boolean): void;
}) { ... }


交互：

每一行是：

checkbox

input[type="text"] 文本输入框

一个小星标 / 图钉按钮用于切换 isPromoted

新增行：

在列表底部有一行「+ 新增待办」；

或在最后一个 input 回车时自动追加新项。

删除行：

行尾 hover 时出现删除小 icon，删除该 item。

保存：

退出编辑（blur / Esc / 切块）时，调用 onChangeContent(updatedContent)；

外层负责发 API 并恢复展示态。

2.4 与 Book TODO Tab 的联动（最小版本）

先做一个「软联动」版本：

建一个 helper：extractPromotedTodosFromBlocks(blocks: BlockEntity[])，返回：

{ text: string; blockId: string; itemId: string; checked: boolean }[]


Book TODO Tab 中：

读取当前 Book 所有 blocks；

调用 helper 得到「来自 block 的 TODO 项」；

作为只读/半只读列表展示（勾选时可以直接回写对应 block）。

将来可以把 Block TODO 项映射到单独的 book_todos 表，但 v2 起步不需要动数据库，先用「视图型联动」。

3. Callout / Quote / Divider Block

这三种本质都是「视觉组件 + 简单文本」，适合一起做。

3.1 Callout（callout）

展示组件：

function CalloutDisplay(props: { block: BlockEntity<CalloutContent>; onEnterEdit(): void }) { ... }


样式建议：

左侧彩色竖条 + 图标（info / warning / danger / success 不同颜色）；

右侧正文文本；

整体缩进一点，作为文档中的“高亮卡”。

编辑组件：

双击或点击进入编辑；

上方是一个 variant 选择（下拉或小标签：信息 / 提醒 / 风险 / 成功 等）；

下方是 textarea 编辑内容；

退出编辑时保存。

3.2 Quote（quote）

展示组件：

左侧引号/竖线；

主体是 text；

底部右侧可以显示 — source（如果有）。

编辑组件：

两个输入区：

主要文本 textarea；

来源（可选）单行 input；

退出编辑时保存。

3.3 Divider（divider）

展示组件：

一个 <hr /> 风格的线；

如果 style === 'dashed'，用虚线样式。

编辑/配置：

divider 基本不需要编辑器；

插入后默认 style 为 solid；

如果要切换样式，可以在 toolbar 的「更多」里加一项「切换为虚线」。

4. Image / ImageGallery Block

这块可以走「最小可用版本」：先只支持 URL / 简单上传；高级媒体库以后再做。

4.1 Image（image）

展示组件 ImageBlockDisplay：

显示图片（限制宽度，保持比例）；

下方显示 caption（可选）；

点击图片可放大预览（可以用现成 lightbox 或简易 modal）。

编辑组件 ImageBlockEditor：

字段：

图片来源：

一个「选择图片…」按钮（打开你现有的上传 / 选择接口）；

或直接输入 URL 的 input（最小版本）。

caption 文本框。

行为：

选择/上传图片后，填充 imageId + url；

退出编辑时保存。

4.2 ImageGallery（image_gallery）

展示组件 ImageGalleryDisplay：

支持两种布局：

layout = 'strip'：一行横向缩略图条，超出可横向滚动；

layout = 'grid'：多行网格，maxPerRow 控制每行数量。

每个图片支持点击放大；

可显示 indexLabel（角标 1 / 2 / 3）和 caption。

编辑组件 ImageGalleryEditor（v2 简化版）：

提供一个「添加图片」按钮：连续添加多张；

每一张图片一行：

缩略图预览；

URL / 上传按钮；

caption 输入框；

删除按钮；

上方有布局选项：

单选：条形 / 网格；

可选 maxPerRow（最多 5）。

排序：

v2 简化为列表顺序就是展示顺序，不做拖拽；

后续可以加 drag & drop 调整次序。

5. 插入入口 & Block 类型菜单

为了能在编辑器里插入这些新类型，需要扩展「插入 block」菜单。

5.1 全局插入按钮

在「+ 添加一段文字」旁边，增加一个主按钮 / dropdown：

「+ 插入块」→ 展开菜单：

基础：段落、标题、列表、编号列表

Todo：待办列表

标注：Callout、引用、分割线

媒体：图片、图片组

选中某个类型时：

在当前 block 之后插入一个新 BlockEntity；

kind 设置为对应值；

content 用合理的默认值，例如：

todo_list: { items: [{ id: uuid(), text: '', checked: false }] }

callout: { variant: 'info', text: '' }

quote: { text: '', source: '' }

divider: { style: 'solid' }

image: { imageId: '', url: '', caption: '' }

image_gallery: { layout: 'strip', items: [] }

设置 editingBlockId 为新 block id，进入编辑态。

5.2 已有 block 的类型切换（可选）

v2 可以暂时忽略复杂的类型切换，只做「插入即是最终类型」。
真正的跨类型转换（比如段落 → todo_list）可以以后再设计。

6. 给 Copilot 的工作指令模板

你可以在 VS Code 里对 Copilot 说明：

参考 Plan_78_BlockTypes_v2_Todo_Callout_Media.md。

在现有 Block 系统上实现新的 BlockKind：todo_list, callout, quote, divider, image, image_gallery。

从数据模型开始：扩展 BlockKind、定义对应 content 类型，并在 Block API 中支持这些 kind。

在前端的 BlockRenderer 中，为新增 kind 实现 Display 组件和简单 Editor 组件，遵守「展示态 + 编辑态」模式。

为「添加 block」入口增加一个菜单，可以插入这些新类型的 block，并为它们填充合适的默认 content。

对 todo_list，实现勾选、增删项、提升到 Book TODO Tab 的最小联动功能（使用提取 TODO 的 helper）。

这样，Copilot 就不会只是“帮你补一小段代码”，而是按照整套脚本去填充各种组件和类型。
你这边的工作重点就变成：检查它写出来的结构有没有偏离这份计划，再微调视觉和交互。