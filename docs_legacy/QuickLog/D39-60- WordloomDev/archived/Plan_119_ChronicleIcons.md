可以，两种都要很合理：同一套数据，两种视图皮肤。给 Copilot 的时候就明确成「时间线视图模式规范」。

下面这段你可以直接丢进 CHRONICLE_TIMELINE_SPEC.md 或 VISUAL_RULES 的某个章节。

Chronicle 时间线视图模式规范（给 Copilot 看）
1. 总目标

Chronicle 是 Wordloom 的「事件时间线」。
同一批事件数据，提供两种视图模式：

timeline：时间轴点视图 —— 左侧竖线 + 小圆点，突出时间顺序，视觉克制。

grouped：按事件类型分组视图 —— 每组有标题 + 图标，下面是文本列表，适合浏览同类事件。

它们只是在前端用不同组件渲染，数据模型和 API 完全一致。

2. 事件数据模型（后端 / UseCase 不动）

前端拿到的事件（示意）：

type ChronicleEventType =
  | "maturity_recalculated"
  | "block_created"
  | "block_deleted"
  | "book_archived"
  | "ops_bonus_adjusted"
  | "system_warning"
  | "system_error"
  // … 后续可扩展

interface ChronicleEvent {
  id: string;
  type: ChronicleEventType;
  createdAt: string; // ISO 时间
  title: string;     // e.g. "成熟度重算"
  summary: string;   // e.g. "Score 76 → 71 Δ-5 · 阶段 Stable · block_created"
  details?: string;  // 可选，hover 或展开时显示
  tags?: string[];   // e.g. ["Stable", "manual_refresh"]
}


前端用一个 hook 取数据：

const { events, isLoading, error } = useChronicleEvents({ bookId, limit, cursor });


注意：任何视图切换都只在前端操作 events 数组，不触碰 UseCase 逻辑。

3. 视图模式枚举 & 切换
type ChronicleViewMode = "timeline" | "grouped";


顶部右上角加一个 SegmentedControl / Tabs：

「时间线」 / 「按类型分组」

视图模式可以：

临时存到 URL query（例如 ?view=timeline）

或存到 localStorage（用户偏好）

示例：

function ChronicleView(props: { events: ChronicleEvent[] }) {
  const [viewMode, setViewMode] = useChronicleViewMode(); // 封装 localStorage + URL

  return (
    <div>
      <ChronicleViewModeSwitch value={viewMode} onChange={setViewMode} />
      {viewMode === "timeline" ? (
        <ChronicleTimelineView events={props.events} />
      ) : (
        <ChronicleGroupedView events={props.events} />
      )}
    </div>
  );
}

4. 视图模式 A：时间轴点视图（timeline）
4.1 布局

左侧：一条淡灰色竖线（时间轴主线）

每条事件左侧：小圆点（点在线上）

右侧：事件内容（title + summary + 时间）

视觉要求：

小圆点尺寸小 / 颜色克制，不要抢占主视线。

整列看上去像「一串小点 + 一列文字事件」，而不是一堆大图标。

4.2 颜色 / 样式映射（按事件类型）

用颜色或填充方式区分事件类型：

function getTimelineDotStyle(type: ChronicleEventType) {
  switch (type) {
    case "maturity_recalculated":
      return { variant: "filled", color: "blue" };
    case "block_created":
    case "block_deleted":
      return { variant: "outlined", color: "gray" };
    case "system_warning":
      return { variant: "filled", color: "orange" };
    case "system_error":
      return { variant: "filled", color: "red" };
    default:
      return { variant: "outlined", color: "gray" };
  }
}


variant=filled：实心点

variant=outlined：空心点

颜色用中性色阶（不要太亮）。

4.3 文本排版

第一行：事件标题（如「成熟度重算」），稍微加粗。

第二行：summary，如 Score 76 → 71 Δ-5 · 阶段 Stable · block_created。

右侧末端：时间（如「13 小时前」），用浅色小字号。

4.4 交互细节

鼠标 hover 小圆点或事件条目：可以高亮这条事件（点 + 文本一起变深）。

可选：点击事件展开更多 details（如果有）。

5. 视图模式 B：按事件类型分组（grouped）
5.1 分组规则

前端按 event.type 对 events 分组：

const groups = groupBy(events, e => e.type);


分组顺序可以是：

把所有 type 映射为一个有序数组（优先展示成熟度相关、Block 相关）；

或按最近事件时间排序。

定义一个 type → 分组标题 / 图标 的 map：

interface ChronicleGroupMeta {
  title: string;
  icon: ReactNode; // 仅用于组标题
}

const GROUP_META: Record<ChronicleEventType, ChronicleGroupMeta> = {
  maturity_recalculated: { title: "成熟度重算", icon: <RefreshIcon /> },
  block_created: { title: "Block 相关", icon: <BlockIcon /> },
  block_deleted: { title: "Block 相关", icon: <BlockIcon /> },
  ops_bonus_adjusted: { title: "运维加成调整", icon: <SettingsIcon /> },
  system_warning: { title: "系统告警", icon: <WarningIcon /> },
  system_error: { title: "系统错误", icon: <ErrorIcon /> },
};


同一组可以包含多个 type，例如把 block_created / block_deleted 都归到「Block 相关」。

5.2 布局

每个分组长这样：

[组图标] 组标题
----------------------------------
  · 事件1标题 / 概要 …… 时间
  · 事件2标题 / 概要 …… 时间
  · …


要求：

图标只出现在组标题行，下面每条事件不要再画图标。

组标题稍微加大字号，和事件行之间有一点间距。

多个分组之间，用 16–24px 的竖向间隔。

5.3 事件行排版

与时间轴视图类似，只是去掉左侧点：

事件标题（加粗）

summary + 时间（同一行 or 换行都可）

可选：在 summary 里高亮 score 变化部分（使用强调色）：

例如 Score 76 → 71 Δ-5 用蓝色 or 红色。

6. 两种视图共享的样式 / 行为

无论哪种视图，都保持以下一致性：

文本信息一致：同一条事件在两种视图里 title/summary/time 完全相同。

点击行为一致：

点击事件条目：打开相同的详情面板（Drawer/Modal/右侧详情）。

分页 / 加载逻辑一致：

视图切换时不重复请求，使用同一批 events。

空状态：

没有事件时，展示统一的空状态组件（例如「暂无时间线事件」）。

7. 给 Copilot 的实现提示

可以在前端拆出专门的组件：

// 顶层容器，放视图切换和数据加载
function ChroniclePanel(props: { bookId: string }) {
  const { events, isLoading } = useChronicleEvents({ bookId: props.bookId });
  const [viewMode, setViewMode] = useChronicleViewMode();

  if (isLoading) return <ChronicleSkeleton />;

  return (
    <div>
      <ChronicleViewModeSwitch
        value={viewMode}
        onChange={setViewMode}
        // ["时间线", "按类型分组"]
      />
      {viewMode === "timeline" ? (
        <ChronicleTimelineView events={events} />
      ) : (
        <ChronicleGroupedView events={events} />
      )}
    </div>
  );
}


ChronicleTimelineView：

负责渲染左侧竖线 + 小圆点；

根据 getTimelineDotStyle(event.type) 渲染点的颜色/样式；

文本布局见第 4 节。

ChronicleGroupedView：

先 groupBy(type)；

按预设顺序渲染组标题（带 icon）；

组内渲染事件行，行样式与 Timeline 模式的文本部分复用。

8. VISUAL_RULES 中可以加入的一句规范
- Chronicle timeline:
  - 提供两种只读视图模式：时间轴点视图 (timeline) 与按事件类型分组视图 (grouped)。
  - 两种视图使用相同事件数据和交互行为，仅改变布局与图标使用位置：
    - timeline: 左侧为细时间轴 + 小圆点，点颜色表达事件类型，图标极度弱化。
    - grouped: 顶部为按类型分组的标题行（含图标），组内列表行不再重复图标。
  - 图标用于表达「类型」而非装饰，任何模式下都不能盖过事件文本信息。


这样 Copilot 接收到的信息是：

有两个正式的 view mode，代码层面要有 ChronicleViewMode；

timeline 用小点 + 竖线，grouped 用组标题 + 图标；

数据结构 / UseCase 不动，只写 React + 样式逻辑。

之后你要加第三种视图模式（比如「只看错误」）也可以用同一套模式扩展。