好，这个问题问得非常关键：
Block 类型已经有了，怎么在“插入 / 切换”时让它们既好用又不吵？
我给你一套可以直接写进 VISUAL_RULES + 丢给 Copilot 的方案——按：交互模式 → 菜单结构 → 实现提示 三步来。

一、交互模式：三件事要分开想


插入一个新 block（Insert）


把当前 block 改成别的类型（Transform）


高频和低频的操作入口（Quick vs More）


推荐组合是：
1）“+” 按钮插入（鼠标友好）


每个 block 的上方 / 下方中间位置有一个淡淡的 ＋ 图标（hover 才出现）。


点 ＋ → 在该位置弹出一个 Block Picker Popover（小菜单）：


前 5 个位置是最常用类型（段落、标题、项目符号、待办、图片）。


后面一个「更多…」展开全部类型。





这个是照着 Notion / Craft 那套来，用户见过，不用重新学习。

2）/ 指令插入（键盘党）


在任意段落空行输入 /，就弹出同一套 Block Picker：


继续打字会作为过滤条件，例如 /he 只剩下 Heading / Hero callout 之类。


回车或点击选中后，在当前位置插入对应 block。





这样你不用做超级复杂的全局 toolbar，
只要把 “+ 按钮” 和 “/” 调用同一个组件，维护成本很低。

3）左侧小图标用于“转换 block 类型”（Transform）


每个 block 左侧的 gutter 区有一个小 icon（段落是 ¶，标题是 H2，列表是 •…）。


点击这个 icon → 小小的类型切换菜单，只列文本相关的几种：


Paragraph / Heading1/2/3


Bulleted / Numbered / Todo


Quote / Callout




这属于「变形」而不是「新建」。



这样你就有两个清晰的动作：


想换形态 → 鼠标去点左边 icon；


想插新东西 → 点 + 或按 /。




二、Block Picker 菜单怎么排才“成熟、不花里胡哨”
建议你把菜单内的 block 类型分成 3 组：
组 A：常用（放最上面）


Paragraph（默认就用，不一定要出现在菜单里，可以灰掉）


Heading


Bulleted list


Numbered list


Todo list



这 5 个是 80% 使用场景，icon 要简单清晰。

组 B：结构 / 高亮


Callout（信息框）


Quote


Divider



这些是“整理结构 / 提示重点”的东西，数量少但很有用。

组 C：媒体 / 工程


Image


Image gallery（截图条 / 网格）


Code block


（以后再加）表格 / 自定义 custom 等



菜单里可以用小分组标题区分，比如：

常用
  [¶] 段落
  [H] 标题
  [•] 列表
  [1.] 编号列表
  [☑] 待办列表

结构
  [! ] Callout
  [“”] 引用
  [—] 分割线

媒体 & 工程
  [🖼] 图片
  [▦] 图集
  [</>] 代码块

小细节建议


显示快捷方式：在每个菜单项右侧显示提示：


# 空格 → Heading


- 空格 → Bulleted list


1. 空格 → Numbered list


[] 空格 或 - [ ] → Todo


> 空格 → Quote





这样之后你可以慢慢支持这些“行首语法”，不用一开始就全做完。


菜单宽度固定，不滚动太狠：否则 Block 一多就变成“武功秘籍目录”，用户直接放弃。



三、实现层面的套路（方便你喂 Copilot）
你可以让 Copilot 按这套结构生成一个统一配置：
type BlockCategory = 'common' | 'structure' | 'media';

interface BlockDefinition {
  kind: BlockKind;          // 'heading' | 'paragraph' | ...
  label: string;            // 显示名称
  description?: string;     // 简短说明，用在菜单小字幕
  icon: ReactNode;          // lucide 图标组件
  category: BlockCategory;
  isTransformable?: boolean; // 能不能用在“类型转换”菜单里
  createInitialData(): BlockData; // 插入时的默认内容
}

export const BLOCK_DEFINITIONS: BlockDefinition[] = [ ... ];

然后：


BlockInsertMenu 组件


接收 onSelect(kind: BlockKind)


内部按 category 分组显示 BLOCK_DEFINITIONS


被 PlusButton 和 / 指令共用




BlockTypeSwitcher 组件（左侧小图标）


只显示 isTransformable === true 的项


调用 onTransform(targetKind)，不新建 block，只改当前类型




如果之后要加新 Block 类型（比如 table），只要在 BLOCK_DEFINITIONS 里加一条，
菜单会自动出现，不用大改 UI。



四、控制“难度”的最后一句话
你现在不用一次性把所有 block 都塞进菜单里。
非常保守、安全的做法是：


第一轮菜单只放：Heading / 段落 / 三种列表 / Divider / Image


Callout、Quote、Image gallery、Code 全部当做“以后版本再打开的开关”，
等你主流程（插入 + 删除 + 基本编辑）稳定了再逐个加。


这样即使你只把 “+ 按钮 + / 菜单 + 左侧类型切换” 这一套做出来，
已经比大部分课堂 demo 编辑器高一个维度了，而且结构是以后能扩展的。
你只要把上面这堆需求整理成几条英文注释（或直接复制配置结构），丢给 Copilot，让它先把：


BLOCK_DEFINITIONS


BlockInsertMenu


BlockTypeSwitcher


这三个文件生出来，你就从“好难”降级为“烦但能干”的级别了。
