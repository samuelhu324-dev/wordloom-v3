import { BlockKind } from '@/entities/block';

// LEGACY: Menu definitions for the deprecated BlockList experience.

export interface InsertMenuItemConfig {
  label: string;
  kind: BlockKind;
  keywords?: string[];
  headingLevel?: 1 | 2 | 3;
  description?: string;
}

export interface InsertMenuGroupConfig {
  title: string;
  items: InsertMenuItemConfig[];
}

const TEXT_INSERT_ITEMS: InsertMenuItemConfig[] = [
  { label: '段落', kind: 'paragraph', keywords: ['text', 'paragraph', '正文', '/text'], description: '标准正文段落' },
  { label: '一级标题', kind: 'heading', headingLevel: 1, keywords: ['h1', 'heading1', '一级标题', '/h1'], description: '章节主标题' },
  { label: '二级标题', kind: 'heading', headingLevel: 2, keywords: ['h2', 'heading2', '二级标题', '/h2'], description: '段落标题' },
  { label: '三级标题', kind: 'heading', headingLevel: 3, keywords: ['h3', 'heading3', '三级标题', '/h3'], description: '内层小标题' },
];

const LIST_INSERT_ITEMS: InsertMenuItemConfig[] = [
  { label: '项目符号列表', kind: 'bulleted_list', keywords: ['list', 'bullet', 'ul', '•'], description: '普通项目前缀 •' },
  { label: '编号列表', kind: 'numbered_list', keywords: ['list', 'numbered', 'ol', '1.'], description: '自动递增编号' },
  { label: '待办列表', kind: 'todo_list', keywords: ['todo', 'task', 'checkbox'], description: '可勾选复选框' },
];

export const COMMON_INSERT_ITEMS: InsertMenuItemConfig[] = [
  ...TEXT_INSERT_ITEMS,
  ...LIST_INSERT_ITEMS,
  { label: 'Callout', kind: 'callout', keywords: ['callout', 'note', 'info'], description: '强调提示气泡' },
  { label: '分割线', kind: 'divider', keywords: ['divider', 'line', 'split'], description: '细分隔线' },
];

export const EXTRA_INSERT_GROUPS: InsertMenuGroupConfig[] = [
  {
    title: '标注',
    items: [{ label: '引用', kind: 'quote', keywords: ['quote', 'reference', '>'], description: '带来源的引用段落' }],
  },
  {
    title: '媒体',
    items: [
      { label: '图片', kind: 'image', keywords: ['image', 'photo', 'img'], description: '单张图片' },
      { label: '图片组', kind: 'image_gallery', keywords: ['gallery', 'album'], description: '多张图片拼排' },
    ],
  },
];

export const ALL_INSERT_ITEMS: InsertMenuItemConfig[] = [
  ...COMMON_INSERT_ITEMS,
  ...EXTRA_INSERT_GROUPS.flatMap((group) => group.items),
];

export type SlashCommandAction =
  | { type: 'insert'; kind: BlockKind; headingLevel?: 1 | 2 | 3 }
  | { type: 'transform'; target: 'paragraph' | 'heading'; headingLevel?: 1 | 2 | 3 };

export interface SlashCommandConfig {
  id: string;
  label: string;
  keywords: string[];
  hint?: string;
  description?: string;
  action: SlashCommandAction;
}

const TRANSFORM_COMMANDS: SlashCommandConfig[] = [
  {
    id: 'transform-paragraph',
    label: '切换为正文',
    keywords: ['/text', '/paragraph', 'paragraph', 'text', '正文'],
    hint: 'Ctrl+0',
    description: '恢复为普通正文',
    action: { type: 'transform', target: 'paragraph' },
  },
  {
    id: 'transform-h1',
    label: '切换为 H1 标题',
    keywords: ['/h1', 'h1', '一级标题'],
    hint: 'Ctrl+Alt+1',
    description: '章节主标题',
    action: { type: 'transform', target: 'heading', headingLevel: 1 },
  },
  {
    id: 'transform-h2',
    label: '切换为 H2 标题',
    keywords: ['/h2', 'h2', '二级标题'],
    hint: 'Ctrl+Alt+2',
    description: '段落标题',
    action: { type: 'transform', target: 'heading', headingLevel: 2 },
  },
  {
    id: 'transform-h3',
    label: '切换为 H3 标题',
    keywords: ['/h3', 'h3', '三级标题'],
    hint: 'Ctrl+Alt+3',
    description: '内层小标题',
    action: { type: 'transform', target: 'heading', headingLevel: 3 },
  },
];

export const SLASH_COMMANDS: SlashCommandConfig[] = [
  ...ALL_INSERT_ITEMS.map<SlashCommandConfig>((item, index) => ({
    id: `insert-${item.kind}-${item.headingLevel ?? index}`,
    label: `插入${item.label}`,
    keywords: item.keywords ?? [item.label],
    hint: item.description ? undefined : '插入新块',
    description: item.description,
    action: { type: 'insert', kind: item.kind, headingLevel: item.headingLevel },
  })),
  ...TRANSFORM_COMMANDS,
];
