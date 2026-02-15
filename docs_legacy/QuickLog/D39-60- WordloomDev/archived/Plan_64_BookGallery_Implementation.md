# Plan 64 · Book Gallery 改造执行方案

## 1. 背景与目标
- 现状：Bookshelf 详情页的 `BookMainWidget` 以成熟度分区 + 列表卡片为主，视觉上偏“报表”。
- 目标：按照 Plan_64，要构建“页面 → 陈列区模块 → 书架条 → 多本斜书”的三层陈列体验，让用户一眼看到“这是一排真实摆放的书”。
- 约束：
  1. 不新增后端字段或端口，全部发生在前端 UI 层；
  2. 继续复用现有 `useBooks` 数据流与成熟度统计；
  3. 与 Book Workspace (`/admin/books/{bookId}`) 的视觉语言保持一致。

## 2. 总体结构
1. **顶层容器**：`frontend/src/widgets/book/BookMainWidget.tsx`
   - 保留 breadcrumb 与 summaryBar。
   - 将“该书架的书籍 + +NEW BOOK”头部与新增陈列 strip 封装为一个独立 section。
2. **陈列区组件**：`BookshelfBooksSection`
   - 建议放在 `frontend/src/widgets/book/BookshelfBooksSection.tsx`。
   - 结构：
     ```tsx
     <section className={styles.bookshelfSection}>
       <header className={styles.bookshelfHeader}>...</header>
       <div className={styles.shelfStrip}>
         <div className={styles.shelfBoard} />
         <div className={styles.shelfBooks}>
           {books.map((book, idx) => (
             <BookDisplayCabinet key={book.id} book={book} data-index={idx} />
           ))}
         </div>
       </div>
     </section>
     ```
   - 数据来源：合并 snapshot 中的 `seed + growing + stable` 作为 active 书列表，按照 `updated_at` DESC 排序。
3. **单本斜书组件**：`BookDisplayCabinet`
   - 放在 `frontend/src/features/book/ui/BookDisplayCabinet.tsx`。
   - Props：`book`, `className?`, `onClick?`。
   - CSS 重点：
     - `.bookTilted` 使用 `transform: perspective(900px) rotateY(-18deg) rotateZ(-1deg)`；
     - `.spine` 作为书脊、`.badge` 显示状态（例如 DRAFT）；
     - `.shadow` 采用 radial-gradient 模拟贴着木板的阴影。

## 3. 详细步骤
1. **数据与状态**
   - `BookMainWidget` 新增 `const activeBooks = useMemo(() => [...seed, ...growing, ...stable], [snapshot])`。
   - strip 为空时显示灰色提示并隐藏 `shelfBoard` 阴影。
2. **UI 布局调整**
   - summaryBar 下方插入 `BookshelfBooksSection`：
     - `title` 使用“该书架的书籍”，副标题沿用 Plan_64 文案。
     - `actions` 区域放置 `+NEW BOOK` 与新建表单（点击按钮展开）。
   - 原 `BookMaturityView` 下移，成为 strip 之后的“深入分区”，保留 Seed/Growing/Stable/Legacy 的卡片内容。
3. **CSS 细节**
   - `BookshelfBooksSection.module.css`：
     - `.shelfStrip`: `padding: 32px 40px 56px; border-radius: 24px; background: radial-gradient(circle at top, #ffffff 0, #f3f4f6 40%, #e5e7eb 100%); box-shadow: 0 18px 40px rgba(15,23,42,0.12), 0 0 0 1px rgba(148,163,184,0.15); overflow-x: auto; position: relative;`。
     - `.shelfBoard`: `position: absolute; left: 32px; right: 32px; bottom: 18px; height: 14px; border-radius: 999px; background: linear-gradient(to bottom,#cbd5e1,#94a3b8); box-shadow: 0 8px 18px rgba(15,23,42,0.25), inset 0 2px 0 rgba(255,255,255,0.6);`。
     - `.shelfBooks`: `display:flex; align-items:flex-end; gap:32px; min-height:220px; padding-bottom:10px; z-index:1;`。
     - `.bookSlot`: `flex:0 0 auto; scroll-snap-align:center;`（配合 `.shelfBooks { scroll-snap-type: x mandatory; }`）。
   - `BookDisplayCabinet.module.css`：
     - `.wrapper`: `width:140px; height:200px; display:flex; flex-direction:column; align-items:center;`。
     - `.bookTilted`: `border-radius:16px; box-shadow: 0 10px 24px rgba(15,23,42,0.35), 10px 0 16px rgba(15,23,42,0.2); overflow:hidden; background:#1d4ed8; transform-origin:left center;`。
     - `.spine`: 左侧书脊，使用 `skewY(-8deg)` 和 `linear-gradient`；
     - `.badge`: `position:absolute; top:10px; right:12px; padding:4px 10px; font-size:10px; border-radius:999px; background:rgba(15,23,42,0.9); color:#f9fafb;`。
     - `.shadow`: `margin-top:6px; width:60%; height:10px; border-radius:999px; background: radial-gradient(circle at center, rgba(15,23,42,0.3), transparent 70%); filter:blur(2px);`。
4. **交互规则**
   - 点击 `BookDisplayCabinet` → `onSelectBook`，保持导航到 `/admin/books/{bookId}`。
   - `+NEW BOOK` 按钮改用 `+NEW BOOK` 文案，与书库页一致；提交成功后保持 toast + refetch。
5. **性能与响应式**
   - 阴影/渐变在 `prefers-reduced-motion` 情况下降低强度。
   - 768px 以下：strip 改为 `padding: 24px 20px 48px; gap: 20px;`，`BookDisplayCabinet` 降为 110×160 并调整 `rotateY` 角度至 -14°，避免遮挡。

## 4. 时间线与验收
1. **阶段 1**（1 天）：落地 `BookDisplayCabinet` + `BookshelfBooksSection` 组件与样式，接入 `BookMainWidget`，保留原分区。
2. **阶段 2**（0.5 天）：调整 `BookMaturityView` 与 strip 的协同、空状态与响应式行为、nth-child 角度扰动。
3. **阶段 3**（0.5 天）：视觉微调 + 无障碍校验（tab focus、aria-label），并编写 Storybook/截图供比对。
4. **验收标准**：
   - 页面加载后能看到完整 strip + 木板 + 多本斜书；
   - 点击任一本书可进入 Book 工作区；
   - Seed 为空时 strip 有明确提示且木板阴影被弱化；
   - Lint/Type-check 通过，相关单元测试（如 snapshot）更新。
