// LEGACY: Retained only for reference. Use modules/book-editor for all block editing.
import React from 'react';
import {
  BlockDto,
  BlockContent,
  BlockKind,
  ParagraphBlockContent,
  HeadingBlockContent,
  TodoListBlockContent,
  TodoListItemContent,
  CalloutBlockContent,
  QuoteBlockContent,
  DividerBlockContent,
  ImageBlockContent,
  ImageGalleryBlockContent,
  ListBlockContent,
  generateBlockScopedId,
} from '@/entities/block';
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  Star,
  Plus,
  Trash2,
  Image as ImageIcon,
  List,
  Grid,
} from 'lucide-react';
import styles from '../ui/BlockList.module.css';
import type { InsertBlockHandler } from './insertTypes';
import { SLASH_COMMANDS, SlashCommandConfig } from './insertMenuConfig';
import { getBlockPlugin, registerBlockPlugin } from './blockPlugins';
import { getSelectionWithin } from '@/modules/book-editor/model/caretDomUtils';

export interface BlockRendererProps {
  block: BlockDto;
  content: BlockContent;
  isEditing: boolean;
  editorRef?: React.RefObject<HTMLElement | null>;
  onStartEdit: () => void;
  onChange: (nextContent: BlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
  onQuickSave?: () => Promise<void> | void;
  onInsertBlock?: InsertBlockHandler;
  onTransformBlock?: (kind: BlockKind, content: BlockContent) => void;
  onDeleteBlock?: () => void;
}

export const BlockRenderer: React.FC<BlockRendererProps> = ({
  block,
  content,
  isEditing,
  editorRef,
  onStartEdit,
  onChange,
  onSave,
  onExitEdit,
  onCancelEdit,
  onQuickSave,
  onInsertBlock,
  onTransformBlock,
  onDeleteBlock,
}) => {
  if (isEditing) {
    return renderEditor({
      block,
      content,
      editorRef,
      onChange,
      onSave,
      onExitEdit,
      onCancelEdit,
      onInsertBlock,
      onTransformBlock,
      onDeleteBlock,
    });
  }
  return renderDisplay({ block, content, onStartEdit, onChange, onQuickSave });
};

interface DisplayProps {
  block: BlockDto;
  content: BlockContent;
  onStartEdit: () => void;
  onChange: (nextContent: BlockContent) => void;
  onQuickSave?: () => Promise<void> | void;
}

const renderDisplay = ({ block, content, onStartEdit, onChange, onQuickSave }: DisplayProps) => {
  const plugin = getBlockPlugin(block.kind);
  if (!plugin) {
    return <UnsupportedBlock kind={block.kind} />;
  }
  const DisplayComponent = plugin.Display;

  return (
    <DisplayComponent
      block={block}
      content={content}
      onStartEdit={onStartEdit}
      onChange={(nextContent) => onChange(nextContent)}
      onQuickSave={onQuickSave}
    />
  );
};

interface EditorProps {
  block: BlockDto;
  content: BlockContent;
  editorRef?: React.RefObject<HTMLElement | null>;
  onChange: (nextContent: BlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
  onInsertBlock?: InsertBlockHandler;
  onTransformBlock?: (kind: BlockKind, content: BlockContent) => void;
  onDeleteBlock?: () => void;
}

const renderEditor = ({
  block,
  content,
  editorRef,
  onChange,
  onSave,
  onExitEdit,
  onCancelEdit,
  onInsertBlock,
  onTransformBlock,
  onDeleteBlock,
}: EditorProps & { onTransformBlock?: (kind: BlockKind, content: BlockContent) => void }) => {
  const plugin = getBlockPlugin(block.kind);
  if (!plugin) {
    return <UnsupportedBlock kind={block.kind} />;
  }
  const EditorComponent = plugin.Editor;
  return (
    <EditorComponent
      block={block}
      content={content}
      editorRef={editorRef}
      onChange={onChange}
      onSave={onSave}
      onExitEdit={onExitEdit}
      onCancelEdit={onCancelEdit}
      onInsertBlock={onInsertBlock}
      onTransformBlock={onTransformBlock}
      onDeleteBlock={onDeleteBlock}
    />
  );
};

const ParagraphDisplay: React.FC<{ blockId: string; content: ParagraphBlockContent; onStartEdit: () => void }> = ({ blockId, content, onStartEdit }) => {
  const text = content?.text ?? '';
  const isEmpty = text.trim().length === 0;
  const shellClassName = `${styles.textBlockShell} ${styles.textBlockShellParagraph} ${isEmpty ? styles.textBlockShellParagraphEmpty : ''}`;
  return (
    <div
      className={shellClassName}
      role="button"
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit();
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onStartEdit();
        }
      }}
    >
      {text ? (
        text.split('\n').map((line, lineIndex) => (
          <p key={`${blockId}-${lineIndex}`} className={styles.paragraphTextLine}>
            {line || '\u00A0'}
          </p>
        ))
      ) : (
        <span className={styles.blockPlaceholder}>写点什么...</span>
      )}
    </div>
  );
};

const HeadingDisplay: React.FC<{
  content: HeadingBlockContent;
  onStartEdit: () => void;
}> = ({ content, onStartEdit }) => {
  const text = content?.text ?? '';
  const level = content?.level ?? 2;
  const Tag = (['h1', 'h2', 'h3'][Math.min(Math.max(level, 1), 3) - 1] ?? 'h2') as keyof JSX.IntrinsicElements;
  const placeholder = level === 1 ? '一级标题...' : level === 2 ? '二级标题...' : '三级标题...';
  const levelClass = styles[`headingLevel${Math.min(Math.max(level, 1), 3)}`] ?? styles.headingLevel2;
  return (
    <div
      className={`${styles.textBlockShell} ${styles.textBlockShellHeading}`}
      role="button"
      tabIndex={0}
      data-heading-level={level}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit();
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onStartEdit();
        }
      }}
    >
      <Tag className={`${styles.headingText} ${levelClass}`}>
        {text || <span className={styles.blockPlaceholder}>{placeholder}</span>}
      </Tag>
    </div>
  );
};

const normalizeEditorText = (value: string) => value.replace(/\r\n?/g, '\n');

const ParagraphEditor: React.FC<{
  content: ParagraphBlockContent | HeadingBlockContent;
  editorRef?: React.RefObject<HTMLElement | null>;
  onChange: (text: string) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
  onInsertBlock?: InsertBlockHandler;
  onTransformBlock?: (kind: BlockKind, content: BlockContent) => void;
  blockKind: BlockKind;
  headingLevel?: 1 | 2 | 3;
  onDeleteEmptyBlock?: () => void;
  enableAdvancedEditing?: boolean;
}> = ({
  content,
  editorRef,
  onChange,
  onSave,
  onExitEdit,
  onCancelEdit,
  onInsertBlock,
  onTransformBlock,
  blockKind,
  headingLevel = 2,
  onDeleteEmptyBlock,
  enableAdvancedEditing = true,
}) => {
  const advancedEditingEnabled = enableAdvancedEditing !== false;
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const fallbackRef = React.useRef<HTMLElement | null>(null);
  const mergedEditorRef = editorRef ?? fallbackRef;
  const slashAnchorRef = React.useRef<Range | null>(null);
  const pendingSlashAnchorRef = React.useRef<Range | null>(null);
  const [slashState, setSlashState] = React.useState<{
    query: string;
    caret: { top: number; left: number } | null;
  } | null>(null);
  const [slashIndex, setSlashIndex] = React.useState(0);

  const readEditorText = React.useCallback(() => normalizeEditorText(mergedEditorRef.current?.innerText ?? ''), [mergedEditorRef]);

  const getSelectionRange = React.useCallback(() => {
    const editorElement = mergedEditorRef.current;
    if (!editorElement) {
      return null;
    }
    const selection = getSelectionWithin(editorElement);
    if (!selection || selection.rangeCount === 0) {
      return null;
    }
    const range = selection.getRangeAt(0);
    if (!editorElement.contains(range.startContainer) || !editorElement.contains(range.endContainer)) {
      return null;
    }
    return range;
  }, [mergedEditorRef]);

  const computeCaretRect = React.useCallback((range: Range) => {
    const container = containerRef.current;
    if (!container) return { top: 0, left: 0 };
    const rects = range.getClientRects();
    const caretRect = rects.length > 0 ? rects[rects.length - 1] : range.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    const top = (caretRect?.bottom ?? containerRect.top) - containerRect.top + 4;
    const left = (caretRect?.left ?? containerRect.left) - containerRect.left + 4;
    return { top, left };
  }, []);

  const closeSlashMenu = React.useCallback(() => {
    slashAnchorRef.current = null;
    pendingSlashAnchorRef.current = null;
    setSlashState(null);
    setSlashIndex(0);
  }, []);

  const updateSlashState = React.useCallback(
    (explicitRange?: Range | null, options?: { resetIndex?: boolean }) => {
      const anchor = slashAnchorRef.current;
      const editorElement = mergedEditorRef.current;
      if (!anchor || !editorElement) {
        closeSlashMenu();
        return false;
      }
      const caretRange = explicitRange ?? getSelectionRange();
      if (!caretRange) {
        closeSlashMenu();
        return false;
      }
      const commandRange = anchor.cloneRange();
      try {
        commandRange.setEnd(caretRange.endContainer, caretRange.endOffset);
      } catch (error) {
        closeSlashMenu();
        return false;
      }
      const raw = commandRange.toString();
      if (!raw.startsWith('/')) {
        closeSlashMenu();
        return false;
      }
      const query = raw.slice(1);
      if (/\s/.test(query)) {
        closeSlashMenu();
        return false;
      }
      const caret = computeCaretRect(caretRange);
      setSlashState({ query, caret });
      if (options?.resetIndex) {
        setSlashIndex(0);
      }
      return true;
    },
    [closeSlashMenu, computeCaretRect, getSelectionRange, mergedEditorRef]
  );

  React.useEffect(() => {
    const editorElement = mergedEditorRef.current;
    if (!editorElement) return;
    const nextValue = normalizeEditorText(content?.text ?? '');
    if (normalizeEditorText(editorElement.innerText ?? '') !== nextValue) {
      editorElement.innerText = nextValue;
    }
  }, [content?.text, mergedEditorRef]);

  React.useEffect(() => {
    if (!slashState) return;
    const handleSelectionChange = () => {
      requestAnimationFrame(() => {
        updateSlashState();
      });
    };
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, [slashState, updateSlashState]);

  const slashCommands = React.useMemo<SlashCommandConfig[]>(() => (advancedEditingEnabled ? SLASH_COMMANDS : []), [advancedEditingEnabled]);

  const slashItems = React.useMemo(() => {
    if (!advancedEditingEnabled) {
      return [];
    }
    const query = slashState?.query?.toLowerCase() ?? '';
    if (!query) return slashCommands;
    return slashCommands.filter((item) => item.keywords.some((keyword) => keyword.toLowerCase().includes(query)));
  }, [advancedEditingEnabled, slashCommands, slashState?.query]);

  React.useEffect(() => {
    if (slashIndex >= slashItems.length && slashItems.length > 0) {
      setSlashIndex(0);
    }
  }, [slashIndex, slashItems.length]);

  const emitTransform = React.useCallback(
    (target: { type: 'paragraph' | 'heading'; level?: 1 | 2 | 3; text: string }) => {
      if (!advancedEditingEnabled || !onTransformBlock) {
        return;
      }
      if (target.type === 'paragraph') {
        onTransformBlock('paragraph', { text: target.text });
        return;
      }
      onTransformBlock('heading', { level: target.level ?? headingLevel, text: target.text } as HeadingBlockContent);
    },
    [advancedEditingEnabled, headingLevel, onTransformBlock]
  );

  const getCaretMetrics = React.useCallback(() => {
    const value = readEditorText();
    const selection = getSelectionRange();
    if (!selection || !mergedEditorRef.current) {
      return { value, caretOffset: null as number | null, selectionCollapsed: selection?.collapsed ?? false };
    }
    const preRange = selection.cloneRange();
    preRange.selectNodeContents(mergedEditorRef.current);
    preRange.setEnd(selection.startContainer, selection.startOffset);
    const caretOffset = preRange.toString().length;
    return { value, caretOffset, selectionCollapsed: selection.collapsed };
  }, [getSelectionRange, mergedEditorRef, readEditorText]);

  const handleSlashSelection = React.useCallback(
    (item: SlashCommandConfig) => {
      if (!advancedEditingEnabled) {
        return;
      }
      const editorElement = mergedEditorRef.current;
      if (!editorElement) {
        closeSlashMenu();
        return;
      }
      const selectionRange = getSelectionRange();
      const anchor = slashAnchorRef.current;
      if (!selectionRange || !anchor) {
        closeSlashMenu();
        return;
      }
      const removalRange = anchor.cloneRange();
      removalRange.setEnd(selectionRange.endContainer, selectionRange.endOffset);
      removalRange.deleteContents();
      const selection = editorElement ? getSelectionWithin(editorElement) : null;
      if (selection) {
        selection.removeAllRanges();
        const collapsed = anchor.cloneRange();
        collapsed.collapse(true);
        selection.addRange(collapsed);
      }
      slashAnchorRef.current = null;
      const nextValue = readEditorText();
      onChange(nextValue);
      closeSlashMenu();
      if (item.action.type === 'insert') {
        onInsertBlock?.('after', item.action.kind, 'slash-command', { headingLevel: item.action.headingLevel });
      } else {
        emitTransform({ type: item.action.target, level: item.action.headingLevel, text: nextValue });
      }
      requestAnimationFrame(() => editorElement.focus());
    },
    [advancedEditingEnabled, closeSlashMenu, emitTransform, getSelectionRange, mergedEditorRef, onChange, onInsertBlock, readEditorText]
  );

  const handleInput = (event: React.FormEvent<HTMLElement>) => {
    const element = event.currentTarget;
    const nextValue = normalizeEditorText(element.innerText ?? '');
    if (!nextValue && element.innerHTML !== '') {
      element.innerHTML = '';
    }
    onChange(nextValue);
    if (!advancedEditingEnabled) {
      return;
    }
    if (pendingSlashAnchorRef.current) {
      slashAnchorRef.current = pendingSlashAnchorRef.current;
      pendingSlashAnchorRef.current = null;
      updateSlashState(undefined, { resetIndex: true });
      return;
    }
    if (advancedEditingEnabled && slashState) {
      updateSlashState(undefined, { resetIndex: true });
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    pendingSlashAnchorRef.current = null;
    const hasModifier = event.ctrlKey || event.metaKey || event.altKey;
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      onSave();
      return;
    }

    const { value, caretOffset, selectionCollapsed } = getCaretMetrics();
    const trimmedValue = value.trim();

    if (
      advancedEditingEnabled &&
      event.key === 'Backspace' &&
      !event.shiftKey &&
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      selectionCollapsed &&
      caretOffset !== null &&
      caretOffset === 0 &&
      trimmedValue.length === 0 &&
      onDeleteEmptyBlock
    ) {
      event.preventDefault();
      closeSlashMenu();
      onDeleteEmptyBlock();
      return;
    }

    if (
      event.key === 'Enter' &&
      !event.shiftKey &&
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      (blockKind === 'paragraph' || blockKind === 'heading') &&
      onInsertBlock
    ) {
      if (selectionCollapsed && caretOffset !== null && caretOffset === value.length) {
        event.preventDefault();
        closeSlashMenu();
        void onSave();
        const currentEditor = mergedEditorRef.current;
        onInsertBlock('after', 'paragraph', 'enter-key');
        if (currentEditor) {
          requestAnimationFrame(() => currentEditor.focus());
        }
        return;
      }
    }

    if (advancedEditingEnabled) {
      const applyHeadingShortcut = (level: 1 | 2 | 3) => {
        event.preventDefault();
        emitTransform({ type: 'heading', level, text: value });
      };

      if ((event.ctrlKey || event.metaKey) && event.altKey) {
        if (event.key === '1') {
          applyHeadingShortcut(1);
          return;
        }
        if (event.key === '2') {
          applyHeadingShortcut(2);
          return;
        }
        if (event.key === '3') {
          applyHeadingShortcut(3);
          return;
        }
      }

      if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key === '0') {
        event.preventDefault();
        emitTransform({ type: 'paragraph', text: value });
        return;
      }
    }

    if (advancedEditingEnabled && slashState) {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        const delta = event.key === 'ArrowDown' ? 1 : -1;
        setSlashIndex((current) => {
          if (slashItems.length === 0) return 0;
          const next = (current + delta + slashItems.length) % slashItems.length;
          return next;
        });
        return;
      }
      if (event.key === 'Enter') {
        if (slashItems[slashIndex]) {
          event.preventDefault();
          handleSlashSelection(slashItems[slashIndex]);
          return;
        }
      }
      if (event.key === 'Escape') {
        event.preventDefault();
        closeSlashMenu();
        return;
      }
    }

    if (advancedEditingEnabled && !slashState && !hasModifier && event.key === '/') {
      const selection = getSelectionRange();
      if (selection && selection.collapsed && caretOffset !== null) {
        const prevChar = value[caretOffset - 1];
        if (!prevChar || /\s/.test(prevChar)) {
          pendingSlashAnchorRef.current = selection.cloneRange();
        }
      }
    }

    if (event.key === 'Escape') {
      if (advancedEditingEnabled && slashState) {
        event.preventDefault();
        closeSlashMenu();
        return;
      }
      if (!slashState) {
        event.preventDefault();
        onCancelEdit();
        return;
      }
    }

    if (
      advancedEditingEnabled &&
      event.key === ' ' &&
      !event.shiftKey &&
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      caretOffset !== null
    ) {
      const lineStart = value.lastIndexOf('\n', caretOffset - 1) + 1;
      const prefix = value.slice(lineStart, caretOffset);
      if (/^#{1,3}$/.test(prefix)) {
        event.preventDefault();
        const remaining = value.slice(0, lineStart) + value.slice(caretOffset);
        onChange(remaining);
        emitTransform({ type: 'heading', level: prefix.length as 1 | 2 | 3, text: remaining });
        closeSlashMenu();
        return;
      }

      const applyListTransform = (targetKind: BlockKind) => {
        if (!onTransformBlock) return;
        const remaining = value.slice(0, lineStart) + value.slice(caretOffset);
        onChange(remaining);
        closeSlashMenu();
        if (targetKind === 'todo_list') {
          onTransformBlock('todo_list', {
            items: [{ id: generateBlockScopedId(), text: '', checked: false }],
          } as TodoListBlockContent);
          return;
        }
        onTransformBlock(targetKind, { items: [''] } as ListBlockContent);
      };

      const applyQuoteTransform = () => {
        if (!onTransformBlock) return;
        const remaining = value.slice(0, lineStart) + value.slice(caretOffset);
        onChange(remaining);
        closeSlashMenu();
        onTransformBlock('quote', { text: '', source: '' } as QuoteBlockContent);
      };

      if (/^[-*]$/.test(prefix.trim())) {
        event.preventDefault();
        applyListTransform('bulleted_list');
        return;
      }

      if (prefix.trim() === '[]') {
        event.preventDefault();
        applyListTransform('todo_list');
        return;
      }

      if (/^\d+\.$/.test(prefix.trim())) {
        event.preventDefault();
        applyListTransform('numbered_list');
        return;
      }

      if (prefix.trim() === '>') {
        event.preventDefault();
        applyQuoteTransform();
        return;
      }
    }
  };

  const normalizedHeadingLevel = Math.min(Math.max(headingLevel, 1), 3) as 1 | 2 | 3;
  const placeholderText = blockKind === 'heading' ? `H${normalizedHeadingLevel} 标题...` : '写点什么...';
  const normalizedContentValue = normalizeEditorText(content?.text ?? '');
  const isEditorEmpty = normalizedContentValue.length === 0;
  const baseClassNames = [styles.inlineEditable];
  if (blockKind === 'heading') {
    const headingLevelKey = (`headingLevel${normalizedHeadingLevel}`) as 'headingLevel1' | 'headingLevel2' | 'headingLevel3';
    const headingLevelClass = styles[headingLevelKey] ?? styles.headingLevel2;
    baseClassNames.push(
      styles.inlineEditableHeading,
      styles.headingText,
      headingLevelClass
    );
  } else {
    baseClassNames.push(styles.inlineEditableParagraph);
  }
  const editorClassName = baseClassNames.join(' ');
  const EditableTag = (blockKind === 'heading'
    ? (['h1', 'h2', 'h3'][normalizedHeadingLevel - 1] ?? 'h2')
    : 'div') as keyof JSX.IntrinsicElements;
  const assignEditableRef = React.useCallback((node: HTMLElement | null) => {
    (mergedEditorRef as React.MutableRefObject<HTMLElement | null>).current = node;
  }, [mergedEditorRef]);
  const editableElement = React.createElement(EditableTag, {
    ref: assignEditableRef as React.Ref<HTMLElement>,
    className: editorClassName,
    contentEditable: true,
    suppressContentEditableWarning: true,
    role: 'textbox',
    'aria-multiline': true,
    spellCheck: false,
    'data-placeholder': placeholderText,
    'data-heading-level': blockKind === 'heading' ? normalizedHeadingLevel : undefined,
    'data-empty': isEditorEmpty ? 'true' : 'false',
    onInput: handleInput,
    onKeyDown: handleKeyDown,
    onClick: (event: React.MouseEvent<HTMLElement>) => event.stopPropagation(),
    onBlur: async () => {
      closeSlashMenu();
      await onSave();
      onExitEdit();
    },
  });

  return (
    <div
      className={`${styles.paragraphEditor} ${styles.textBlockShell} ${
        blockKind === 'heading' ? styles.textBlockShellHeading : styles.textBlockShellParagraph
      } ${styles.textBlockShellEditing}`}
      ref={containerRef}
      data-kind={blockKind}
      data-heading-level={blockKind === 'heading' ? normalizedHeadingLevel : undefined}
      data-empty={isEditorEmpty ? 'true' : 'false'}
    >
      <div className={styles.textBlockContent} data-empty={isEditorEmpty ? 'true' : 'false'}>
        {editableElement}
      </div>
      {advancedEditingEnabled && slashState && (
        <div
          className={styles.slashMenu}
          style={{ top: slashState.caret?.top ?? 0, left: slashState.caret?.left ?? 0 }}
          role="listbox"
          aria-label="块插入命令"
        >
          {slashItems.length === 0 ? (
            <div className={styles.slashMenuEmpty}>没有匹配的块类型</div>
          ) : (
            slashItems.map((item, index) => (
              <button
                key={item.id}
                type="button"
                className={`${styles.slashMenuItem} ${index === slashIndex ? styles.slashMenuItemActive : ''}`}
                onMouseDown={(event) => {
                  event.preventDefault();
                  handleSlashSelection(item);
                }}
              >
                <div className={styles.slashMenuItemBody}>
                  <span className={styles.slashMenuItemLabel}>{item.label}</span>
                  {item.description && (
                    <span className={styles.slashMenuItemDescription}>{item.description}</span>
                  )}
                </div>
                <span className={styles.slashMenuItemHint}>{item.hint ?? item.keywords[0]}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};

const TodoListDisplay: React.FC<{
  blockId: string;
  content: TodoListBlockContent;
  onToggleItem: (id: string, checked: boolean) => void;
  onStartEdit: () => void;
}> = ({ blockId, content, onToggleItem, onStartEdit }) => {
  const items = Array.isArray(content?.items) ? content.items : [];
  return (
    <div className={styles.todoList} role="group" aria-label="Todo 列表">
    <div className={styles.todoListHeader}>
      <span className={styles.todoListLabel}>Todo</span>
      <button type="button" className={styles.todoEditButton} onClick={(event) => { event.stopPropagation(); onStartEdit(); }}>
        编辑列表
      </button>
    </div>
      {items.map((item) => (
      <label key={`${blockId}-${item.id}`} className={styles.todoItem}>
        <input
          type="checkbox"
          checked={Boolean(item.checked)}
          onChange={(event) => onToggleItem(item.id ?? '', event.target.checked)}
          onClick={(event) => event.stopPropagation()}
        />
        <span className={`${styles.todoText} ${item.checked ? styles.todoTextChecked : ''}`}>
          {item.text?.trim() ? item.text : '写点什么...'}
        </span>
        {item.isPromoted && <span className={styles.todoBadge}>提升</span>}
      </label>
    ))}
      {items.length === 0 && (
        <p className={styles.blockPlaceholder}>暂无待办，点击编辑添加</p>
      )}
    </div>
  );
};

const TodoListEditor: React.FC<{
  content: TodoListBlockContent;
  onChange: (next: TodoListBlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
}> = ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => {
  const items = Array.isArray(content?.items) ? content.items : [];
  const handleItemChange = (item: TodoListItemContent, patch: Partial<TodoListItemContent>) => {
    const nextItems = items.map((candidate) =>
      candidate.id === item.id ? { ...candidate, ...patch } : candidate
    );
    onChange({ ...content, items: nextItems });
  };

  const handleDelete = (item: TodoListItemContent) => {
    const nextItems = items.filter((candidate) => candidate.id !== item.id);
    onChange({ ...content, items: nextItems });
  };

  const handleAdd = () => {
    const nextItem: TodoListItemContent = {
      id: generateBlockScopedId(),
      text: '',
      checked: false,
    };
    onChange({ ...content, items: [...items, nextItem] });
  };

  const handleSave = async () => {
    await onSave();
    onExitEdit();
  };

  return (
    <div className={styles.todoEditor}>
      {items.map((item, index) => (
        <div key={item.id ?? index} className={styles.todoEditorRow}>
          <input
            type="checkbox"
            checked={Boolean(item.checked)}
            onChange={(event) => handleItemChange(item, { checked: event.target.checked })}
          />
          <input
            type="text"
            value={item.text ?? ''}
            placeholder="输入待办内容"
            className={styles.todoEditorInput}
            onChange={(event) => handleItemChange(item, { text: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                handleAdd();
              }
              if (event.key === 'Escape') {
                event.preventDefault();
                onCancelEdit();
              }
            }}
          />
          <button
            type="button"
            className={`${styles.iconButton} ${item.isPromoted ? styles.todoPromoteActive : ''}`}
            onClick={() => handleItemChange(item, { isPromoted: !item.isPromoted })}
            aria-label="提升到书籍 TODO"
          >
            <Star size={16} />
          </button>
          <button
            type="button"
            className={`${styles.iconButton} ${styles.deleteIconButton}`}
            onClick={() => handleDelete(item)}
            aria-label="删除待办"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
      <button type="button" className={styles.todoAddButton} onClick={handleAdd}>
        <Plus size={16} /> 新增待办
      </button>
      <div className={styles.editorActions}>
        <button type="button" className={styles.primaryActionButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryActionButton} onClick={onCancelEdit}>
          取消
        </button>
      </div>
    </div>
  );
};

const CALLOUT_VARIANTS: Record<NonNullable<CalloutBlockContent['variant']>, {
  label: string;
  icon: React.ReactNode;
}> = {
  info: { label: '信息', icon: <Info size={18} /> },
  warning: { label: '提醒', icon: <AlertTriangle size={18} /> },
  danger: { label: '风险', icon: <AlertTriangle size={18} /> },
  success: { label: '成功', icon: <CheckCircle2 size={18} /> },
};

const CalloutDisplay: React.FC<{ content: CalloutBlockContent; onStartEdit: () => void }> = ({ content, onStartEdit }) => {
  const tone = content.variant ?? 'info';
  const meta = CALLOUT_VARIANTS[tone];
  return (
    <div
      className={`${styles.callout} ${styles[`callout${tone.charAt(0).toUpperCase() + tone.slice(1)}`] ?? ''}`}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit();
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onStartEdit();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className={styles.calloutIcon}>{meta?.icon ?? <Info size={18} />}</div>
      <div className={styles.calloutBody}>
        <p>{content.text || '暂无内容'}</p>
      </div>
    </div>
  );
};

const CalloutEditor: React.FC<{
  content: CalloutBlockContent;
  onChange: (next: CalloutBlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
}> = ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => {
  const handleSave = async () => {
    await onSave();
    onExitEdit();
  };
  return (
    <div className={styles.calloutEditor}>
      <div className={styles.calloutVariantList}>
        {(Object.keys(CALLOUT_VARIANTS) as Array<NonNullable<CalloutBlockContent['variant']>>).map((variant) => (
          <button
            key={variant}
            type="button"
            className={`${styles.calloutVariantButton} ${content.variant === variant ? styles.calloutVariantButtonActive : ''}`}
            onClick={() => onChange({ ...content, variant })}
          >
            {CALLOUT_VARIANTS[variant].label}
          </button>
        ))}
      </div>
      <textarea
        className={styles.calloutTextarea}
        value={content.text ?? ''}
        placeholder="输入需要强调的内容"
        onChange={(event) => onChange({ ...content, text: event.target.value })}
      />
      <div className={styles.editorActions}>
        <button type="button" className={styles.primaryActionButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryActionButton} onClick={onCancelEdit}>
          取消
        </button>
      </div>
    </div>
  );
};

const QuoteDisplay: React.FC<{ content: QuoteBlockContent; onStartEdit: () => void }> = ({ content, onStartEdit }) => (
  <div
    className={styles.quoteBlock}
    onClick={(event) => { event.stopPropagation(); onStartEdit(); }}
    onKeyDown={(event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onStartEdit();
      }
    }}
    role="button"
    tabIndex={0}
  >
    <blockquote>
      <p>“{content.text || '引用内容'}”</p>
      {content.source && <cite>— {content.source}</cite>}
    </blockquote>
  </div>
);

const QuoteEditor: React.FC<{
  content: QuoteBlockContent;
  onChange: (next: QuoteBlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
}> = ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => {
  const handleSave = async () => {
    await onSave();
    onExitEdit();
  };
  return (
    <div className={styles.quoteEditor}>
      <textarea
        className={styles.quoteTextarea}
        value={content.text ?? ''}
        placeholder="引用内容"
        onChange={(event) => onChange({ ...content, text: event.target.value })}
      />
      <input
        type="text"
        value={content.source ?? ''}
        placeholder="来源（可选）"
        className={styles.quoteSourceInput}
        onChange={(event) => onChange({ ...content, source: event.target.value })}
      />
      <div className={styles.editorActions}>
        <button type="button" className={styles.primaryActionButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryActionButton} onClick={onCancelEdit}>
          取消
        </button>
      </div>
    </div>
  );
};

const DividerDisplay: React.FC<{ content: DividerBlockContent }> = ({ content }) => (
  <div className={styles.dividerBlock}>
    <span className={content.style === 'dashed' ? styles.dividerDashed : styles.dividerSolid} />
  </div>
);

const DividerEditor: React.FC<{
  content: DividerBlockContent;
  onChange: (next: DividerBlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
}> = ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => {
  const handleSave = async () => {
    await onSave();
    onExitEdit();
  };
  return (
    <div className={styles.dividerEditor}>
      <label className={styles.dividerOption}>
        <input
          type="radio"
          checked={!content.style || content.style === 'solid'}
          onChange={() => onChange({ style: 'solid' })}
        />
        实线
      </label>
      <label className={styles.dividerOption}>
        <input
          type="radio"
          checked={content.style === 'dashed'}
          onChange={() => onChange({ style: 'dashed' })}
        />
        虚线
      </label>
      <div className={styles.editorActions}>
        <button type="button" className={styles.primaryActionButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryActionButton} onClick={onCancelEdit}>
          取消
        </button>
      </div>
    </div>
  );
};

const ImageBlockDisplay: React.FC<{ content: ImageBlockContent; onStartEdit: () => void }> = ({ content, onStartEdit }) => (
  <div className={styles.imageBlock}>
    {content.url ? (
      <button
        type="button"
        className={styles.imageButton}
        onClick={(event) => {
          event.stopPropagation();
          onStartEdit();
        }}
      >
        <img src={content.url} alt={content.caption || '图片块'} />
      </button>
    ) : (
      <button type="button" className={styles.imagePlaceholder} onClick={(event) => { event.stopPropagation(); onStartEdit(); }}>
        <ImageIcon size={18} /> 选择图片
      </button>
    )}
    {content.caption && <p className={styles.imageCaption}>{content.caption}</p>}
  </div>
);

const ImageBlockEditor: React.FC<{
  content: ImageBlockContent;
  onChange: (next: ImageBlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
}> = ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => {
  const handleSave = async () => {
    await onSave();
    onExitEdit();
  };
  return (
    <div className={styles.imageEditor}>
      <label className={styles.imageField}>
        图片 URL
        <input
          type="url"
          value={content.url ?? ''}
          placeholder="https://example.com/image.jpg"
          onChange={(event) => onChange({ ...content, url: event.target.value })}
        />
      </label>
      <label className={styles.imageField}>
        Caption
        <input
          type="text"
          value={content.caption ?? ''}
          placeholder="图片说明"
          onChange={(event) => onChange({ ...content, caption: event.target.value })}
        />
      </label>
      <div className={styles.editorActions}>
        <button type="button" className={styles.primaryActionButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryActionButton} onClick={onCancelEdit}>
          取消
        </button>
      </div>
    </div>
  );
};

const ImageGalleryDisplay: React.FC<{ content: ImageGalleryBlockContent; onStartEdit: () => void }> = ({ content, onStartEdit }) => {
  const items = Array.isArray(content?.items) ? content.items : [];
  return (
    <div
      className={`${styles.imageGallery} ${content.layout === 'grid' ? styles.imageGalleryGrid : styles.imageGalleryStrip}`}
      onClick={(event) => { event.stopPropagation(); onStartEdit(); }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onStartEdit();
        }
      }}
      role="button"
      tabIndex={0}
    >
      {items.length === 0 ? (
        <span className={styles.blockPlaceholder}>暂无图片，点击编辑添加</span>
      ) : (
        items.map((item, index) => (
          <figure key={item.id ?? index} className={styles.imageGalleryItem}>
            {item.url ? <img src={item.url} alt={item.caption || '图片'} /> : <div className={styles.imagePlaceholder}><ImageIcon size={16} /></div>}
            {(item.caption || item.indexLabel) && (
              <figcaption>
                {item.indexLabel && <strong>{item.indexLabel}</strong>}
                {item.caption && <span>{item.caption}</span>}
              </figcaption>
            )}
          </figure>
        ))
      )}
    </div>
  );
};

const ImageGalleryEditor: React.FC<{
  content: ImageGalleryBlockContent;
  onChange: (next: ImageGalleryBlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
}> = ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => {
  const items = Array.isArray(content?.items) ? content.items : [];
  const handleAdd = () => {
    const nextItem = { id: generateBlockScopedId(), url: '', caption: '' };
    onChange({ ...content, items: [...items, nextItem] });
  };

  const handleItemChange = (targetId: string, patch: Partial<ImageGalleryBlockContent['items'][number]>) => {
    const nextItems = items.map((item) =>
      item.id === targetId ? { ...item, ...patch } : item
    );
    onChange({ ...content, items: nextItems });
  };

  const handleDelete = (targetId: string) => {
    onChange({ ...content, items: items.filter((item) => item.id !== targetId) });
  };

  const handleSave = async () => {
    await onSave();
    onExitEdit();
  };

  return (
    <div className={styles.galleryEditor}>
      <div className={styles.galleryLayoutOptions}>
        <button
          type="button"
          className={`${styles.galleryLayoutButton} ${content.layout !== 'grid' ? styles.galleryLayoutButtonActive : ''}`}
          onClick={() => onChange({ ...content, layout: 'strip' })}
        >
          <List size={16} /> 条形
        </button>
        <button
          type="button"
          className={`${styles.galleryLayoutButton} ${content.layout === 'grid' ? styles.galleryLayoutButtonActive : ''}`}
          onClick={() => onChange({ ...content, layout: 'grid' })}
        >
          <Grid size={16} /> 网格
        </button>
        {content.layout === 'grid' && (
          <label className={styles.galleryGridField}>
            每行数量
            <input
              type="number"
              min={2}
              max={6}
              value={content.maxPerRow ?? 3}
              onChange={(event) => onChange({ ...content, maxPerRow: Number(event.target.value) || 3 })}
            />
          </label>
        )}
      </div>
      {items.map((item, index) => (
        <div key={item.id ?? index} className={styles.galleryEditorRow}>
          <input
            type="url"
            value={item.url ?? ''}
            placeholder="图片 URL"
            onChange={(event) => handleItemChange(item.id ?? '', { url: event.target.value })}
          />
          <input
            type="text"
            value={item.caption ?? ''}
            placeholder="说明"
            onChange={(event) => handleItemChange(item.id ?? '', { caption: event.target.value })}
          />
          <input
            type="text"
            value={item.indexLabel ?? ''}
            placeholder="序号标签"
            onChange={(event) => handleItemChange(item.id ?? '', { indexLabel: event.target.value })}
          />
          <button type="button" className={`${styles.iconButton} ${styles.deleteIconButton}`} onClick={() => handleDelete(item.id ?? '')}>
            <Trash2 size={16} />
          </button>
        </div>
      ))}
      <button type="button" className={styles.todoAddButton} onClick={handleAdd}>
        <Plus size={16} /> 添加图片
      </button>
      <div className={styles.editorActions}>
        <button type="button" className={styles.primaryActionButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryActionButton} onClick={onCancelEdit}>
          取消
        </button>
      </div>
    </div>
  );
};

const UnsupportedBlock: React.FC<{ kind: BlockDto['kind'] }> = ({ kind }) => (
  <div className={styles.blockDisplay}>
    <span className={styles.blockPlaceholder}>暂不支持 {kind} 类型</span>
  </div>
);

const ensureBlockPluginsRegistered = (() => {
  let installed = false;
  return () => {
    if (installed) return;
    installed = true;

    registerBlockPlugin({
      kind: 'paragraph',
      Display: ({ block, content, onStartEdit }) => (
        <ParagraphDisplay blockId={block.id} content={content as ParagraphBlockContent} onStartEdit={onStartEdit} />
      ),
      Editor: ({ content, editorRef, onChange, onSave, onExitEdit, onCancelEdit, onInsertBlock, onTransformBlock, onDeleteBlock }) => (
        <ParagraphEditor
          content={content as ParagraphBlockContent}
          editorRef={editorRef}
          onChange={(text) => onChange({ text })}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
          onInsertBlock={onInsertBlock}
          onTransformBlock={onTransformBlock}
          blockKind="paragraph"
          onDeleteEmptyBlock={onDeleteBlock}
          enableAdvancedEditing={false}
        />
      ),
      createDefaultContent: () => ({ text: '' }),
    });

    registerBlockPlugin({
      kind: 'heading',
      Display: ({ content, onStartEdit }) => (
        <HeadingDisplay content={content as HeadingBlockContent} onStartEdit={onStartEdit} />
      ),
      Editor: ({ block, content, editorRef, onChange, onSave, onExitEdit, onCancelEdit, onInsertBlock, onTransformBlock, onDeleteBlock }) => {
        const headingContent = content as HeadingBlockContent;
        return (
          <ParagraphEditor
            content={headingContent}
            editorRef={editorRef}
            onChange={(text) => onChange({ ...headingContent, text })}
            onSave={onSave}
            onExitEdit={onExitEdit}
            onCancelEdit={onCancelEdit}
            onInsertBlock={onInsertBlock}
            onTransformBlock={onTransformBlock}
            blockKind={block.kind}
            headingLevel={headingContent.level}
            onDeleteEmptyBlock={onDeleteBlock}
            enableAdvancedEditing={false}
          />
        );
      },
      createDefaultContent: () => ({ text: '', level: 2 }),
    });

    registerBlockPlugin({
      kind: 'todo_list',
      Display: ({ block, content, onStartEdit, onChange, onQuickSave }) => (
        <TodoListDisplay
          blockId={block.id}
          content={content as TodoListBlockContent}
          onToggleItem={(itemId, checked) => {
            const source = content as TodoListBlockContent;
            const nextItems = source.items.map((item) =>
              item.id === itemId ? { ...item, checked } : item
            );
            onChange({ ...source, items: nextItems });
            void onQuickSave?.();
          }}
          onStartEdit={onStartEdit}
        />
      ),
      Editor: ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => (
        <TodoListEditor
          content={content as TodoListBlockContent}
          onChange={(next) => onChange(next)}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
        />
      ),
      createDefaultContent: () => ({ items: [] }),
    });

    registerBlockPlugin({
      kind: 'callout',
      Display: ({ content, onStartEdit }) => (
        <CalloutDisplay content={content as CalloutBlockContent} onStartEdit={onStartEdit} />
      ),
      Editor: ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => (
        <CalloutEditor
          content={content as CalloutBlockContent}
          onChange={(next) => onChange(next)}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
        />
      ),
      createDefaultContent: () => ({ text: '', variant: 'info' }),
    });

    registerBlockPlugin({
      kind: 'quote',
      Display: ({ content, onStartEdit }) => (
        <QuoteDisplay content={content as QuoteBlockContent} onStartEdit={onStartEdit} />
      ),
      Editor: ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => (
        <QuoteEditor
          content={content as QuoteBlockContent}
          onChange={(next) => onChange(next)}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
        />
      ),
      createDefaultContent: () => ({ text: '', source: '' }),
    });

    registerBlockPlugin({
      kind: 'divider',
      Display: ({ content }) => <DividerDisplay content={content as DividerBlockContent} />,
      Editor: ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => (
        <DividerEditor
          content={content as DividerBlockContent}
          onChange={(next) => onChange(next)}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
        />
      ),
      createDefaultContent: () => ({}),
    });

    registerBlockPlugin({
      kind: 'image',
      Display: ({ content, onStartEdit }) => (
        <ImageBlockDisplay content={content as ImageBlockContent} onStartEdit={onStartEdit} />
      ),
      Editor: ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => (
        <ImageBlockEditor
          content={content as ImageBlockContent}
          onChange={(next) => onChange(next)}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
        />
      ),
      createDefaultContent: () => ({ url: '', caption: '' }),
    });

    registerBlockPlugin({
      kind: 'image_gallery',
      Display: ({ content, onStartEdit }) => (
        <ImageGalleryDisplay content={content as ImageGalleryBlockContent} onStartEdit={onStartEdit} />
      ),
      Editor: ({ content, onChange, onSave, onExitEdit, onCancelEdit }) => (
        <ImageGalleryEditor
          content={content as ImageGalleryBlockContent}
          onChange={(next) => onChange(next)}
          onSave={onSave}
          onExitEdit={onExitEdit}
          onCancelEdit={onCancelEdit}
        />
      ),
      createDefaultContent: () => ({ layout: 'strip', items: [] }),
    });
  };
})();

ensureBlockPluginsRegistered();
