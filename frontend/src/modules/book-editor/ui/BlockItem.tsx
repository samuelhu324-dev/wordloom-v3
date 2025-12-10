'use client';

import React from 'react';
import type { BlockContent, BlockKind } from '@/entities/block';
import { serializeBlockContent } from '@/entities/block';
import { getBlockPlugin } from '../model/blockPlugins';
import { useScopedCaretTracker } from '../model/caret';
import { buildQuickInsertActions, type QuickInsertAction } from '../model/quickActions';
import { BlockToolbar } from './BlockToolbar';
import { SaveStatusBadge, SaveState } from './SaveStatusBadge';
import { UnsupportedBlock } from './UnsupportedBlock';
import { QuickInsertMenu } from './QuickInsertMenu';
import styles from './bookEditor.module.css';
import type { BlockEditorRenderable } from '../model/BlockEditorContext';
import { useBlockCommands, useBlockDeleteGuard } from '../model/blockCommands';
import { useBlockAutosaveMutation } from '../model/useBlockAutosaveMutation';
import { announceFocusIntent } from '../model/selectionStore';
import { getBlockEditorHandle } from '../model/editorRegistry';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';
import { isRenderableBlockEmpty } from '../model/isRenderableBlockEmpty';
import type { MarkdownShortcutRequest } from './ParagraphEditor';
import type { KeyboardContextInput } from '../model/keyboardDecider';
import { useI18n } from '@/i18n/useI18n';

const MARKDOWN_SHORTCUT_SOURCE_KINDS = new Set<BlockKind>(['paragraph', 'heading']);

type QuickMenuTrigger = 'slash' | 'plus';

interface QuickMenuState {
  anchorRect: DOMRect | null;
  trigger: QuickMenuTrigger;
}

interface BlockItemProps {
  block: BlockEditorRenderable;
  index: number;
  nextFractionalIndex?: string;
  autoFocus?: boolean;
  onAutoFocusComplete?: () => void;
  onBlockCreated?: (blockId: string) => void;
  onBlockDeleted?: (payload: { blockId: string; index: number }) => void;
  onRequestFocusAdjacent?: (options: { currentIndex: number; direction: 'prev' | 'next' }) => void;
  focusPosition?: 'start' | 'end';
  onRequestSlashMenu?: (payload: { blockId: string; onSelect: (action: QuickInsertAction) => void }) => void;
}

export const BlockItem: React.FC<BlockItemProps> = ({
  block,
  index,
  nextFractionalIndex,
  autoFocus,
  onAutoFocusComplete,
  onBlockCreated,
  onBlockDeleted,
  onRequestFocusAdjacent,
  focusPosition,
  onRequestSlashMenu,
}) => {
  const plugin = getBlockPlugin(block.kind);
  const updateMutation = useBlockAutosaveMutation(block.id);
  const { createBlock, transformBlock } = useBlockCommands();
  const deleteBlockWithGuard = useBlockDeleteGuard();
  const { t } = useI18n();
  const quickInsertActions = React.useMemo(() => buildQuickInsertActions(t), [t]);


  const [isEditing, setIsEditing] = React.useState(Boolean(autoFocus));
  const [draftContent, setDraftContent] = React.useState<BlockContent>(() => plugin?.normalize(block.content) ?? block.content);
  const draftRef = React.useRef<BlockContent>(draftContent);
  const lastSerializedRef = React.useRef<string>(serializeBlockContent(block.kind, block.content));
  const debounceRef = React.useRef<number | null>(null);
  const [saveState, setSaveState] = React.useState<SaveState>('idle');
  const pendingFlushRef = React.useRef(false);
  const hoverDelayRef = React.useRef<number | null>(null);
  const [hoverActive, setHoverActive] = React.useState(false);
  const blockRef = React.useRef<HTMLDivElement | null>(null);
  const caretRect = useScopedCaretTracker(Boolean(plugin?.prefersInlineShell && isEditing), blockRef);
  const [quickMenu, setQuickMenu] = React.useState<QuickMenuState | null>(null);
  const useDomShadowState = block.kind === 'paragraph' || block.kind === 'heading';

  React.useEffect(() => {
    setDraftContent(plugin?.normalize(block.content) ?? block.content);
    draftRef.current = plugin?.normalize(block.content) ?? block.content;
    lastSerializedRef.current = serializeBlockContent(block.kind, block.content);
  }, [block.content, block.kind, plugin]);

  React.useEffect(() => {
    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    pendingFlushRef.current = false;
    setSaveState('idle');
  }, [block.id, block.kind]);

  React.useEffect(() => {
    if (!autoFocus) return;
    setIsEditing(true);
    const frame = requestAnimationFrame(() => onAutoFocusComplete?.());
    return () => cancelAnimationFrame(frame);
  }, [autoFocus, onAutoFocusComplete]);

  const flushSave = React.useCallback(async () => {
    if (!pendingFlushRef.current) {
      return;
    }
    pendingFlushRef.current = false;
    setSaveState('saving');
    const serialized = serializeBlockContent(block.kind, draftRef.current);
    if (serialized === lastSerializedRef.current) {
      setSaveState('saved');
      return;
    }
    try {
      await updateMutation.mutateAsync({ content: serialized });
      lastSerializedRef.current = serialized;
      setSaveState('saved');
    } catch (error) {
      console.error('更新块失败', error);
      setSaveState('error');
    }
  }, [block.kind, updateMutation]);

  React.useEffect(() => () => {
    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }
    if (pendingFlushRef.current) {
      void flushSave();
    }
  }, [flushSave]);

  const scheduleSave = React.useCallback(() => {
    pendingFlushRef.current = true;
    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }
    debounceRef.current = window.setTimeout(() => {
      debounceRef.current = null;
      void flushSave();
    }, 300);
  }, [flushSave]);

  const handleChange = (next: BlockContent) => {
    draftRef.current = next;
    if (!useDomShadowState) {
      setDraftContent(next);
    }
    scheduleSave();
  };

  const pendingSlashFromKeyRef = React.useRef(false);

  const exitEdit = () => {
    setIsEditing(false);
    pendingSlashFromKeyRef.current = false;
    void flushSave();
  };

  const beginEdit = (request?: BlockEditorStartEditRequest) => {
    pendingSlashFromKeyRef.current = false;
    if (request?.source === 'key' && request.key === '/' && !request.shiftKey && block.kind === 'paragraph') {
      pendingSlashFromKeyRef.current = true;
    }
    setIsEditing(true);
  };

  const requestDelete = async (origin: 'keyboard' | 'menu' | 'toolbar' | 'system' = 'keyboard', options?: { silent?: boolean }) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[deleteGuard]', block.kind, {
        origin,
        isDraftEmpty: isRenderableBlockEmpty({ ...block, content: draftRef.current }),
      });
    }
    try {
      const result = await deleteBlockWithGuard({ blockId: block.id, intent: origin });
      if (result.status === 'deleted' && !options?.silent) {
        onBlockDeleted?.({ blockId: block.id, index });
      }
    } catch (error) {
      console.error('删除块失败', error);
    }
  };

  const insertionPosition = React.useMemo(() => {
    const base = { before: block.fractional_index };
    if (nextFractionalIndex) {
      return { ...base, after: nextFractionalIndex };
    }
    return { ...base, rank: index + 1 };
  }, [block.fractional_index, index, nextFractionalIndex]);

  const handleCreateBelow = async () => {
    try {
      await createBlock({
        position: insertionPosition,
        selectionEdge: 'start',
        onCreated: (id) => onBlockCreated?.(id),
      });
    } catch (error) {
      console.error('创建块失败', error);
    }
  };

  React.useEffect(() => () => {
    if (hoverDelayRef.current) {
      window.clearTimeout(hoverDelayRef.current);
    }
  }, []);

  React.useEffect(() => {
    if (!isEditing || !pendingSlashFromKeyRef.current) {
      return;
    }
    if (block.kind !== 'paragraph') {
      pendingSlashFromKeyRef.current = false;
      return;
    }
    pendingSlashFromKeyRef.current = false;
    const dispatchSlashEvent = () => {
      const editable = blockRef.current?.querySelector<HTMLElement>('[contenteditable="true"]');
      if (!editable) {
        return;
      }
      const handle = getBlockEditorHandle(block.id);
      handle?.focusAtEdge('start');
      editable.focus({ preventScroll: true });
      const slashEvent = new KeyboardEvent('keydown', {
        key: '/',
        code: 'Slash',
        bubbles: true,
        cancelable: true,
      });
      editable.dispatchEvent(slashEvent);
    };
    requestAnimationFrame(() => {
      requestAnimationFrame(dispatchSlashEvent);
    });
  }, [block.id, block.kind, isEditing]);

  React.useEffect(() => {
    if (!blockRef.current) return;
    if (!caretRect) {
      blockRef.current.style.removeProperty('--wl-inline-caret-top');
      blockRef.current.style.removeProperty('--wl-inline-caret-left');
      return;
    }
    blockRef.current.style.setProperty('--wl-inline-caret-top', `${caretRect.top + window.scrollY}px`);
    blockRef.current.style.setProperty('--wl-inline-caret-left', `${caretRect.left + window.scrollX}px`);
  }, [caretRect]);

  const handleSoftBreak = () => {
    // Plan161A：Shift+Enter 交由浏览器生成软换行，仍保留回调以便未来扩展。
  };

  const isDraftEmpty = React.useCallback(() => {
    return isRenderableBlockEmpty({ ...block, content: draftRef.current });
  }, [block]);

  const handleDeleteEmptyBlock = React.useCallback(() => {
    if (!isDraftEmpty()) {
      return;
    }
    void requestDelete('keyboard');
  }, [isDraftEmpty, requestDelete]);

  const handleFocusPrev = () => {
    onRequestFocusAdjacent?.({ currentIndex: index, direction: 'prev' });
  };

  const handleFocusNext = () => {
    onRequestFocusAdjacent?.({ currentIndex: index, direction: 'next' });
  };

  const openQuickMenu = (anchorRect: DOMRect | null, trigger: QuickMenuTrigger) => {
    const fallback = anchorRect ?? blockRef.current?.getBoundingClientRect() ?? null;
    setQuickMenu({ anchorRect: fallback, trigger });
  };

  const closeQuickMenu = () => setQuickMenu(null);

  const shouldSkipCaretCapture = (target: HTMLElement | null) => {
    if (!target) return true;
    if (target.closest('[data-block-toolbar="true"]')) return true;
    if (target.closest('button, a, input, textarea, [data-caret-skip="true"]')) return true;
    if (target.closest('[contenteditable="true"]')) return true;
    return false;
  };

  const handleBlockMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!plugin?.prefersInlineShell) {
      return;
    }
    if (event.defaultPrevented || event.button !== 0) {
      return;
    }
    const target = event.target as HTMLElement | null;
    if (shouldSkipCaretCapture(target)) {
      return;
    }
    const { clientX, clientY } = event;
    event.preventDefault();
    const editorHandle = getBlockEditorHandle(block.id);
    const pointerOffset = editorHandle?.getOffsetFromPoint?.(clientX, clientY);
    announceFocusIntent('pointer', block.id, {
      ttlMs: 600,
      payload: typeof pointerOffset === 'number' ? { offset: pointerOffset } : undefined,
      source: 'block-item.pointer',
    });

    const scheduleCaretPlacement = () => {
      requestAnimationFrame(() => {
        const handle = getBlockEditorHandle(block.id);
        handle?.focusFromPoint(clientX, clientY);
      });
    };

    if (!isEditing) {
      beginEdit();
      requestAnimationFrame(() => {
        requestAnimationFrame(scheduleCaretPlacement);
      });
    } else {
      scheduleCaretPlacement();
    }
  };

  const insertBlockOfKind = async (targetKind: BlockKind, override?: BlockContent) => {
    try {
      await createBlock({
        kind: targetKind,
        contentOverride: override,
        position: insertionPosition,
        selectionEdge: 'start',
        onCreated: (id) => onBlockCreated?.(id),
      });
    } catch (error) {
      console.error('创建块失败', error);
    }
  };

  const transformFromMarkdownShortcut = async (
    targetKind: BlockKind,
    options?: { skipEmptyCheck?: boolean; source?: string },
  ) => {
    if (block.kind === targetKind) {
      return;
    }
    if (!options?.skipEmptyCheck && !isDraftEmpty()) {
      return;
    }
    try {
      await transformBlock({
        blockId: block.id,
        targetKind,
        selectionEdge: 'start',
        source: options?.source ?? `block-item.transform.${targetKind}`,
      });
    } catch (error) {
      console.error('变形块失败', error);
    }
  };

  const handleQuickActionSelect = async (action: QuickInsertAction, triggerOverride?: QuickMenuTrigger) => {
    const trigger = triggerOverride ?? quickMenu?.trigger ?? 'plus';
    closeQuickMenu();
    const allowTransform =
      action.behavior === 'transform' && block.kind === 'paragraph' && isDraftEmpty();
    if (allowTransform) {
      await transformFromMarkdownShortcut(action.kind, { source: `quick-menu.${trigger}` });
      return;
    }
    await insertBlockOfKind(action.kind);
  };

  const handleMarkdownShortcut = async (request: MarkdownShortcutRequest) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[shortcut]', block.kind, request);
    }
    if (!MARKDOWN_SHORTCUT_SOURCE_KINDS.has(block.kind)) {
      return;
    }
    const skipCheck = request.cleared === true;
    if (!skipCheck && !isDraftEmpty()) {
      return;
    }
    await transformFromMarkdownShortcut(request.kind, {
      skipEmptyCheck: skipCheck,
      source: 'markdown-shortcut',
    });
  };

  const getKeyboardContext = React.useCallback((): KeyboardContextInput | null => {
    if (!MARKDOWN_SHORTCUT_SOURCE_KINDS.has(block.kind)) {
      return null;
    }
    return {
      blockKind: block.kind,
      isBlockEmpty: isDraftEmpty(),
    };
  }, [block.kind, isDraftEmpty]);

  const handleEditorSubmit = React.useCallback(async () => {
    const emptyParagraph = block.kind === 'paragraph' && isDraftEmpty();
    if (process.env.NODE_ENV !== 'production') {
      console.log('[block.submit]', {
        blockId: block.id,
        kind: block.kind,
        emptyParagraph,
      });
    }
    await flushSave();
    if (emptyParagraph) {
      exitEdit();
    }
    await handleCreateBelow();
  }, [block.id, block.kind, exitEdit, flushSave, handleCreateBelow, isDraftEmpty]);

  if (!plugin) {
    return <UnsupportedBlock kind={block.kind} />;
  }

  const display = (
    <plugin.Display
      block={block}
      content={draftContent}
      onStartEdit={beginEdit}
    />
  );

  const editor = (
    <plugin.Editor
      block={block}
      content={draftContent}
      autoFocus={autoFocus || isEditing}
      focusPosition={focusPosition}
      onChange={handleChange}
      onSubmit={handleEditorSubmit}
      getKeyboardContext={getKeyboardContext}
      onExitEdit={exitEdit}
      onSoftBreak={handleSoftBreak}
      onDeleteEmptyBlock={handleDeleteEmptyBlock}
      onFocusPrev={handleFocusPrev}
      onFocusNext={handleFocusNext}
      onRequestSlashMenu={
        block.kind === 'paragraph'
          ? () => {
              onRequestSlashMenu?.({
                blockId: block.id,
                onSelect: (action) => void handleQuickActionSelect(action, 'slash'),
              });
            }
          : undefined
      }
      onMarkdownShortcut={MARKDOWN_SHORTCUT_SOURCE_KINDS.has(block.kind) ? handleMarkdownShortcut : undefined}
      readOnly={plugin?.prefersInlineShell ? !isEditing : undefined}
      onStartEdit={plugin?.prefersInlineShell ? beginEdit : undefined}
    />
  );

  const mainContent = plugin?.prefersInlineShell ? editor : isEditing ? editor : display;

  const showActions = isEditing || hoverActive;

  const handleMouseEnter = () => {
    if (hoverDelayRef.current) {
      window.clearTimeout(hoverDelayRef.current);
    }
    hoverDelayRef.current = window.setTimeout(() => {
      setHoverActive(true);
      hoverDelayRef.current = null;
    }, 150);
  };

  const handleMouseLeave = () => {
    if (hoverDelayRef.current) {
      window.clearTimeout(hoverDelayRef.current);
      hoverDelayRef.current = null;
    }
    setHoverActive(false);
  };

  return (
    <div
      ref={blockRef}
      className={styles.blockItem}
      data-editing={isEditing ? 'true' : undefined}
      data-show-actions={showActions ? 'true' : undefined}
      data-kind={block.kind}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onMouseDown={handleBlockMouseDown}
    >
      <div className={styles.blockItemMain}>{mainContent}</div>
      <div className={styles.blockItemActions} aria-hidden={!showActions}>
        <BlockToolbar
          onOpenMenu={(anchorRect) => openQuickMenu(anchorRect, 'plus')}
          disabled={updateMutation.isPending}
        />
      </div>
      <SaveStatusBadge state={saveState} />
      {quickMenu && (
        <QuickInsertMenu
          anchorRect={quickMenu.anchorRect}
          actions={quickInsertActions}
            onSelect={(action) => void handleQuickActionSelect(action)}
          onClose={closeQuickMenu}
        />
      )}
    </div>
  );
};
