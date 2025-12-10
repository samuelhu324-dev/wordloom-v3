import React from 'react';
import type {
  BlockContent,
  BlockDto,
  BlockKind,
  HeadingBlockContent,
  ParagraphBlockContent,
  ListBlockContent,
  TodoListBlockContent,
  TodoListItemContent,
  CalloutBlockContent,
  QuoteBlockContent,
  DividerBlockContent,
  ImageBlockContent,
  ImageGalleryBlockContent,
  ImageGalleryItemContent,
  CodeBlockContent,
  CustomBlockContent,
  PanelBlockContent,
} from '@/entities/block';
import { generateBlockScopedId } from '@/entities/block';
import { ParagraphDisplay } from '../ui/ParagraphDisplay';
import { HeadingDisplay } from '../ui/HeadingDisplay';
import { ParagraphEditor, type MarkdownShortcutRequest } from '../ui/ParagraphEditor';
import { HeadingEditor } from '../ui/HeadingEditor';
import { ListDisplay, ListEditor } from '../ui/ListBlock';
import { TodoListDisplay, TodoListEditor } from '../ui/TodoListBlock';
import { CalloutDisplay, CalloutEditor } from '../ui/CalloutBlock';
import { QuoteDisplay, QuoteEditor } from '../ui/QuoteBlock';
import { DividerDisplay, DividerEditor } from '../ui/DividerBlock';
import { ImageBlockDisplay, ImageBlockEditor } from '../ui/ImageBlock';
import { ImageGalleryDisplay, ImageGalleryEditor } from '../ui/ImageGalleryBlock';
import { CodeBlockDisplay, CodeBlockEditor } from '../ui/CodeBlock';
import { CustomBlockDisplay, CustomBlockEditor } from '../ui/CustomBlock';
import { PanelDisplay, PanelEditor } from '../ui/PanelBlock';
import type { BlockEditorStartEditRequest } from '../ui/BlockEditorCore';
import type { KeyboardAction, KeyboardContextInput, KeyboardIntent } from './keyboardDecider';
export interface BlockDisplayProps {
  block: BlockDto;
  content: BlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export interface BlockEditorProps {
  block: BlockDto;
  content: BlockContent;
  autoFocus?: boolean;
  onChange: (next: BlockContent) => void;
  onSubmit: () => void;
  onExitEdit: () => void;
  onSoftBreak?: () => void;
  onDeleteEmptyBlock?: () => void;
  readOnly?: boolean;
  onStartEdit?: (request?: BlockEditorStartEditRequest) => void;
  onFocusPrev?: () => void;
  onFocusNext?: () => void;
  focusPosition?: 'start' | 'end';
  onRequestSlashMenu?: () => void;
  onMarkdownShortcut?: (request: MarkdownShortcutRequest) => void;
  getKeyboardContext?: (intent: KeyboardIntent) => KeyboardContextInput | null;
  onKeyboardDecision?: (payload: { intent: KeyboardIntent; decision: KeyboardAction }) => boolean | void;
}

export interface BlockPlugin {
  kind: BlockKind;
  Display: React.FC<BlockDisplayProps>;
  Editor: React.FC<BlockEditorProps>;
  normalize: (content: BlockContent) => BlockContent;
  createDefaultContent: () => BlockContent;
  prefersInlineShell?: boolean;
}

const normalizeParagraph = (content: BlockContent): ParagraphBlockContent => {
  if (!content || typeof content !== 'object') {
    return { text: '' };
  }
  const text = (content as { text?: unknown }).text;
  if (typeof text === 'string') {
    return { text };
  }
  return { text: '' };
};

const normalizeHeading = (content: BlockContent): HeadingBlockContent => {
  const source = normalizeParagraph(content);
  const level = (content as HeadingBlockContent)?.level;
  return {
    text: source.text,
    level: level === 1 || level === 3 ? level : 2,
  };
};

const normalizeList = (content: BlockContent): ListBlockContent => {
  const items = Array.isArray((content as ListBlockContent)?.items)
    ? (content as ListBlockContent).items.map((item) => (typeof item === 'string' ? item : String(item ?? '')))
    : [];
  if (items.length === 0) {
    items.push('');
  }
  return { items };
};

const normalizeTodoList = (content: BlockContent): TodoListBlockContent => {
  const items = Array.isArray((content as TodoListBlockContent)?.items)
    ? [...(content as TodoListBlockContent).items]
    : [];
  const normalized = items.map<TodoListItemContent>((item) => ({
    id: typeof item.id === 'string' && item.id ? item.id : generateBlockScopedId(),
    text: typeof item.text === 'string' ? item.text : '',
    checked: Boolean(item.checked),
    isPromoted: typeof item.isPromoted === 'boolean' ? item.isPromoted : undefined,
  }));
  if (normalized.length === 0) {
    normalized.push({ id: generateBlockScopedId(), text: '', checked: false });
  }
  return { items: normalized };
};

const normalizeCallout = (content: BlockContent): CalloutBlockContent => {
  const source = content as CalloutBlockContent;
  const allowed: NonNullable<CalloutBlockContent['variant']>[] = ['info', 'warning', 'danger', 'success'];
  const variant = allowed.includes(source?.variant as any)
    ? (source.variant as NonNullable<CalloutBlockContent['variant']>)
    : 'info';
  return {
    variant,
    text: typeof source?.text === 'string' ? source.text : '',
  };
};

const normalizeQuote = (content: BlockContent): QuoteBlockContent => {
  const source = content as QuoteBlockContent;
  return {
    text: typeof source?.text === 'string' ? source.text : '',
    source: typeof source?.source === 'string' ? source.source : undefined,
  };
};

const normalizeDivider = (content: BlockContent): DividerBlockContent => {
  const style = (content as DividerBlockContent)?.style;
  return { style: style === 'dashed' ? 'dashed' : 'solid' };
};

const normalizeImage = (content: BlockContent): ImageBlockContent => {
  const source = content as ImageBlockContent;
  return {
    imageId: typeof source?.imageId === 'string' ? source.imageId : undefined,
    url: typeof source?.url === 'string' ? source.url : undefined,
    caption: typeof source?.caption === 'string' ? source.caption : undefined,
  };
};

const normalizeImageGallery = (content: BlockContent): ImageGalleryBlockContent => {
  const layout = (content as ImageGalleryBlockContent)?.layout === 'grid' ? 'grid' : 'strip';
  const rawItems = Array.isArray((content as ImageGalleryBlockContent)?.items)
    ? ((content as ImageGalleryBlockContent).items as ImageGalleryItemContent[])
    : [];
  const items = rawItems.map<ImageGalleryItemContent>((item) => ({
    id: typeof item.id === 'string' && item.id ? item.id : generateBlockScopedId(),
    url: typeof item.url === 'string' ? item.url : '',
    caption: typeof item.caption === 'string' ? item.caption : undefined,
    indexLabel: typeof item.indexLabel === 'string' ? item.indexLabel : undefined,
  }));
  return {
    layout,
    maxPerRow: typeof (content as ImageGalleryBlockContent)?.maxPerRow === 'number'
      ? (content as ImageGalleryBlockContent).maxPerRow
      : undefined,
    items,
  };
};

const normalizePanel = (content: BlockContent): PanelBlockContent => {
  const source = content as PanelBlockContent;
  return {
    layout: source?.layout === 'two-column' ? 'two-column' : 'one-column',
    title: typeof source?.title === 'string' ? source.title : '',
    body: typeof source?.body === 'string' ? source.body : '',
    imageUrl: typeof source?.imageUrl === 'string' ? source.imageUrl : '',
  };
};

const normalizeCode = (content: BlockContent): CodeBlockContent => {
  const source = content as CodeBlockContent;
  return {
    language: typeof source?.language === 'string' ? source.language : 'text',
    code: typeof source?.code === 'string' ? source.code : '',
  };
};

const normalizeCustom = (content: BlockContent): CustomBlockContent => {
  if (!content || typeof content !== 'object') {
    return {};
  }
  return content as CustomBlockContent;
};

const paragraphPlugin: BlockPlugin = {
  kind: 'paragraph',
  Display: ({ block, content, onStartEdit }) => (
    <ParagraphDisplay blockId={block.id} text={normalizeParagraph(content).text} onStartEdit={onStartEdit} />
  ),
  Editor: ({ block, content, onChange, ...rest }) => (
    <ParagraphEditor
      blockId={block.id}
      value={normalizeParagraph(content).text}
      {...rest}
      onChange={(value) => onChange({ text: value })}
    />
  ),
  normalize: (content) => normalizeParagraph(content),
  createDefaultContent: () => ({ text: '' }),
  prefersInlineShell: true,
};

const headingPlugin: BlockPlugin = {
  kind: 'heading',
  Display: ({ block, content, onStartEdit }) => (
    <HeadingDisplay blockId={block.id} content={normalizeHeading(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ block, content, onChange, ...rest }) => (
    <HeadingEditor
      blockId={block.id}
      content={normalizeHeading(content)}
      onChange={(next) => onChange(next)}
      {...rest}
    />
  ),
  normalize: (content) => normalizeHeading(content),
  createDefaultContent: () => ({ text: '', level: 2 }),
  prefersInlineShell: true,
};

const todoListPlugin: BlockPlugin = {
  kind: 'todo_list',
  Display: ({ content, onStartEdit }) => (
    <TodoListDisplay content={normalizeTodoList(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({
    block,
    content,
    onChange,
    onExitEdit,
    autoFocus,
    readOnly,
    onStartEdit,
    onDeleteEmptyBlock,
    onSoftBreak,
    onFocusPrev,
    onFocusNext,
    onSubmit,
  }) => (
    <TodoListEditor
      blockId={block.id}
      content={normalizeTodoList(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
      onDeleteEmptyBlock={onDeleteEmptyBlock}
      onSoftBreak={onSoftBreak}
      autoFocus={autoFocus}
      readOnly={readOnly}
      onStartEdit={onStartEdit}
      onFocusPrev={onFocusPrev}
      onFocusNext={onFocusNext}
      onCreateSiblingBlock={onSubmit}
    />
  ),
  normalize: (content) => normalizeTodoList(content),
  createDefaultContent: () => normalizeTodoList({} as BlockContent),
  prefersInlineShell: true,
};

const createListPlugin = (kind: 'bulleted_list' | 'numbered_list'): BlockPlugin => {
  const ordered = kind === 'numbered_list';
  return {
    kind,
    Display: ({ content, onStartEdit }) => (
      <ListDisplay content={normalizeList(content)} ordered={ordered} onStartEdit={onStartEdit} />
    ),
    Editor: ({
      block,
      content,
      onChange,
      onExitEdit,
      autoFocus,
      readOnly,
      onDeleteEmptyBlock,
      onSoftBreak,
      onStartEdit,
      onFocusPrev,
      onFocusNext,
      onSubmit,
    }) => (
      <ListEditor
        blockId={block.id}
        content={normalizeList(content)}
        ordered={ordered}
        onChange={(next) => onChange(next)}
        onExitEdit={onExitEdit}
        autoFocus={autoFocus}
        readOnly={readOnly}
        onDeleteEmptyBlock={onDeleteEmptyBlock}
        onSoftBreak={onSoftBreak}
        onStartEdit={onStartEdit}
        onFocusPrev={onFocusPrev}
        onFocusNext={onFocusNext}
        onCreateSiblingBlock={onSubmit}
      />
    ),
    normalize: (content) => normalizeList(content),
    createDefaultContent: () => normalizeList({} as BlockContent),
    prefersInlineShell: true,
  };
};

const bulletedListPlugin = createListPlugin('bulleted_list');
const numberedListPlugin = createListPlugin('numbered_list');

const calloutPlugin: BlockPlugin = {
  kind: 'callout',
  Display: ({ content, onStartEdit }) => (
    <CalloutDisplay content={normalizeCallout(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <CalloutEditor
      content={normalizeCallout(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeCallout(content),
  createDefaultContent: () => ({ text: '', variant: 'info' }),
};

const quotePlugin: BlockPlugin = {
  kind: 'quote',
  Display: ({ content, onStartEdit }) => (
    <QuoteDisplay content={normalizeQuote(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <QuoteEditor
      content={normalizeQuote(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeQuote(content),
  createDefaultContent: () => ({ text: '', source: '' }),
};

const dividerPlugin: BlockPlugin = {
  kind: 'divider',
  Display: ({ content }) => <DividerDisplay content={normalizeDivider(content)} />,
  Editor: ({ content, onChange, onExitEdit }) => (
    <DividerEditor
      content={normalizeDivider(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeDivider(content),
  createDefaultContent: () => ({ style: 'solid' }),
};

const imagePlugin: BlockPlugin = {
  kind: 'image',
  Display: ({ content, onStartEdit }) => (
    <ImageBlockDisplay content={normalizeImage(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <ImageBlockEditor
      content={normalizeImage(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeImage(content),
  createDefaultContent: () => ({ url: '', caption: '' }),
};

const imageGalleryPlugin: BlockPlugin = {
  kind: 'image_gallery',
  Display: ({ content, onStartEdit }) => (
    <ImageGalleryDisplay content={normalizeImageGallery(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <ImageGalleryEditor
      content={normalizeImageGallery(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeImageGallery(content),
  createDefaultContent: () => ({ layout: 'strip', items: [] }),
};

const panelPlugin: BlockPlugin = {
  kind: 'panel',
  Display: ({ content, onStartEdit }) => (
    <PanelDisplay content={normalizePanel(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <PanelEditor
      content={normalizePanel(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizePanel(content),
  createDefaultContent: () => ({ layout: 'one-column', title: '', body: '', imageUrl: '' }),
};

const codePlugin: BlockPlugin = {
  kind: 'code',
  Display: ({ content, onStartEdit }) => (
    <CodeBlockDisplay content={normalizeCode(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <CodeBlockEditor
      content={normalizeCode(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeCode(content),
  createDefaultContent: () => ({ language: 'text', code: '' }),
};

const customPlugin: BlockPlugin = {
  kind: 'custom',
  Display: ({ content, onStartEdit }) => (
    <CustomBlockDisplay content={normalizeCustom(content)} onStartEdit={onStartEdit} />
  ),
  Editor: ({ content, onChange, onExitEdit }) => (
    <CustomBlockEditor
      content={normalizeCustom(content)}
      onChange={(next) => onChange(next)}
      onExitEdit={onExitEdit}
    />
  ),
  normalize: (content) => normalizeCustom(content),
  createDefaultContent: () => ({}),
};

const REGISTRY: Partial<Record<BlockKind, BlockPlugin>> = {
  paragraph: paragraphPlugin,
  heading: headingPlugin,
  bulleted_list: bulletedListPlugin,
  numbered_list: numberedListPlugin,
  todo_list: todoListPlugin,
  callout: calloutPlugin,
  quote: quotePlugin,
  divider: dividerPlugin,
  image: imagePlugin,
  image_gallery: imageGalleryPlugin,
  panel: panelPlugin,
  code: codePlugin,
  custom: customPlugin,
};

export const getBlockPlugin = (kind: BlockKind): BlockPlugin | null => REGISTRY[kind] ?? null;

export const getRegisteredKinds = (): BlockKind[] => Object.keys(REGISTRY) as BlockKind[];
