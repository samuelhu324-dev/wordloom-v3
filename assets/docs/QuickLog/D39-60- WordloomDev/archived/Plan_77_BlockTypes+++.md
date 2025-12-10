Plan_77 – Block Types & Block Editor v1/v2 规范（给 Copilot 用）

使用方式（给 Copilot 的一句话）：
按本文件说明重构 Book 的「块编辑」Tab：实现基于 BlockKind 的渲染器 & 编辑器，先完成 v1 阶段（纯文本 block + 展示/编辑双态），再按阶段逐步支持更多 Block 类型。

0. 总体目标

数据上：Book 由一组有序 Block 组成：
Book -> Blocks[Block]，每个 Block 有 kind、content、createdAt、updatedAt 等字段。

UI 上：用户看到的是一段一段的正文，尽量接近 Word / Notion 的感觉，而不是一堆卡片。

扩展性：BlockKind 设计要支持后续增加新类型（图片、截图条、代码等），不破坏现有结构。

审计友好：保留 Block 级别的 created_at / updated_at，在 UI 中以「低噪音 + 可查看」的方式呈现。

1. Block 数据模型（最终目标 v2）

后端 / 数据层：

// BlockKind 枚举
export type BlockKind =
  | 'heading'
  | 'paragraph'
  | 'bulleted_list'
  | 'numbered_list'
  | 'todo_list'
  | 'code'
  | 'callout'
  | 'quote'
  | 'divider'
  | 'image'
  | 'image_gallery'
  | 'custom';

// Block 主体（content 用 JSON）
export interface BlockEntity {
  id: string;
  bookId: string;
  index: number;         // 排序用（从 0 或 1 开始）
  kind: BlockKind;
  content: any;          // 实际内容，按 kind 解析
  createdAt: string;
  updatedAt: string;
  deletedAt?: string | null;
}


说明：Comment 不是 BlockKind，而是独立实体 BlockComment，挂在 Block 上（以后再做）。

2. Block 类型详细规格（以最终 v2 为准）

注意：这是「最终目录」；实现时按阶段拆解（见第 3 部分）。

2.1 文本基础

heading

字段：{ level: 1 | 2 | 3; text: string }

用途：章节标题，小节标题（可用于自动目录）。

paragraph

字段：{ text: RichText }

用途：普通正文段落（翻译、说明等）。

2.2 列表 / 任务

bulleted_list

字段：{ items: RichText[] }

numbered_list

字段：{ items: RichText[] }

todo_list

字段：

{
  items: {
    text: RichText;
    checked: boolean;
    isPromoted?: boolean; // true 时升级到 Book 级 TODO
  }[];
}

2.3 工程 / 高亮

code

字段：{ language: string; code: string }

功能：代码高亮 + 一键复制。

callout

字段：{ variant: 'info' | 'warning' | 'danger' | 'success'; text: RichText; }

quote

字段：{ text: RichText; source?: string }

2.4 结构 / 媒体

divider

字段：{ style?: 'solid' | 'dashed' } 或空对象。

image

字段：{ imageId: string; url: string; caption?: string }

image_gallery

字段：

{
  layout: 'strip' | 'grid';    // 默认 strip
  maxPerRow?: number;          // 默认 4 或 5
  items: {
    id: string;
    url: string;
    caption?: string;
    indexLabel?: string;       // 1 / 2 / 3 标号
  }[];
}


custom

字段：{ schemaVersion: string; data: unknown }

用途：未来实验型结构（表格、图表等）。

3. 实现分期（v1 先干什么，v2 再扩）

这部分是「给 Copilot 的 TODO 清单」。

3.1 v1 – 只实现 paragraph，但改成 Block 化 + 展示/编辑双态

目标：
继续只支持「纯文本段落」，但所有逻辑都基于 Block 数据模型，并引入「展示态 BlockDisplay / 编辑态 BlockEditorArea」。

后端 / API：

确认 blocks 表结构包含：

id, book_id, index, kind, content(json), created_at, updated_at, deleted_at?

现有「文本块」数据迁移为：

kind = 'paragraph'

content = { text: 原来的内容 }

API 保持：

GET /books/{id}/blocks

POST /blocks（创建 paragraph）

PATCH /blocks/{id}（更新内容）

DELETE /blocks/{id}（软删除）

前端：Book 块编辑页重构

在 Book 块编辑 Tab 中：

从后端拿的是 BlockEntity[]。

组件中新增：

const [editingBlockId, setEditingBlockId] = useState<string | null>(null);


新建 BlockRenderer 组件：

现在只支持 kind === 'paragraph'。

当 editingBlockId === block.id 时渲染 BlockEditorArea；

否则渲染 BlockDisplay。

BlockDisplay：

以 <div> 或 <p> 方式展示文本；

样式接近 Word 段落：无边框、无背景，仅在 hover 时略微高亮；

点击时触发 setEditingBlockId(block.id) 进入编辑。

BlockEditorArea：

使用 <textarea>（复用你当前逻辑），autoFocus；

支持：

Ctrl+S / Cmd+S 保存；

Enter+Ctrl/Cmd 保存（如果你想保留）

Esc 取消编辑（不提交，回到原内容）；

onBlur 时自动保存（可选）。

保存成功后调用 setEditingBlockId(null) 回到展示态。

Block 右上工具栏：

保留 Clock（时间线/审计入口预留）和 Trash2（删除）图标；

toolbar 默认 opacity: 0，在 block hover 或编辑态时 opacity: 1；

在 Clock 旁显示简短的「更新 · 3 小时前」文字（前端用相对时间格式化）。

「添加一段文字」按钮：

在列表末尾展示一个淡色按钮：+ 添加一段文字;

点击后调用创建 paragraph 的 API，并将 editingBlockId 设置为新 block 的 id。

完成 v1 后，页面已经「无 block 卡片感」，但底层已完全 Block 化，为后续类型扩展打好基础。

3.2 v1.5 – 基础文本类型（heading + bulleted/numbered_list）

目标：
在现有 Block 系统上增加 Text 相关类型，让文档结构更清晰，但 UI 仍然保持简单。

后端：

支持 kind = 'heading' | 'bulleted_list' | 'numbered_list'。

约定 content 结构：

heading: { level: 1 | 2 | 3; text: string }

bulleted_list: { items: RichText[] }

numbered_list: { items: RichText[] }

前端：

扩展 BlockRenderer：

根据 kind 渲染不同的展示组件：

HeadingBlockDisplay

BulletedListDisplay

NumberedListDisplay

暂时可以共用一个编辑器组件，简单到：

heading：单行 textarea；

list：多行 textarea，每一行一个 item（先不做真正的富文本编辑器）。

插入入口（简单版）：

在「添加一段文字」按钮旁边，增加一个 更多… 菜单，允许选择：

段落 / 标题 / 列表 / 编号列表；

或者在 BlockDisplay 左侧预留一个小 H / • 图标用于类型切换（后续 v2 可以完善）。

3.3 v2 – TODO / Callout / Quote / Divider / Media

这个阶段可以在 v1.5 稳定后再启动，现在只做规划：

todo_list：

编辑器：支持勾选，isPromoted 与 Book TODO Tab 联动。

callout, quote, divider：

以视觉组件形式呈现；

可以作为“工程批注的正文版本”。

image / image_gallery：

接入你的媒体库 / 上传接口；

image_gallery 作为「小缩略图条 / 网格」，点击放大。

4. 审计 & 时间线（关联说明）

暂时不要求实现完整时间线，只约定字段与 UI 显示方式。

Block 必须有 createdAt, updatedAt。

前端在每个 block 右上角显示：

一条简短的「更新 · 相对时间」；

hover 或点击 Clock 图标时展示 tooltip：

创建于 2025-11-27 14:32

最近更新 2025-11-27 15:06

Book「时间线」Tab 将来可以基于 Block 的重要变更（新增 / 删除 / TODO 完成等）来生成事件。

5. Copilot 提示模板（你可以直接贴给它）

可以在 VS Code 里这样对 Copilot 说：

项目：Wordloom 前端，Book 的「块编辑」Tab。

目标：按照 Plan_77_BlockTypes++++.md 中的 v1 规范，把当前“多文本区域”的实现重构为基于 Block 的展示/编辑双态。

数据模型：使用 BlockEntity 和 BlockKind（见文档）。

只实现 kind = 'paragraph'，但代码结构要为将来扩展其它 BlockKind 预留（BlockRenderer、BlockDisplay / BlockEditorArea）。

保留已有保存 / 删除 / 时间戳显示逻辑，UI 上保持接近「一行一段的 Word 文档」，不要再使用 card 样式。

这样一来：

对你自己：这是一个可以长期维护的 Block 规范 + 实施路线图；

对 Copilot：有很清晰的「现在做 v1，只管 paragraph，但按最终 BlockKind 架构写」的指令；

对以后 demo / 面试：你可以拿出 Plan_77 说“这里是我对编辑器 Block 系统的分阶段设计”。

你可以先把这份 plan 贴进 Wordloom 的 Plan 文档里（比如 Plan_77_BlockTypes++++.md），然后从 v1 段落 Block 重构 开始，让 Copilot 帮你把现在的块编辑页一步步迁过去。