# ADR-076: Bookshelf Widget Rich Integration & Degradation Strategy

- Status: Accepted
- Date: 2025-11-20
- Author: Wordloom Core
- Related: ADR-070, ADR-071, ADR-074, ADR-069, ADR-057

## 背景 (Context)
Library 详情页需要一个“可永远呈现”的书橱管理区：在后端出现超时或 4xx/5xx 错误时仍能展示已有结构和缓存数据，避免出现空白或整块替换。此前多次迭代中，BookshelfMainWidget 遇到错误会直接 `return` 错误面板，阻断网格与创建入口。用户要求“彻底修改”，并添加网格/列表双模式、插图与说明丰富度。后端端点保持平铺 `/api/v1/bookshelves?library_id=...`，前端需要遵守独立聚合根与降级策略。

## 现状问题
1. 错误阻断：组件早期错误分支返回，隐藏操作区与已有内容。
2. 超时体验差：3s Abort 后仅显示红色错误，无缓存回退。
3. 展示单一：只有网格，卡片无封面插图，信息密度低。
4. Query Key 风险：潜在字符串拼接方式会导致后续过滤参数膨胀时缓存污染。

## 决策 (Decision)
实现一个具备“结构持久性 + 双模式 + 插图 + 缓存降级”的 BookshelfMainWidget：
- 始终渲染：错误→顶部横幅；列表区域仍保留（为空或缓存）。
- 双模式：`viewMode` 本地 state，支持 `grid` 与 `list`，不触发重新请求。
- 插图：使用名称哈希计算稳定 `coverColor` + 首字母大写，避免 SSR/C SR Hydration mismatch。
- 缓存降级：客户端 API 适配器 3s 超时后读取 localStorage（`wl_bookshelves_cache_{libraryId}`）填充。
- Query Key 规范：`['bookshelves', { filters: { libraryId } }]`，拒绝 `['bookshelves', libraryId]` 形式。
- 平铺端点：继续使用 `/bookshelves?library_id=`，禁止嵌套 URL。

## 实施 (Implementation)
前端：
1. `BookshelfDto` 新增 `coverColor`（稳定哈希 + 8 色调色板）。
2. `BookshelfCard` 重构：`media` 插图区 + `meta` 信息 + `footer` 徽章/操作；`list` 模式横向排版。
3. `BookshelfList` 支持 `viewMode` 属性，分别渲染 `.grid` 或 `.list` 布局。
4. `BookshelfMainWidget` 增加模式切换按钮（网格/列表），错误分支也传递 `viewMode`。
5. CSS：新增 list 布局样式，卡片样式支持横向。
6. 规则文件：更新 VISUAL_RULES / DDD_RULES / HEXAGONAL_RULES 增补相关条目。
7. ADR-076 创建（本文件）。

后端：
- 暂无结构性更改；保留现有平铺路由与用例。后续将添加 list_bookshelves 性能日志（单独任务）。

## 备选方案 (Alternatives)
- 使用全局 store 保存 viewMode：增加复杂度且非跨页面需求，拒绝。
- 动态请求切换 list/grid：无数据差异，浪费网络，拒绝。
- 服务端生成插图：增加后端职责与 IO，前端哈希即可满足，拒绝。

## 影响 (Consequences)
优点：
- 显著提升错误与超时场景的可用性与视觉稳定性。
- 双模式提升信息密度与阅读舒适度。
- 规则同步后，新成员易于理解聚合根与降级策略。
缺点：
- 组件样式与逻辑复杂度略增；维护需要遵守哈希稳定性。

## 风险与缓解 (Risks & Mitigation)
- Hydration mismatch：避免使用随机色；采用名称哈希 + 固定色板。
- 缓存数据陈旧：后续可加 `updated_at` 判断与灰显提示（扩展项）。
- 超时频繁：需要后端 list 性能分析（Task #25）。

## 验收标准 (Validation)
- 超时网络模拟（Chrome DevTools 3G）→ 组件显示错误横幅 + 缓存列表/空状态，无白屏。
- 切换模式 10 次：不触发额外 XHR。
- 创建成功后：列表自动刷新（React Query invalidate）。
- 规则文件含新增条目（grep RULE_BOOKSHELF_VIEW_MODES_001 等返回命中）。

## 后续 (Follow-up)
- Task: 后端 list_bookshelves 增加日志，定位 3s timeout 根因。
- Task: 书橱插图扩展支持自定义上传（需要 Media 聚合协作）。
- Task: 增加书橱排序与位置字段 UI（position）。

## 状态 (Status)
已合并并运行在分支 `refactor/infra/blue-green-v3`。
