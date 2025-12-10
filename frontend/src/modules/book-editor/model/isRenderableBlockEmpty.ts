import type {
  BlockEditorRenderable,
} from './BlockEditorContext';
import type {
  CalloutBlockContent,
  CodeBlockContent,
  HeadingBlockContent,
  ListBlockContent,
  PanelBlockContent,
  ParagraphBlockContent,
  QuoteBlockContent,
  TodoListBlockContent,
} from '@/entities/block';

const isBlank = (value?: string | null) => !value || value.trim().length === 0;

const areListItemsBlank = (items?: string[]) => {
  if (!Array.isArray(items) || items.length === 0) {
    return true;
  }
  return items.every((item) => isBlank(typeof item === 'string' ? item : String(item ?? '')));
};

const areTodoItemsBlank = (content?: TodoListBlockContent['items']) => {
  if (!Array.isArray(content) || content.length === 0) {
    return true;
  }
  return content.every((item) => isBlank(item?.text));
};

export const isRenderableBlockEmpty = (block: BlockEditorRenderable): boolean => {
  const content = block.content;
  switch (block.kind) {
    case 'paragraph': {
      const paragraph = content as ParagraphBlockContent;
      return isBlank(paragraph?.text);
    }
    case 'heading': {
      const heading = content as HeadingBlockContent;
      return isBlank(heading?.text);
    }
    case 'bulleted_list':
    case 'numbered_list': {
      const list = content as ListBlockContent;
      return areListItemsBlank(list?.items);
    }
    case 'todo_list': {
      const todo = content as TodoListBlockContent;
      return areTodoItemsBlank(todo?.items);
    }
    case 'quote': {
      const quote = content as QuoteBlockContent;
      return isBlank(quote?.text);
    }
    case 'callout': {
      const callout = content as CalloutBlockContent;
      return isBlank(callout?.text);
    }
    case 'code': {
      const code = content as CodeBlockContent;
      return isBlank(code?.code);
    }
    case 'panel': {
      const panel = content as PanelBlockContent;
      return isBlank(panel?.title) && isBlank(panel?.body);
    }
    default:
      return false;
  }
};
