后续建议（按优先级）

后端扩展 GET /books/deleted 返回 bookshelf_exists 与 original_bookshelf_name（若尚未实现）。
增加书架选择：获取当前库书架列表 → Modal 中下拉选择（避免手动输入 ID）。
批量恢复与多选：加入选择模式与批量 API 占位。
增加 /basement/stats 端点，避免用 groups 请求推导统计。
Loading skeleton & 错误状态统一用现有设计系统组件（Spinner/Toast）。
国际化：将 “删除书籍”“删除书架”“进入回收站”“恢复” 等文案抽离到 i18n。
安全与可用性：恢复操作完成后自动刷新分组；失败重试；Modal ESC 关闭与焦点陷阱。
Retention 过期标识：DTO 添加 expired:boolean 后在 UI 上加过期角标与快速清理。
可选继续动作

我可以下一轮直接为后端端点补充 bookshelf_exists 逻辑与响应字段，然后前端消费。
或先完善前端书架选择下拉组件与批量恢复模式。

Next Steps

Extend /books/deleted to include original_bookshelf_name & bookshelf_exists.
Add /basement/stats endpoint.
Hook restore modal to fetch target shelves dynamically.