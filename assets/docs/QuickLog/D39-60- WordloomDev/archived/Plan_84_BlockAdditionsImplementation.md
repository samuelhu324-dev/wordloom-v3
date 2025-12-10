Plan: Plan_83 Block 类型落地与文档同步
本计划基于最新的 Plan_83 文档，在现有 Plan_77/Plan_80/Plan_82 基础上扩展 BlockKind（todo_list / callout / quote / divider / image / image_gallery），补齐前后端类型与渲染器结构，并将规范完整同步到三份 RULES 及 ADR‑108。下面是给“下一个实现代理/你自己”用的实施蓝图。

Steps
梳理与对齐现状（只读核对）

在 types.ts / index.ts 中确认现有 BlockKind、各 *BlockContent 接口以及 BlockContent 联合类型是否已覆盖 Plan_83 的六类（todo_list, callout, quote, divider, image, image_gallery）；记录差异。
在 api.ts / hooks.ts 中确认 BlockDto、BlockApiResponse、mapApiTypeToKind / mapKindToApiType / parseBlockContent 的现状，以及目前前端是否只在 paragraph 下做内容修正。
在 BlockRenderer.tsx / BlockList.tsx / BlockCard.tsx 中梳理：现在的 BlockRenderer 仅支持 paragraph 的分支结构、BlockItem 如何管理 value / 保存、BlockCard 如何展示预览。
在 DDD_RULES.yaml / HEXAGONAL_RULES.yaml / VISUAL_RULES.yaml 与 ADR-108-plan77-blockkind-roadmap.md 中确定：已经记录的 Plan_77 / Plan_80 / Plan_82 内容与 BlockKind、BlockContent 的边界与适配规则，找出 Plan_83 需要新增/扩展的空位。
数据模型 & DTO 层规划（后端/前端共识）

约定领域层 BlockKind 最终全集：在 DDD 规则中将 core set 明确为 paragraph / heading / bulleted_list / numbered_list / todo_list / code / callout / quote / divider / image / image_gallery / custom（与前端 BlockKind 类型保持一致），并强调目前新落地的 UI 仅激活 Plan_83 中六种。
明确每类 content schema 的“最终形态”（与 Plan_83 保持一一对应）：
todo_list: items[{id,text,checked,isPromoted?}]；
callout: {variant,text}；quote: {text,source?}；divider: {style?}；
image: {imageId?,url?,caption?}；image_gallery: {layout?,maxPerRow?,items[{id?,url,caption?,indexLabel?}]}。
规划后端应用层的校验策略（写在 DDD/HEX 文档里，不急着编码）：
Create/Update Block UseCase 接口保持 kind + content(json)，但在 Phase_83 对这六个 kind 引入“软校验”：只要 type/kind 对应关系正确且顶层结构是对象或期望数组即可，具体字段错误先以日志+默认值处理。
确定前端 DTO 适配责任：normalizeBlock 必须保证 BlockDto.content 始终是解析后的 JSON；parseBlockContent 在 paragraph 之外为每一种 Plan_83 kind 提供“安全兜底”的默认结构（空 items、空字符串、默认 layout 等），避免 UI 因旧数据崩溃。
前端类型 &解析规则扩展（实体层设计）

在 types.ts 中按 Plan_83 的接口命名重新核对 / 微调：
确认/补充 TodoListItemContent、TodoListBlockContent、CalloutBlockContent、QuoteBlockContent、DividerBlockContent、ImageBlockContent、ImageGalleryItemContent、ImageGalleryBlockContent，字段语义与 Plan_83 文档保持一致。
将这些接口统一纳入 BlockContent 联合类型，并在 index.ts 中向外导出，供 UI 和未来 TODO/Media 特性引用。
为常见类型设计轻量级 type guard / helper（规划即可）：例如 isTodoListContent, isImageGalleryContent，用于 BlockRenderer 内安全判断。
设计扩展版 parseBlockContent(kind, rawContent) 的规则（写在计划中，后续实现）：
paragraph：保持现有 {text} 封装逻辑；
todo_list：如果解析结果不是对象或没有 items，生成 items: []；否则对每个 item 做 id/text/checked/isPromoted 的容错转换；
callout / quote / divider：遇到字符串或空对象时转成 {variant:'info',text:''} / {text:'',source:''} / {}；
image/image_gallery：缺 url / items 时返回空但结构完整的对象，并允许 UI 渲染“未选择图片”的占位。
BlockRenderer & BlockList 扩展计划（渲染/编辑器栈）

设计 BlockRenderer 的新结构，不修改现有 paragraph 逻辑：
在 BlockRenderer 内为 todo_list / callout / quote / divider / image / image_gallery 分别添加 case，统一路由到 TodoListDisplay/Editor、CalloutDisplay/Editor、QuoteDisplay/Editor、DividerDisplay/Editor、ImageDisplay/Editor、ImageGalleryDisplay/Editor。
保持 UnsupportedBlock 仍是默认分支，以防后端提前发出新 kind。
规划每个 kind 的 Display 组件行为（符合 Plan_83 + VISUAL_RULES）：
Todo：多行 checkbox 列表，左侧勾选框，右侧文本行；block toolbar 区可显示 “Todo” 标签；勾选变化直接触发上层 onSave(JSON.stringify(newContent))；
Callout：左侧彩色竖条+图标（info/warning/danger/success），右侧正文；整体缩进并在 hover/编辑态强调；
Quote：左侧引号/竖线，主体 text，底部右对齐 — source；
Divider：一条线，依据 style 使用实线/虚线；
Image：受限宽度图片 + 下方 caption，点击图片可触发轻量预览（可以将 Modal/Lightbox 设计为后续子任务）；
ImageGallery：strip 模式为横向缩略图条、grid 模式为固定列网格，均支持点击放大。
规划对应 Editor 组件的交互边界：
TodoListEditor：checkbox + 文本 input + 星标按钮 + hover 删除 icon；支持“+ 新增待办”行和在最后一行回车添加新项，退出编辑（blur/Esc/切换 block）时统一调用 onChangeContent 再由外层执行 PATCH。
CalloutEditor：variant 选择控件（segmented control 或下拉）+ textarea，保留 Ctrl/Cmd+S / blur 保存、Esc 取消逻辑；
QuoteEditor：textarea（text）+ 单行 input（source），同样遵守 Plan_80/82 的保存键盘约定；
DividerEditor：几乎无输入，仅提供一个 style 切换（按钮或下拉），其余交互放在 block toolbar 的 “更多” 菜单中；
ImageEditor：URL 输入 + “选择图片/上传” 按钮（最小版可以先只实现 URL），外带 caption 输入；保存时写回完整 ImageBlockContent；
ImageGalleryEditor：layout 选择（strip/grid）、可选 maxPerRow、每个 item 的 URL+caption+删除按钮、“添加图片” CTA；排序先用“列表顺序即展示顺序”，拖拽留作后续迭代。
在 BlockList.tsx 中规划好编辑/保存接口统一性：
继续使用 editingBlockId 驱动哪个 Block 进入 editor；
对 paragraph 保持 value 字符串模型不变；
对结构化 kind，计划由各 Editor 内部维护局部 state，通过 onSave 回调传递完整 JSON 字符串给 useUpdateBlock，保证 SaveAll 仍然只是调用多个 updateBlock。
插入菜单 & Block 创建策略（Blocks Tab）

在 page.tsx（或 Blocks Tab 容器）设计插入菜单方案：
保 留现有 “+ 添加一段文字” 作为默认段落；
新增一个 dropdown / split button：“+ 插入块”，菜单项按 Plan_83 分组：基础（段落/标题/列表/编号列表）、Todo（待办列表）、标注（Callout/引用/分割线）、媒体（图片/图片组）。
设计菜单项到创建请求的映射：
所有菜单调用统一 useCreateBlock，传入：kind、book_id、content 字符串（由默认 JSON 序列化而成）；
默认 content 规划：
todo_list: {items:[{id:uuid,text:'',checked:false}]}；
callout: {variant:'info',text:''}；
quote: {text:'',source:''}；
divider: {style:'solid'}；
image: {imageId:'',url:'',caption:''}；
image_gallery: {layout:'strip',items:[]}。
规划新建后编辑态切换：创建成功后，由调用方拿到新 blockId，调用 BlockList 对外暴露的 focusBlock(blockId)（或继续沿用 setEditingBlockId）立刻进入对应 kind 的 Editor。
TODO → Book TODO Tab 软联动方案

在 frontend/src/features/todo/model/derive.ts 设计（或完善）一个纯函数：deriveBookTodosFromBlocks(blocks: BlockDto[]): { text; blockId; itemId; checked; isPromoted? }[]，只读取 todo_list kind 的 content；
在 Book Overview Tab（对应 features 或 app 路由文件）规划：
使用 Blocks 分页数据或单本 Book 的 block 列表，调用 deriveBookTodosFromBlocks 得到视图层待办；
展示 “Open TODOs / Done” 两个胶囊统计（对齐 VISUAL_RULES 的 book_workspace_todo_visual_rules）；
列出最多 N 条升级待办（isPromoted === true），点击后切换到 Blocks Tab 并滚动/聚焦到对应 block（只读与可编辑状态受 Basement/Legacy 策略约束）。
在 Blocks Tab 中规划 checkbox 和星标按钮的写入逻辑：
所有勾选/提升操作仍经由 updateBlock 更新整个 todo_list content，不引入 /todos 独立 API；
与 DDD 的 POLICY-BLOCK-TODO-EMBEDDED-MODEL / POLICY-BOOK-TODO-PROJECTION 保持一致。
RULES / ADR 更新计划
VISUAL_RULES.yaml

metadata：
更新/追加字段，例如：
block_rich_types_status: "✅ Plan83 Phase 2 - todo/callout/quote/divider/image/image_gallery 基础可视化上线 (2025-11-27)"。
新增 block_rich_types_plan83 区块（或在现有 block_* 规则后追加）：
描述每种 Plan_83 BlockKind 的视觉语言（颜色、排版、hover 行为）；
说明 Insert 菜单的分组及交互（主按钮+dropdown，并给出“插入即进入编辑态”的约定）；
对 TODO list 的显示与编辑模式做明确 UI 约束（列表布局、勾选动画、星标样式、空态/最后一行占位、“+ 新增待办”等）；
对 image / image_gallery 的缩略图尺寸、布局（strip/grid）、点击放大行为给出最小规范；
明确可访问性要求：checkbox/按钮 aria-label、键盘 Tab / Enter / Space 行为、只读态的提示。
若有现有 block_todo_visual_rules / book_workspace_todo_visual_rules：
补充说明 Plan_83 是第一版直连 UI 实现；
将 “list_todo” / “todo_list” 命名统一为 Plan_83 中的 BlockKind 文本规范。
DDD_RULES.yaml

在 POLICIES_ADDED_NOV27（或新的日期段）下：
扩充 POLICY-BLOCK-KIND-CORE-SET：
将 todo_list (or list_todo) 的 payload 结构写清楚（items 数组嵌入 Block.content）；
明确 callout/quote/divider/image/image_gallery 的字段 schema 与允许的可选字段；
规定：custom/experimental 仍作为实验型保底类型，不得覆盖上述核心枚举。
增补/细化 POLICY-BLOCK-PLAN77-V1-CONTENT 与 POLICY-BLOCK-PLAN77-DTO-ADAPTER：
标注 Plan_83 为 Phase v2：激活更多 BlockKind，但不改变 Block 聚合结构，仍为 kind + content(JSONB)；
强调：任何新增 kind 必须同步更新三份 RULES + ADR-108，且 UI 不允许直接处理未声明 schema 的 JSON。
在 TODO 相关策略（POLICY-BLOCK-TODO-EMBEDDED-MODEL, POLICY-BOOK-TODO-PROJECTION, POLICY-CHRONICLE-TODO-MAPPING 等）中补一段：
指出 Plan_83 的前端 TodoListEditor / TodoListDisplay 是对嵌入模型的首个正式消费实现；
重申禁止引入 /books/{id}/todos 独立写端点，写操作必须通过 BlockUseCase。
HEXAGONAL_RULES.yaml

metadata：
新增/更新 Plan_83 状态，例如：block_editor_plan83_status: "Plan83 - multi-kind BlockRenderer (todo/callout/quote/divider/image/gallery) wiring in progress"。
新增 block_renderer_plan83_adapter 区块（可紧挨 block_renderer_plan77_adapter）：
指定作用范围：types.ts / api.ts / BlockRenderer.tsx / BlockList.tsx；
定义端口/适配器责任：
API 适配器负责 type ↔ kind 映射与 JSON 解析；
React Query hooks 继续暴露 list/paginated/create/update 等端口，不为新 kind 新增专用路由；
BlockRenderer 作为 UI Adapter 的入口，只消费 BlockDto，不直接发 HTTP。
确认 TODO 相关的 hex 规则：
deriveBookTodosFromBlocks 属于前端 query/derive 层；
未来若增加 ITodoProjectionQueryPort，返回值形态与该 helper 保持兼容。
如有必要，为 block_todo_visual_rules 和 book_workspace_todo_visual_rules 在 HEX 文件中增加一段 todo_projection_strategy 说明：
什么时候前端本地聚合，什么时候可以切换到服务端投影；
明确不改变 Domain 聚合边界。
ADR‑108 Plan77 Roadmap 更新

在“Phased rollout roadmap”部分追加 Plan_83 作为 Phase v2：
标注“Plan_83_BlockAdditions” 作为 v2 阶段：在 v1 Paragraph-only 基础上扩展 todo_list, callout, quote, divider, image, image_gallery；
总结：
DTO/BlockKind 已在 v1 完成抽象，现在只是在现有 contract 基础上填入更多实现；
UI 采用 BlockRenderer switch + kind-specific Display/Editor 组合，仍然遵守 Plan_80/82 的 inline editing / SaveAll 约束；
后端仍停留在 kind + content(JSONB) 模式，不新增表。
在 “Consequences” 或新增小节中说明：
Phase v2 不破坏旧段落数据；
除非 RULES 被同步更新并实现新的 case，否则任何新增 kind 都应先走 UnsupportedBlock 占位。
在“References”中追加：
Plan_83 文档路径 assets/docs/QuickLog/.../Plan_83_BlockAdditions.md；
相关 VISUAL/HEX/DDD 规则 section 名称（block_rich_types_plan83, POLICY-BLOCK-KIND-CORE-SET 更新部分、block_renderer_plan83_adapter 等）。
风险 & 待决问题
旧数据兼容

旧 Block 可能仍然以“纯字符串 content” 或非标准 JSON 存储：
若解析过于严格会导致 UI 报错；
计划通过前端 parseBlockContent 的“容错+默认值策略”消化旧数据，并在 RULES 中标注这点。
后端校验力度选择

若后端对新 kind 的 JSON 结构做强校验，可能阻塞当前 UI 发布节奏；
建议在 Phase_83 初期将后端校验定义为“建议性/宽松校验”，主逻辑留在适配层，后续再通过迁移+更严格规则收紧。
媒体集成范围

Image / ImageGallery 若直接绑定 Media 模块的「选择/上传」全功能，容易在单次迭代中膨胀；
建议 Phase_83 只实现 URL+轻量预览，Media 选择器以一个独立的后续 Plan + ADR 处理。
TODO 性能与分页

在 blocks 数量较大时，完全前端聚合 TODO 可能有性能问题；
当前按照 RULES 采用“分页 Blocks + 本地聚合”策略并在文档里留下 ITodoProjectionQueryPort 作为未来扩展点。
类型切换与内容迁移

Plan_83 明确“类型切换（段落→Todo 等）暂不做”，否则需要复杂的内容迁移与语义规则；
若业务后续提需求，需要单独在 ADR 和 RULES 中为“跨 kind 转换”定义规则（可引入转换 UseCase 或前端提示“不可逆操作”）。
（5）中文计划书小结
整体思路：

以 Plan_77 打好的 BlockKind/BlockRenderer 基础为支点，在不改 schema 的前提下，通过 DTO + UI 渲染器扩展六种新 BlockKind；
所有行为（编辑、保存、插入、TODO 联动）都基于现有 CreateBlock/UpdateBlock 端点和 inline 编辑流，不新增额外后端路由；
三份 RULES（VISUAL/DDD/HEX）+ ADR-108 负责把这些约定固化下来，后续每次扩展 BlockKind 都遵守同一套路。
你或后续代理可以按上面的步骤实施具体代码和 YAML 变更：

先核对/补齐 BlockKind 与各 Content 类型定义；
扩展 parseBlockContent 与 API 适配层，保证前端拿到结构化 content；
在 BlockRenderer 中按 kind 拆分 Display/Editor，实现 todo/callout/quote/divider/image/image_gallery 的最小版本；
在 Blocks Tab 中接入插入菜单与默认 content；
在 Overview Tab 中用 derive 函数做 TODO 视图聚合；
最后同步更新三份 RULES 和 ADR-108，让 Plan_83 正式成为 Block 系统的 Phase v2 规划与实现依据。