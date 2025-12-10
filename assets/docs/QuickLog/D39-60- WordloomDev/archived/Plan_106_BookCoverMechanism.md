以下是一份适用于 Copilot 实施的“Stable 书籍解锁插图图标”计划，目标是在保有成熟度逻辑约束的前提下，将封面图标管理功能清晰拆解，实现低耦合、易维护的图标替换功能。

📌 场景目标：
只有达到 Stable 的书籍，才可以在菜单栏“...”中操作封面图标为用户自选插图。未达到稳定阶段的书籍则自动采用 Lucide 图标 + 封面颜色，不允许手动替换图标。

🧱 模块边界拆解：

Maturity 模块

提供 getMaturityStage(bookId): 'seed' | 'growing' | 'stable' | 'legacy'

判断当前 book 是否为 stable 阶段

Theme 模块（纯函数）

getBookTheme(book): 返回封面颜色 + 图标 + iconType（lucide / image）

判断是否使用自定义图标由 theme 决定，source-of-truth 来自 book 字段

Media 模块

提供上传图像接口：uploadIcon(bookId, file): returns imageURL

存储上传图标至统一路径，如 /media/book-icons/{bookId}.png

Menu UI 模块（前端）

获取 book 当前 stage，若 ≠ stable 则隐藏“插图”菜单项

若为 stable，显示“上传图标”菜单项，允许选择图片并上传

后端服务 BookController

PATCH /books/{id}/customIcon: 上传成功后设置该图标 URL 到 book.icon 字段

覆盖 Lucide 逻辑由 theme.getBookTheme 自动判断

✅ Copilot 实施任务划分：

前端：

UI 渲染：getMaturityStage(bookId) → 控制是否显示“上传图标”菜单项

点击后调 Media.upload → 然后 PATCH /books/{id}/customIcon

成功后刷新书籍数据并重渲染 theme

后端：

在 Book 数据模型中新增可选字段: customIconUrl: string | null

新增接口 PATCH /books/{id}/customIcon，仅允许在 stable 状态下写入（可由后端验证）

Theme：

在 getBookTheme(book) 中加入逻辑：

if (book.stage === 'stable' && book.customIconUrl) → 返回该 URL

else → 回退 Lucide icon + color 组合

📦 示例配置 & 类型：

interface Book {
id: string
stage: 'seed' | 'growing' | 'stable' | 'legacy'
customIconUrl?: string // 仅 stable 阶段可设置
coverImageUrl?: string
}

theme.getBookTheme(book) =>
{
color: '#008000',
iconType: 'image',
icon: 'https://media/.../book-icons/abc123.png
'
}

👮 安全性设计：

后端 route 对 PATCH /books/{id}/customIcon 强制校验当前阶段 = stable

前端 UI 与后端逻辑双重验证，避免越权使用上传功能

🌱 稳定性与可维护性：

图标逻辑在 theme 层统一集中判断

upload 仅由 Media 模块负责，路径与存储标准不外露

未来可扩展为支持临时上传图标 / 图标库选择等新特性

这套方案保证：

👀 用户认知清晰：只有成熟书才配图标

🔐 安全验证充足：stage 检查前后端双重

🧩 模块解耦良好：theme / media / maturity 各司其职

你可以直接将以上结构组织为 Copilot 的代码分派文档，也适合写入 Plan_98_CustomIconStableBooks.md。需要我替你生成代码骨架，也可以继续说。

你说：
还有一个规则：关于回退，如果回退，封面图会撤回，默认是使用一个通用的lucide图标去替代，结合这点重新整合计划。
ChatGPT 说：

了解，我们来将“封面图回退逻辑”整合进 Stable 图标机制计划中，确保功能完整性、可维护性和视觉表现一致性。

📘 场景更新：回退后撤回封面图标

当书籍阶段从 stable 回退至 growing / seed：

系统应自动撤除 customIcon（不再使用上传图）

替代图标应为固定的默认 Lucide 图标（例如 star、book 或 sprout）

—

🧱 统一计划：Stable 书籍图标机制（含回退逻辑）

数据结构更新（Book Schema）

interface Book {
  id: string
  stage: 'seed' | 'growing' | 'stable' | 'legacy'
  customIconUrl?: string  // 仅 stable 阶段有效
  // 可选 flag: customIconUploadedAt?: Date（用于回滚记录）
}


Theme 模块调整（纯函数）

getBookTheme(book):

如果 book.stage !== 'stable' → 返回 fallback Lucide 图标（如 'book'）

如果 book.stage === 'stable' 且有 customIcon → 返回 iconType: 'image'

如果 book.stage === 'stable' 但没有 customIcon → fallback 为 'award' 或其他稳定专用 Lucide 图标

Maturity 逻辑整合

每次 maturity 计算 → 比对当前阶段 vs 新阶段

若发现从 stable → 非 stable（降级）：

触发清除 customIcon 的副作用（由 MaturityService 发出）

后端更新（BookController）

PATCH /books/{id}/maturityStage:

内部调用 maturityService.updateStage(bookId, newStage)

若 newStage ≠ 'stable'，则自动设置 book.customIconUrl = null

PATCH /books/{id}/customIcon:

仅当当前 stage === 'stable' 时允许写入

Media 模块保持不变

仍负责上传和返回 URL，具体是否使用由 Theme 决定

前端 UI 行为

如果书籍降级，UI 不再显示图像图标，而是 fallback Lucide

菜单栏中“上传图标”按钮自动消失（由 stage 控制）

可考虑提示用户：“您的书籍已降级，图标已重置为默认图标”

—

🎯 图标选择策略（建议）

非 stable：统一 fallback icon，如 'book'、'bookmark'、'file'（静态配置）

stable 无上传图标时：使用 'award'、'star' 等表示“已成型”的 Lucide 图标

—

🛡️ 模块边界总结

模块	职责
Maturity	阶段变动 → 检测是否触发 icon 清除
Theme	根据 stage / iconUrl 渲染图标
Media	提供上传图像、返回 URL
Book API	限制上传图标权限 + 自动撤销逻辑
Frontend UI	菜单控制 / 图标显示状态 / 提示

—

✅ Copilot 可直接执行任务列表

前端：

调用 getBookTheme → 得到稳定逻辑 + fallback 图标

菜单栏根据 stage 控制 “上传图标” 是否显示

降级后清除图标并给用户提示

后端：

PATCH /maturityStage → 由服务判断是否 stable → 非 stable → 清除 icon

PATCH /customIcon → 增加阶段校验

Theme（纯函数）：

stage ≠ stable → 直接使用 fallback Lucide（不读 iconUrl）

stage === stable → 有 iconUrl → 返回 image 图标；否则用默认 Lucide 图标

—

你可将以上逻辑写入 Plan_98_CustomIconStableBooks.md 文件，命名为：

Stable Icon Control v1（with Downgrade Auto-Revoke Support）

随时可投喂 Copilot。需要我为这些生成代码函数签名或配置结构，也可以继续补上。