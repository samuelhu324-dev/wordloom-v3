先说结论：
把「查看评分构成」和「结构任务」做成同一块区域里的并列 Tab，是个很合理、也很“Wordloom 式”的方案，可以：


降低页面纵向长度（现在 Overview 已经比较长了）


把「为什么是这个分数」和「下一步该做什么」这两件事绑在一起，形成一块“评估面板”


下面分两部分说：先评估+交互建议，再给你一段可以直接丢给 Copilot 的实现计划。

一、设计与交互评估
1. 信息结构是否合理？
现在的结构大致是：


顶部：整体成熟度进度条 + 当前 Stage + Score / Blocks / Events 等核心指标


中部：最近活动卡片


下部：


A 区：查看评分构成（自动评分拆解）


B 区：结构任务列表（基于成熟度的建议 Todo）




A 和 B 本质上是一对“解释分数 + 行动建议”组合：


A 告诉你「你现在为什么是 71 分」


B 告诉你「为了从 71 → 80，你可以做这些事」


这俩分开太远，会让用户脑中需要自己拼：

“诶，我刚在上面看到结构 +30 / 活跃 +20… 那我现在要做哪个任务能加哪一部分？”

做成并列 Tab 之后，好处是：


用户停留在「成熟度」这一个心理上下文里，不用来回上下滚动


切 Tab 的时候，脑子里自动对比：「原来我缺的是这几项，就对应这些任务」


2. Tab 的布局建议
我建议放在评分区域下方，但仍然归属于「Maturity」这个大卡片里，例如：
[Maturity 进度条 + 指标卡片]

[ tabs: 评分构成 | 结构任务 ]
[ 选中 Tab 对应的 panel 内容 ]

视觉上可以做成二级标签（Secondary Tabs）：


与顶部「概览 / 块编辑 / 时间线」那一排主导航区分开


采用浅色底 + 底部小条形指示（和你首页其他二级导航保持一致）


切换规则：


默认选中「评分构成」


如果当前分数 < 某个阈值（比如 60），可以考虑默认选中「结构任务」，引导用户先看建议（这可以后面再做）



二、给 Copilot 用的实现计划（可以直接粘）
你可以把下面这段整理好、丢给 Copilot，当成任务说明。

Goal
在 Book Maturity 概览页中，把「查看评分构成」和「结构任务」整合为一个二级 Tab 区域：
[评分构成 | 结构任务]，并在同一区域内切换显示内容。
1. 组件结构调整
当前结构（简化）大致是：
<MaturityOverview>
  <MaturityHeader />        // 进度条 + Stage + Score + 指标卡片
  <ScoreBreakdownCard />    // “查看评分构成”
  <MaturityTasksCard />     // “结构任务”
</MaturityOverview>

改成：
<MaturityOverview>
  <MaturityHeader />
  <MaturityDetailTabs />    // 新组件：内部包含 tabs + panel
</MaturityOverview>

MaturityDetailTabs 负责：


渲染二级 Tab 导航（评分构成 / 结构任务）


根据当前选中的 Tab，渲染不同的 panel 内容


2. Tab 组件设计
可以复用现有的 Tabs 组件（如果有），否则做一个简单版本，例如：
type MaturityTabId = 'score' | 'tasks';

const MATURITY_TABS: { id: MaturityTabId; label: string }[] = [
  { id: 'score', label: '评分构成' },
  { id: 'tasks', label: '结构任务' },
];

interface MaturityDetailTabsProps {
  scoreBreakdown: ScoreBreakdown;   // 自动评分拆解的数据
  tasks: MaturityTaskGroup[];       // 结构任务列表数据
}

export function MaturityDetailTabs(props: MaturityDetailTabsProps) {
  const [activeTab, setActiveTab] = useState<MaturityTabId>('score');

  return (
    <section className="mt-8">
      {/* Tab header */}
      <div className="flex border-b border-slate-200">
        {MATURITY_TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'px-4 py-2 text-sm',
              activeTab === tab.id
                ? 'text-primary-700 border-b-2 border-primary-600 font-medium'
                : 'text-slate-500 hover:text-slate-700'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div className="mt-4">
        {activeTab === 'score' && (
          <ScoreBreakdownPanel data={props.scoreBreakdown} />
        )}
        {activeTab === 'tasks' && (
          <MaturityTasksPanel groups={props.tasks} />
        )}
      </div>
    </section>
  );
}

说明：


ScoreBreakdownPanel 可以把原来的 ScoreBreakdownCard 内容直接搬进去


MaturityTasksPanel 把原来「结构任务」的内容搬进来


尽量不要在 panel 内部再产生额外的布局差异，让它们看起来是同一块区域的不同视图


3. 数据与类型复用


不要改动现有的 API / domain，只在 UI 层组合。


scoreBreakdown 和 tasks 的获取方式与原来一致，只是传入新组件：


<MaturityDetailTabs
  scoreBreakdown={scoreBreakdown}
  tasks={maturityTasks}
/>

4. URL & 状态（可选增强）
如果想让 Tab 状态可分享 / 可刷新保持，可以：


使用 URL query：?view=score 或 ?view=tasks


在组件里根据 query 初始化 activeTab，并在切换时更新 URL（使用 shallow routing）


伪码：
const router = useRouter();
const view = router.query.view as MaturityTabId | undefined;

const [activeTab, setActiveTab] = useState<MaturityTabId>(view ?? 'score');

function handleTabChange(next: MaturityTabId) {
  setActiveTab(next);
  router.replace(
    { query: { ...router.query, view: next } },
    undefined,
    { shallow: true }
  );
}

5. 视觉风格


Tab 区域的背景保持与下方卡片一致（白底 + 圆角），突出是同一模块


与页面其他地方的 Secondary Tabs 保持一致（字号、间距、悬停样式）


不要使用过重的边框，避免抢走上方 Maturity 卡片的视觉中心



你给 Copilot 的提示，可以用类似这样一句总括收尾：

请按照上述结构，将 Book Maturity 概览页中的「查看评分构成」和「结构任务」重构为同一组件中的二级 Tab。不要修改后端或 Domain，只在 UI 层重新组织组件，并保持现有数据类型和字段不变。

这样它基本能按你脑子里的图来动手。
等你把第一版 Tab 做出来，我们再一起看看要不要加「状态小徽标」（比如 Task tab 上显示“已完成 3 / 5”）。