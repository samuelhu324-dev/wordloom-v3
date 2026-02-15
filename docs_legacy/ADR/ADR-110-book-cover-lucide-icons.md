# ADR-110: Book Cover Lucide Icons

- Status: Accepted (Nov 28, 2025)
- Deciders: Wordloom Core Team
- Context: Plan_88_BookCoverLucide.md, Seeds-to-Stable visual polish initiative
- Related: ADR-092 (Book maturity segmentation), ADR-100 (Book gallery strip), ADR-101 (Book view modes), ADR-102 (Book tag badge pipeline), DDD_RULES `POLICY-BOOK-COVER-ICON-LUCIDE`, HEXAGONAL_RULES `book_cover_icon_contract`, VISUAL_RULES `book_cover_icon_visual_rules` & `book_cover_icon_picker_v1`

## Problem

Book cards目前仅通过首字母 + 阶段 badge 传达信息：

- 中文书名 fallback 成为统一的 `书` 字样，缺少区分度。
- 大量英文首字母重复，展柜 strip 视觉疲劳，用户难以在几十本书中快速定位“灵感本 / 审计本 / 研究本”。
- 允许用户从 Lucide 里任意挑选会导致“图标筛选器”问题：列表失焦、100+ icon 难以治理。

需要一种有限、可治理的封面图标机制，让 Book 可以表达“主题/气质”，又不破坏现有的成熟度/标签策略。

## Decision

1. **Domain 增加 `cover_icon` 可选字段**：Book 聚合持有 `Optional[str]`，仅存储 Lucide icon 名称；Domain 维持 ≤64 字符 + ASCII 校验，不维护枚举列表。
2. **端口合同扩展**：`UpdateBookRequest` / `BookResponse` / `BookDetailResponse` / 列表分页 DTO 均包含 `cover_icon?: string | null`。`null` 表示清除选择，缺省表示保持原值。
3. **前端提供受控白名单**：Plan88 定义 4 组（通用 / 天空 / 学习 / 财法）共 16–24 个 Lucide icon。UI 只渲染这套按钮，不提供搜索或自由输入。
4. **BookEditDialog 新增 “封面图标” Popover**：在书名下方展示当前图标 + “更换”按钮，弹框左侧 tab，右侧一次性呈现所有 icon。选择后与 title/summary/tag_ids 一起发送单次 PATCH。
5. **默认策略保持**：`cover_icon` 为空时仍按现有规则渲染：英文书名 → 首字母；非拉丁 → `book-open`。阶段 badge（Seed/Growing/Stable/Legacy）与 ribbon（tag/maturity）保持独立。

## Consequences

- Positive: 书卡主题更鲜明，中文书名也能快速建立视觉记忆；所有前端入口共用一套 icon 选择器，体验一致。
- Positive: 保持单 PATCH 原则，仍然只依赖 Book 用例，不需要跨 bounded context 协调。
- Negative: 需要维护一份 icon 白名单及中英文标签；当想扩展 icon 数量时需同步规则与 ADR。
- Negative: 需要一次数据库迁移（`books.cover_icon`），并补充 API 合同与测试用例。

## Rationale

- 限制在 4 组 16–24 个 icon 可避免“玩图标”分散注意力，同时足够覆盖知识库 / Mood / 学习 / 严肃业务等常见题材。
- 使用 Lucide 可直接复用前端现有 icon 包，无需自定义 SVG 资产。
- 保持 Domain 只存储字符串，配合静态白名单，能够在不改迁移的情况下快速增删 icon，且不会让后端对 UI 细节负责。
- 默认首字母策略被保留，确保老数据或未来批量导入无需立即选 icon。

## Implementation Notes

1. **数据库/Domain**：新增 migration `018_add_book_cover_icon.sql`（VARCHAR(64) NULL），更新 ORM、Domain Entity、Repository。
2. **UseCase / Router**：`UpdateBookUseCase` 接受 `cover_icon`，Router PATCH DTO 更新；所有 Book 响应序列化 `cover_icon`（缺省 → null）。
3. **Frontend 类型**：`BookDto` / `Book` entity / `useUpdateBook` payload 增加 `coverIcon`；mapper 负责 snake/camel 映射。
4. **Cover 组件**：将封面中心 render helper 抽象为 `renderCoverIcon({coverIcon, title})`，内部按“icon → letter → book-open”顺序 fallback。
5. **Icon Picker**：在 `frontend/src/features/book/ui/BookEditDialog.tsx` 引入新的 `CoverIconPicker` 子组件 + 配置文件 `coverIconsConfig.ts`（包含 tab → icon 列表 + 文案）。
6. **Validation**：前端和后端共同验证：若传入非白名单 icon，server 返回 422；UI 应限制按钮避免无效值。

## Verification

- `pytest backend/api/app/tests/test_books_endpoint.py -k cover_icon`：覆盖设置/清空 cover_icon，并检查响应字段。
- `GET /api/v1/books` / `/books/{id}` 返回体包含 `cover_icon`，展示层根据字段切换 icon/letter。
- BookEditDialog E2E：选择 icon → PATCH → 书卡即时展示 Lucide icon；重开 dialog 仍显示该 icon；点击“恢复默认”→ 首字母策略生效。

## Future Work

- 后续可选地把 icon 白名单提取为共享 JSON，供后端做更严格校验或分析用户偏好。
- 允许按 library/团队自定义 icon 集合时，需要新的配置服务 + ADR，当前版本保持全局固定。
- 结合封面背景色（cover gradient）做自动对比度调节，防止浅色 icon 在淡色封面上不可见。
