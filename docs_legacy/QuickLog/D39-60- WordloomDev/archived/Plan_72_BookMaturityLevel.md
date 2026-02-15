4. 给你一个可以直接写进 RULES 的 mini 版本

Book.maturity_score（0–100）

+5：有标题

+5：有 description

+5：至少 1 个 tag

+5：block类型 大于3种

+5 选择了lucide封面

+0～20：按 blocks 数线性加分（比如 0 blocks = 0 分，≥20 blocks = 20 分封顶）
+1：一条block+1分

相当于卡死了45分是必须要完成的，而且没有完成这45分，无法手动修改额外的55分；

+0～20：TODO 越少分越高（没有 TODO = 20 分）

所以如果有TODO会倒扣分（而且无法手动改，除非完成TODO）

Score → 状态

score < 30 → Seed

30 ≤ score < 70 → Growing

score ≥ 70 → Stable

用户可以手动指定状态，但 UI 要显示一个小图标说明「已覆盖自动规则」。

LegacyFlag

默认为 false

变 true 的条件：

手动设为 Legacy；

或：status === Stable 且 lastEdited > 180 天前 且 最近 90 天打开次数 == 0 且 未被 pinned → 系统弹出建议，“确认后设为 Legacy”。