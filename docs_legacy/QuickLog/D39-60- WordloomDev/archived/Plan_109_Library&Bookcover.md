先确认下目标，再给你一个贴近现状的实现计划。

下面是按照当前 Wordloom 代码结构整理好的中文计划（不含具体实现代码，只说要改哪些文件、做什么事）：

Plan: Library 主题色选择与应用
在“编辑书库”表单中增加一个明确的“主题色”输入区，把值通过现有的 Library API 保存到 libraries.theme_color，然后在展示该书库下的书籍时，把这个主题色作为封面配色的 seed，替代随机颜色或不稳定的推导逻辑。

Steps
在 LibraryForm 中增加主题色表单字段与状态

修改 LibraryForm.tsx：
增加本地状态 themeColor，初始化使用 initialValues?.theme_color ?? ''。
在 onSubmit 组装 payload 时，加入 theme_color: themeColor.trim() || undefined，避免存入空字符串。
在现有表单 UI 中（名字、简介下面、标签上面），插入一块“选取主题色”区域：
label 文案："主题色（可选）" 或 "选取主题色"。
一个文本输入（可以是 type="text"），placeholder："#3B82F6 或留空自动"。
可选再加一个 type="color" 的小色块按钮，同步更新 themeColor，用于直观选色。
简单前端校验：如果非空且不符合 #RGB / #RRGGBB 正则，则在 helper 文本中提示：“请输入合法的十六进制颜色值，例如 #3B82F6（可以留空）”。
确认并打通 Library 类型与 API 中的 theme_color

检查并（如必要）更新 types.ts：
确认 LibraryDto / CreateLibraryRequest / UpdateLibraryRequest 中都有可选字段 theme_color?: string | null。
检查调用 LibraryForm 的容器组件（例如 page.tsx 或对应 feature 组件）：
在把后端的 LibraryDto 映射为 initialValues 时，确保把 dto.theme_color 传给 LibraryForm。
在处理提交结果时（创建/更新），保证没有丢弃 theme_color，例如直接使用 typed request 对象：mutate({ ...values })。
若有专门的 API 封装文件（如 frontend/src/entities/library/api.ts），确认 useCreateLibraryMutation / useUpdateLibraryMutation 的请求体包含 theme_color 字段，不进行手工 omit。
在“编辑书库”页面中集成新的主题色字段

打开 page.tsx（或该路由对应组件）：
确认 LibraryForm 的 initialValues 中包含 theme_color: library.theme_color ?? ''。
页面说明中可加一句简短说明：“主题色会用于该书库下书籍封面的默认配色。”
对于“新建书库”入口页面（可能在 page.tsx 或 LibraryMainWidget）：
创建弹窗 / 抽屉时，同样使用带 theme_color 的 LibraryForm，默认值为空即可。
从 Library 到 Book：在数据层把 theme_color 传给书籍视图

找出展示“某书库下的书”的页面，例如：
page.tsx 中的书籍列表区域，或
frontend/src/widgets/book/main-widget/* / BookshelfBooksSection.tsx 等。
在这些页面的数据加载逻辑中（通常会同时拿到 library 和 books）：
拿到当前库对象的 theme_color。
在渲染书卡组件时，增加一个新的 prop（例如 libraryThemeColor）传下去：
给 BookPreviewCard / BookRowCard / Book3D 或封面占位符组件传入 libraryThemeColor={library.theme_color}。
如果 Book 的 DTO 自身也已经带有 library 子对象或 library_theme_color，则优先直接从 Book 里面读；如果目前没有，就通过上述“页面层 → 书卡组件 props”的方式传。
在封面/主题计算逻辑中使用库主题色，而不是随机色

打开封面和颜色相关的工具，例如：
bookVisuals.ts
coverPlaceholder.ts / coverPlaceholder.tsx
与“主题 seed”有关的 helper（你之前已经有用 librarySeed 控制 placeholder 的逻辑）。
在这些函数的参数中新增可选参数 libraryThemeColor?: string | null（或复用已有 librarySeed）：
如果传入了合法 libraryThemeColor，则：
直接用这个颜色作为主色，或
把它转成 seed，用来选择/生成一组固定配色。
如果未传入（旧数据、未设置主题色），保持现有的随机 / 基于 id 的逻辑不变。
修改 Book* 组件内部调用这些工具函数的位置：
如果 props 中存在 libraryThemeColor，则把它传给封面主题函数。
没有则不传，维持原有行为，保证向后兼容。
Further Considerations
UI 体验与一致性
建议只加一个简洁的文本输入 + 小色块预览（可选 color input），避免引入体积大的第三方 ColorPicker；颜色文案和 helper 文案尽量与现有 ThemeMenu 等地方的语气统一。
兼容旧库与错误输入
允许 theme_color 为空；后端/前端都把“空或非法”视为“未设置”，自动退回原来的书封配色逻辑，避免打断已有数据。
后续可选增强
将常用品牌色或一组系统推荐色（比如一行小圆点）放在主题色输入下方，点击即可填入，有利于保持色彩体系统一，也方便用户选色。