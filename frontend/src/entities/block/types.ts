import { BaseDto } from '@/shared/api';

export type BlockKind =
  | 'heading'
  | 'paragraph'
  | 'bulleted_list'
  | 'numbered_list'
  | 'todo_list'
  | 'code'
  | 'callout'
  | 'quote'
  | 'divider'
  | 'image'
  | 'image_gallery'
  | 'panel'
  | 'custom';

export type BlockTypeApi =
  | 'text'
  | 'heading'
  | 'code'
  | 'image'
  | 'quote'
  | 'list'
  | 'todo_list'
  | 'table'
  | 'divider';

export interface BlockApiResponse extends BaseDto {
  book_id: string;
  type?: BlockTypeApi;
  block_type?: BlockTypeApi;
  content: string;
  order?: string;
  fractional_index?: string;
  heading_level?: number | null;
  soft_deleted_at?: string | null;
}

export interface ParagraphBlockContent {
  text: string;
}

export interface HeadingBlockContent {
  level: 1 | 2 | 3;
  text: string;
}

export interface ListBlockContent {
  items: string[];
}

export interface TodoListItemContent {
  id?: string;
  text: string;
  checked: boolean;
  isPromoted?: boolean;
}

export interface TodoListBlockContent {
  items: TodoListItemContent[];
}

export interface CodeBlockContent {
  language?: string;
  code: string;
}

export interface CalloutBlockContent {
  variant?: 'info' | 'warning' | 'danger' | 'success';
  text: string;
}

export interface QuoteBlockContent {
  text: string;
  source?: string;
}

export interface DividerBlockContent {
  style?: 'solid' | 'dashed';
}

export interface ImageBlockContent {
  imageId?: string;
  url?: string;
  caption?: string;
}

export interface ImageGalleryItemContent {
  id?: string;
  url: string;
  caption?: string;
  indexLabel?: string;
}

export interface ImageGalleryBlockContent {
  layout?: 'strip' | 'grid';
  maxPerRow?: number;
  items: ImageGalleryItemContent[];
}

export interface PanelBlockContent {
  layout?: 'one-column' | 'two-column';
  title?: string;
  body?: string;
  imageUrl?: string;
}

export interface CustomBlockContent {
  schemaVersion?: string;
  data?: unknown;
}

export type BlockContent =
  | ParagraphBlockContent
  | HeadingBlockContent
  | ListBlockContent
  | TodoListBlockContent
  | CodeBlockContent
  | CalloutBlockContent
  | QuoteBlockContent
  | DividerBlockContent
  | ImageBlockContent
  | ImageGalleryBlockContent
  | PanelBlockContent
  | CustomBlockContent
  | Record<string, unknown>;

/** Block DTO - 书中的最小单位 */
export interface BlockDto extends Omit<BlockApiResponse, 'content'> {
  kind: BlockKind;
  fractional_index: string;
  content: BlockContent;
}

/** Create Block Request */
export interface CreateBlockRequest {
  book_id: string;
  kind: BlockKind;
  content: string;
  heading_level?: number | null;
}

/** Update Block Request */
export interface UpdateBlockRequest {
  kind?: BlockKind;
  content?: string;
}

const API_TYPE_TO_KIND: Record<BlockTypeApi, BlockKind> = {
  text: 'paragraph',
  heading: 'heading',
  code: 'code',
  image: 'image',
  quote: 'quote',
  list: 'bulleted_list',
  todo_list: 'todo_list',
  table: 'panel',
  divider: 'divider',
};

const KIND_TO_API_TYPE: Record<BlockKind, BlockTypeApi> = {
  heading: 'heading',
  paragraph: 'text',
  bulleted_list: 'list',
  numbered_list: 'list',
  todo_list: 'todo_list',
  code: 'code',
  callout: 'quote',
  quote: 'quote',
  divider: 'divider',
  image: 'image',
  image_gallery: 'image',
  panel: 'table',
  custom: 'text',
};

const tryParseJson = (raw: unknown): unknown => {
  if (typeof raw !== 'string') {
    return raw;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    return raw;
  }
};

const ensureParagraphContent = (value: unknown): ParagraphBlockContent => {
  if (typeof value === 'string') {
    return { text: value };
  }
  if (value && typeof value === 'object' && 'text' in value) {
    const textValue = (value as { text?: unknown }).text;
    return { text: typeof textValue === 'string' ? textValue : String(textValue ?? '') };
  }
  return { text: '' };
};

const ensureListContent = (value: unknown): ListBlockContent => {
  if (!value) {
    return { items: [''] };
  }
  if (Array.isArray(value)) {
    const normalized = value.map((item) => (typeof item === 'string' ? item : String(item ?? '')));
    return { items: normalized.length ? normalized : [''] };
  }
  if (typeof value === 'object') {
    const source = value as Record<string, unknown>;
    if (Array.isArray(source.items)) {
      const normalized = source.items.map((item) => (typeof item === 'string' ? item : String(item ?? '')));
      return { items: normalized.length ? normalized : [''] };
    }
  }
  return { items: [''] };
};

export const generateBlockScopedId = (): string => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `todo-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
};

const ensureTodoListContent = (value: unknown): TodoListBlockContent => {
  if (!value || typeof value !== 'object') {
    return { items: [] };
  }
  const rawItems = Array.isArray((value as { items?: unknown }).items)
    ? ((value as { items: unknown[] }).items)
    : [];
  const items: TodoListItemContent[] = rawItems.map((item) => {
    if (!item || typeof item !== 'object') {
      return { id: generateBlockScopedId(), text: '', checked: false };
    }
    const source = item as Record<string, unknown>;
    return {
      id: typeof source.id === 'string' && source.id ? source.id : generateBlockScopedId(),
      text: typeof source.text === 'string' ? source.text : String(source.text ?? ''),
      checked: typeof source.checked === 'boolean' ? source.checked : Boolean(source.checked),
      isPromoted: typeof source.isPromoted === 'boolean' ? source.isPromoted : undefined,
    };
  });

  if (items.length === 0) {
    items.push({ id: generateBlockScopedId(), text: '', checked: false });
  }

  return { items };
};

const ensureCalloutContent = (value: unknown): CalloutBlockContent => {
  if (!value || typeof value !== 'object') {
    return { variant: 'info', text: '' };
  }
  const source = value as Record<string, unknown>;
  const variant = source.variant;
  const allowed: CalloutBlockContent['variant'][] = ['info', 'warning', 'danger', 'success'];
  return {
    variant: allowed.includes(variant as any) ? (variant as CalloutBlockContent['variant']) : 'info',
    text: typeof source.text === 'string' ? source.text : String(source.text ?? ''),
  };
};

const ensureQuoteContent = (value: unknown): QuoteBlockContent => {
  if (!value || typeof value !== 'object') {
    return { text: '', source: '' };
  }
  const source = value as Record<string, unknown>;
  return {
    text: typeof source.text === 'string' ? source.text : String(source.text ?? ''),
    source: typeof source.source === 'string' ? source.source : source.source == null ? undefined : String(source.source),
  };
};

const ensureDividerContent = (value: unknown): DividerBlockContent => {
  if (!value || typeof value !== 'object') {
    return { style: 'solid' };
  }
  const style = (value as Record<string, unknown>).style;
  return {
    style: style === 'dashed' ? 'dashed' : 'solid',
  };
};

const ensureImageContent = (value: unknown): ImageBlockContent => {
  if (!value || typeof value !== 'object') {
    return { imageId: '', url: '', caption: '' };
  }
  const source = value as Record<string, unknown>;
  return {
    imageId: typeof source.imageId === 'string' ? source.imageId : undefined,
    url: typeof source.url === 'string' ? source.url : undefined,
    caption: typeof source.caption === 'string' ? source.caption : source.caption == null ? undefined : String(source.caption),
  };
};

const ensureImageGalleryContent = (value: unknown): ImageGalleryBlockContent => {
  if (!value || typeof value !== 'object') {
    return { layout: 'strip', items: [] };
  }
  const source = value as Record<string, unknown>;
  const rawItems = Array.isArray(source.items) ? (source.items as unknown[]) : [];
  const items: ImageGalleryItemContent[] = rawItems.map((item) => {
    if (!item || typeof item !== 'object') {
      return { id: generateBlockScopedId(), url: '', caption: '' };
    }
    const content = item as Record<string, unknown>;
    return {
      id: typeof content.id === 'string' && content.id ? content.id : generateBlockScopedId(),
      url: typeof content.url === 'string' ? content.url : '',
      caption: typeof content.caption === 'string' ? content.caption : content.caption == null ? undefined : String(content.caption),
      indexLabel: typeof content.indexLabel === 'string' ? content.indexLabel : undefined,
    };
  });
  return {
    layout: source.layout === 'grid' ? 'grid' : 'strip',
    maxPerRow: typeof source.maxPerRow === 'number' ? source.maxPerRow : undefined,
    items,
  };
};

const ensurePanelContent = (value: unknown): PanelBlockContent => {
  if (!value || typeof value !== 'object') {
    return { layout: 'one-column', title: '', body: '', imageUrl: '' };
  }
  const source = value as Record<string, unknown>;
  return {
    layout: source.layout === 'two-column' ? 'two-column' : 'one-column',
    title: typeof source.title === 'string' ? source.title : source.title == null ? undefined : String(source.title),
    body: typeof source.body === 'string' ? source.body : source.body == null ? undefined : String(source.body),
    imageUrl: typeof source.imageUrl === 'string' ? source.imageUrl : source.imageUrl == null ? undefined : String(source.imageUrl),
  };
};

export const parseBlockContent = (kind: BlockKind, rawContent: unknown): BlockContent => {
  const parsed = tryParseJson(rawContent);
  switch (kind) {
    case 'paragraph':
      return ensureParagraphContent(parsed);
    case 'bulleted_list':
    case 'numbered_list':
      return ensureListContent(parsed);
    case 'todo_list':
      return ensureTodoListContent(parsed);
    case 'callout':
      return ensureCalloutContent(parsed);
    case 'quote':
      return ensureQuoteContent(parsed);
    case 'divider':
      return ensureDividerContent(parsed);
    case 'image':
      return ensureImageContent(parsed);
    case 'image_gallery':
      return ensureImageGalleryContent(parsed);
    case 'panel':
      return ensurePanelContent(parsed);
    default:
      return (parsed ?? {}) as BlockContent;
  }
};

export const createDefaultBlockContent = (kind: BlockKind): BlockContent => {
  switch (kind) {
    case 'paragraph':
      return { text: '' } satisfies ParagraphBlockContent;
    case 'heading':
      return { level: 2, text: '' } satisfies HeadingBlockContent;
    case 'bulleted_list':
    case 'numbered_list':
      return { items: [''] } satisfies ListBlockContent;
    case 'todo_list':
      return {
        items: [{ id: generateBlockScopedId(), text: '', checked: false }],
      } satisfies TodoListBlockContent;
    case 'code':
      return { language: 'text', code: '' } satisfies CodeBlockContent;
    case 'callout':
      return { variant: 'info', text: '' } satisfies CalloutBlockContent;
    case 'quote':
      return { text: '', source: '' } satisfies QuoteBlockContent;
    case 'divider':
      return { style: 'solid' } satisfies DividerBlockContent;
    case 'image':
      return { imageId: '', url: '', caption: '' } satisfies ImageBlockContent;
    case 'image_gallery':
      return { layout: 'strip', items: [] } satisfies ImageGalleryBlockContent;
    case 'panel':
      return { layout: 'one-column', title: '', body: '', imageUrl: '' } satisfies PanelBlockContent;
    case 'custom':
    default:
      return {} satisfies CustomBlockContent;
  }
};

export const serializeBlockContent = (kind: BlockKind, content: BlockContent): string => {
  if (kind === 'paragraph') {
    if (typeof content === 'string') {
      return content;
    }
    const text = (content as ParagraphBlockContent)?.text;
    return typeof text === 'string' ? text : '';
  }
  if (typeof content === 'string') {
    return content;
  }
  try {
    return JSON.stringify(content ?? {});
  } catch (error) {
    console.warn('Failed to serialize block content', error);
    return '';
  }
};

export const getParagraphText = (source: { kind: BlockKind; content: unknown }): string => {
  if (source.kind !== 'paragraph') {
    return '';
  }
  const value = source.content;
  if (typeof value === 'string') {
    return value;
  }
  if (value && typeof value === 'object' && 'text' in value) {
    const textValue = (value as { text?: unknown }).text;
    return typeof textValue === 'string' ? textValue : String(textValue ?? '');
  }
  return '';
};

export const mapApiTypeToKind = (type: BlockTypeApi): BlockKind => API_TYPE_TO_KIND[type] ?? 'custom';

export const mapKindToApiType = (kind: BlockKind): BlockTypeApi => KIND_TO_API_TYPE[kind] ?? 'text';
