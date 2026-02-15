我这里说的 “做一个 Command 列表（比如 BLOCK_COMMANDS）” 指的是：在 前端代码里 做一份「指令配置表 / 注册表」，通常就是一个 TypeScript 常量数组或对象，用来统一管理 toolbar 按钮、插入菜单、快捷键 等所有跟 BlockEditor 命令相关的东西。

1. 这个 “Command 列表” 是啥

可以理解成一张表：一条命令 = 一行配置，里面写清楚：

command 的内部 id（bold / insertHeading / splitBlock…）

对应的 i18n 前缀或 key

默认快捷键（Mod+B 之类）

在哪类菜单里出现（toolbar / insert menu / context menu）

执行函数（或者执行时需要的参数）

用 TypeScript 写，大概长这样：

// blockCommands.ts
export type BlockCommandId =
  | "bold"
  | "italic"
  | "underline"
  | "insertHeading"
  | "insertQuote";

export interface BlockCommandConfig {
  id: BlockCommandId;
  // i18n key 前缀：具体 label / tooltip 再拼子 key
  i18nBaseKey: string; // 比如 "books.blocks.editor.commands.bold"
  defaultKeybinding?: string; // "Mod+B"
  group: "format" | "insert" | "structure";
  icon?: React.ComponentType;
  run: (ctx: BlockEditorContext) => void;
}

export const BLOCK_COMMANDS: BlockCommandConfig[] = [
  {
    id: "bold",
    i18nBaseKey: "books.blocks.editor.commands.bold",
    defaultKeybinding: "Mod+B",
    group: "format",
    icon: BoldIcon,
    run: (ctx) => ctx.toggleMark("bold"),
  },
  {
    id: "insertHeading",
    i18nBaseKey: "books.blocks.editor.commands.insertHeading",
    group: "insert",
    icon: HeadingIcon,
    run: (ctx) => ctx.insertBlock("heading"),
  },
  // ...
];


然后：

Toolbar 渲染时：从 BLOCK_COMMANDS 里过滤出 group === "format" 的命令，用 t(cmd.i18nBaseKey + ".label") 渲染按钮文本，用 t(cmd.i18nBaseKey + ".tooltip") 渲染 tooltip。

插入菜单：过滤 group === "insert"，展示为菜单列表。

快捷键系统：把 defaultKeybinding 注册进你的 hotkey handler，触发时按 id 找到对应 run。

这样：

命令的名字 / 快捷键 / 文案 key 只有一个“真来源”；

不会出现「toolbar 写了“Bold”，菜单写了“Strong”，快捷键提示又是第三种说法」这种漂移。

2. 为什么不推荐先上 YAML

完全可以把这张表写成 YAML / JSON，再在前端 import 使用，比如：

# blockCommands.yaml
- id: bold
  i18nBaseKey: books.blocks.editor.commands.bold
  defaultKeybinding: Mod+B
  group: format
- id: insertHeading
  i18nBaseKey: books.blocks.editor.commands.insertHeading
  group: insert


然后在 TS 里：

import rawCommands from "./blockCommands.yaml";

export const BLOCK_COMMANDS = rawCommands as BlockCommandConfig[];


但是在你现在这个阶段，我更倾向：

先用 TypeScript 直接写常量：

有类型检查、自动补全；

改命令行为/执行函数时不用来回跳文件；

结构稳定后，你再考虑把“纯配置部分”抽成 YAML 也来得及。

YAML 适合那种“非工程师也要改配置”的场景；你现在前后端都自己搞，直接 TS 常量是成本最低、最不容易漂移的方案。

3. 要跟 i18n 字典怎么对上号

比如你决定用我上面的 i18nBaseKey 方案，那字典里可以这样组织：

// zh-CN
{
  "books": {
    "blocks": {
      "editor": {
        "commands": {
          "bold": {
            "label": "加粗",
            "tooltip": "加粗（Ctrl+B）"
          },
          "insertHeading": {
            "label": "插入标题",
            "tooltip": "插入一级标题"
          }
        }
      }
    }
  }
}


渲染时：

<Button
  aria-label={t(cmd.i18nBaseKey + ".label")}
  title={t(cmd.i18nBaseKey + ".tooltip")}
>
  {t(cmd.i18nBaseKey + ".label")}
</Button>


这样：

Command 列表负责：有哪些命令、归类、默认快捷键、执行逻辑；

i18n 字典负责：这些命令在不同语言里怎么叫。

两边职责很干净，后面扩命令 / 换语言都不会乱。

总结一句：
我说的那份 “Command 列表 / BLOCK_COMMANDS” 本质上就是一个 TS 配置+逻辑表，不是必须是 YAML；现在最省心的做法是，把它写成一个 blockCommands.ts，让 toolbar / 菜单 / 快捷键都从这份表里吃数据。