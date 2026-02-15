你现在这个「评分构成列表」内容非常丰富，但信息密度又偏高，确实会给人一种：

行数太多

层级不够清晰

视觉疲劳

即使 +5、+10 看得懂，但不够“有结构感”

这不是内容的问题，是可视化分组方式的问题。

现在我们来一起找最佳解法。

🟩 高级方案（强烈推荐）：分组折叠 + 分数组块

做一个真正的「评分构成卡片」：

🧩 评分构成卡片（Score Breakdown）

格式类似这样：

结构（Structure） · 30 分

已填写标题（+5）

摘要达到 40 字（+5）

至少 1 标签（+5）

自定义封面图（+5）

Block ≥ 10（+10）

活跃（Activity） · 20 分

最近编辑（+10）

TODO 清理卫生（+10）

质量（Quality） · 6 分

大纲接近完整（+6）

结构任务（Milestones） · 15 分

摘要扩写到 120 字（+5）

标签体系配置（+5）

TODO 清零（+5）

人工评分（Manual） · 5 分

人工加成（+5）

特点：
✔ 每组显示总分

超有专业感，特别像一些“学习行为评估系统 / 质量评分系统”的展示方式。

✔ 折叠/展开

用户可以手动折叠“结构任务”或“活跃”区，减少一次性信息量。

✔ 整体极其“Wordloom”

---层次清晰
---结构感强
---书卷气
---还能上下延伸，不怕以后你加更多评分项

✔ 与你顶部的成熟度、分数卡片完美一致
✔ 这套结构未来能做成「评分报告 PDF」格式（企业级审计风）

超级强。

🟦 再给你一个最有质感的 UI 结构图（纯文字草图）
┌─────────────────────────────┐
│ Score Breakdown                                     71 分
│─────────────────────────────│
│  Structure 30 分   ▼                                │
│    · 已填写标题                      +5             │
│    · 摘要不少于 40 字                 +5             │
│    · 至少 1 个标签                   +5             │
│    · 自定义封面图                   +5             │
│    · Block 数 ≥ 10                 +10             │
│                                                     │
│  Activity 20 分   ▼                                 │
│    · 最近编辑                       +10             │
│    · TODO 清理                      +10             │
│                                                     │
│  Quality 6 分   ▼                                   │
│    · 大纲接近完整                    +6              │
│                                                     │
│  Milestones 15 分   ▼                              │
│    · 摘要扩写到 120 字               +5             │
│    · 配置至少 3 标签                 +5             │
│    · 清空关键 TODO                 +5              │
│                                                     │
│  Manual 5 分   ▼                                   │
│    · 人工加成                        +5             │
└─────────────────────────────┘


这看起来就是一个完整的 Book 评分报告，专业感和美感都很强。

🧠 最后给你的建议（结论）
不建议只加标题，那太“不 Wordloom”。

你做书写软件，你的审美本身又追求「结构化、淡雅、文档智慧」。
列表需要“结构梳理”。

我最推荐的是：分组 + 每组总分 + 小折叠。

它能带来：

结构感

清晰度

专业度

扩展性

美学一致性（保持你前面所有卡片的风格）

而且你的 Maturity 模块本身是一个完整的系统，我也认为应该把“评分构成”打磨得像真正的“结构报告”，而不是只是一个 checklist。

/////////////////////////////////////////////////////////////////////////////////

好，下面这段就是可以直接贴给 Copilot 的英文说明，按我们刚才说的「高级方案：分组 + 每组总分 + 折叠」来实现。
（你只要把下面整块丢进对应文件顶部 / 新建文件里，继续跟它对话就行。）

I want to refactor the "Score Breakdown" view for a Book's Maturity page into a grouped, collapsible panel.

## Context

- Tech stack: React + TypeScript + Next.js (app router) + Tailwind (or similar utility classes).
- The current "score breakdown" is rendered as a flat list of items like:
  - Structure · Title: +5
  - Structure · Summary: +5
  - Activity · Recent edits: +10
  - ...
- Data for these items already exists from the maturity module (either as a flat list or can be derived from it). I don't want to change the maturity scoring algorithm right now; this is **only a UI / view-layer refactor**.

## Goal

Create a new **ScoreBreakdownPanel** that:

1. Groups score items by category (e.g. Structure, Activity, Quality, Milestones, Manual).
2. Shows a **group header row** with:
   - group name (e.g. "Structure"),
   - the total score contributed by this group (e.g. "30 分"),
   - an expand/collapse toggle.
3. Shows a **collapsible list of items** inside each group:
   - Each item has:
     - an icon (optional),
     - a short label,
     - a secondary description line (optional),
     - the score contribution (e.g. "+5") aligned to the right.
4. Each group can be individually expanded or collapsed.
   - By default, expand the first 1–2 groups (e.g. Structure and Activity) and collapse the rest.
5. The overall look should be calm, structured, and consistent with the existing Wordloom maturity cards:
   - light background card,
   - subtle dividers between groups,
   - no heavy borders,
   - text hierarchy: group title > item label > description.

## Data model

Introduce a small, view-layer-only model in the frontend:

```ts
// A single breakdown item inside a group
export interface ScoreBreakdownItem {
  id: string;
  label: string;          // e.g. "已填写标题"
  description?: string;   // e.g. "结构：已填写标题"
  points: number;         // e.g. 5
  icon?: React.ReactNode; // optional, can be null for now
}

// A group of breakdown items, e.g. "Structure", "Activity"
export interface ScoreBreakdownGroup {
  id: string;             // "structure" | "activity" | ...
  title: string;          // e.g. "结构（Structure）"
  totalPoints: number;    // sum of points of this group's items
  items: ScoreBreakdownItem[];
}


The ScoreBreakdownPanel component should accept a prop:

interface ScoreBreakdownPanelProps {
  groups: ScoreBreakdownGroup[];
}


The component itself should not fetch data; it only renders what it receives.
Mapping from the existing maturity score data into ScoreBreakdownGroup[] can be done in the parent container.

Example grouping (for reference)

Use this grouping as a reference when mapping existing items:

Structure (结构)

标题已填写 +5

摘要不少于 40 字 +5

至少 1 个标签 +5

已配置封面图 +5

Block 数 ≥ 10 +10

Activity (活跃)

最近 30 天有编辑 +10

TODO 卫生清理完毕 +10

Quality (质量)

大纲结构接近完整 +6

Milestones (结构任务 / Milestones)

摘要扩写到 120 字 +5

配置至少 3 个标签 +5

清空关键 TODO +5

Manual (人工评估)

人工加成 +5

You don't need to hardcode these labels in the component; they should come from the data passed in.

UI / layout details
Component structure

Rough structure (pseudo-React):

export const ScoreBreakdownPanel: React.FC<ScoreBreakdownPanelProps> = ({ groups }) => {
  // local state: which groups are expanded
  // default: expand first 1–2 groups
  return (
    <section className="rounded-xl bg-slate-50 px-6 py-4">
      <header className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">评分构成</h3>
        {/* Optional: total score or subtitle, can be passed as prop later */}
      </header>

      <div className="space-y-2">
        {groups.map(group => (
          <GroupSection key={group.id} group={group} />
        ))}
      </div>
    </section>
  );
};


GroupSection:

interface GroupSectionProps {
  group: ScoreBreakdownGroup;
}

const GroupSection: React.FC<GroupSectionProps> = ({ group }) => {
  const [open, setOpen] = useState<boolean>(/* default based on index or prop */);

  return (
    <div className="rounded-lg bg-white shadow-sm shadow-slate-100">
      {/* group header */}
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-baseline gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {group.title}
          </span>
          <span className="text-xs text-slate-400">
            {group.items.length} 项
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-800">
            {group.totalPoints} 分
          </span>
          <ChevronDownIcon
            className={cn(
              "h-4 w-4 text-slate-400 transition-transform",
              open && "rotate-180"
            )}
          />
        </div>
      </button>

      {/* item list */}
      {open && (
        <ul className="border-t border-slate-100 px-4 py-2">
          {group.items.map(item => (
            <li
              key={item.id}
              className="flex items-start justify-between py-2 text-sm"
            >
              <div className="flex items-start gap-2">
                {item.icon && (
                  <span className="mt-0.5 text-slate-400">
                    {item.icon}
                  </span>
                )}
                <div>
                  <div className="text-slate-800">{item.label}</div>
                  {item.description && (
                    <div className="text-xs text-slate-400">
                      {item.description}
                    </div>
                  )}
                </div>
              </div>
              <div className="ml-4 text-xs font-semibold text-slate-600">
                {item.points > 0 ? `+${item.points}` : item.points}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};


Feel free to adjust spacing, font sizes and colors to match the existing maturity overview cards.
The main goals are:

groups look like small cards,

inner list is easy to scan,

points are always aligned to the right,

expand/collapse is smooth and unobtrusive.

Integration

Replace the current flat "评分构成" list with this new ScoreBreakdownPanel.

The parent container that already knows the detailed score items should:

Map each item into a ScoreBreakdownItem.

Group them by category into ScoreBreakdownGroup[].

Compute totalPoints per group.

Pass the array into <ScoreBreakdownPanel groups={groups} />.

No changes are needed to the domain logic of maturity scoring; this is purely a view-layer refactor with grouping + collapsible UI.

Please implement this component and wire it into the existing Book Maturity page.


---

你可以先把这段丢给 Copilot，让它在你当前 maturity 页面里生成 `ScoreBreakdownPanel` 组件；
如果它生成的目录/文件名不合你意，再让它按你的项目结构重排就行。
::contentReference[oaicite:0]{index=0}