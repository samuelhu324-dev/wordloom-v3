import type {
  BlockContent,
  BlockKind,
  CalloutBlockContent,
  HeadingBlockContent,
  ListBlockContent,
  PanelBlockContent,
  ParagraphBlockContent,
  QuoteBlockContent,
  TodoListBlockContent,
  TodoListItemContent,
} from '@/entities/block';
import { generateBlockScopedId } from '@/entities/block';
import type { BlockEditorRenderable } from './BlockEditorContext';

export const BASE_BLOCK_KIND: BlockKind = 'paragraph';

const SPECIAL_BLOCK_KIND_SET = new Set<BlockKind>([
  'bulleted_list',
  'numbered_list',
  'todo_list',
  'quote',
  'callout',
  'panel',
]);

export const isBaseBlockKind = (kind: BlockKind): boolean => kind === BASE_BLOCK_KIND;

export const isSpecialBlockKind = (kind: BlockKind): boolean => SPECIAL_BLOCK_KIND_SET.has(kind);

export const createDefaultContentForKind = (kind: BlockKind): BlockContent => {
  switch (kind) {
    case 'paragraph':
      return { text: '' };
    case 'heading':
      return { text: '', level: 2 };
    case 'bulleted_list':
    case 'numbered_list':
      return { items: [''] } satisfies ListBlockContent;
    case 'todo_list': {
      const defaultItem: TodoListItemContent = {
        id: generateBlockScopedId(),
        text: '',
        checked: false,
      };
      return { items: [defaultItem] } satisfies TodoListBlockContent;
    }
    case 'quote':
      return { text: '', source: '' } satisfies QuoteBlockContent;
    case 'callout':
      return { text: '', variant: 'info' } satisfies CalloutBlockContent;
    case 'panel':
      return {
        layout: 'one-column',
        title: '',
        body: '',
        imageUrl: '',
      } satisfies PanelBlockContent;
    default:
      return { text: '' } satisfies ParagraphBlockContent;
  }
};

const normalizeText = (value: unknown): string => {
  if (typeof value === 'string') {
    return value;
  }
  if (value == null) {
    return '';
  }
  return String(value);
};

const joinLines = (values: string[], separator: string = '\n'): string => {
  if (!values.length) {
    return '';
  }
  return values.join(separator).trimEnd();
};

const deriveListText = (content: ListBlockContent | undefined): string => {
  if (!content || !Array.isArray(content.items)) {
    return '';
  }
  const normalized = content.items.map((item) => normalizeText(item).trimEnd());
  return joinLines(normalized);
};

const deriveTodoListText = (content: TodoListBlockContent | undefined): string => {
  if (!content || !Array.isArray(content.items)) {
    return '';
  }
  const normalized = content.items.map((item) => normalizeText(item?.text).trimEnd());
  return joinLines(normalized);
};

const derivePanelText = (content: PanelBlockContent | undefined): string => {
  if (!content) {
    return '';
  }
  const segments: string[] = [];
  if (content.title) {
    segments.push(content.title);
  }
  if (content.body) {
    segments.push(content.body);
  }
  return joinLines(segments, '\n\n');
};

export const deriveParagraphContentFromRenderable = (
  block: BlockEditorRenderable,
): ParagraphBlockContent => {
  switch (block.kind) {
    case 'paragraph': {
      const paragraph = block.content as ParagraphBlockContent;
      return { text: normalizeText(paragraph?.text) };
    }
    case 'heading': {
      const heading = block.content as HeadingBlockContent;
      return { text: normalizeText(heading?.text) };
    }
    case 'bulleted_list':
    case 'numbered_list': {
      return { text: deriveListText(block.content as ListBlockContent) };
    }
    case 'todo_list': {
      return { text: deriveTodoListText(block.content as TodoListBlockContent) };
    }
    case 'quote': {
      const quote = block.content as QuoteBlockContent;
      return { text: normalizeText(quote?.text) };
    }
    case 'callout': {
      const callout = block.content as CalloutBlockContent;
      return { text: normalizeText(callout?.text) };
    }
    case 'panel': {
      return { text: derivePanelText(block.content as PanelBlockContent) };
    }
    default: {
      const fallback = (block.content as { text?: unknown })?.text;
      return { text: normalizeText(fallback) };
    }
  }
};
