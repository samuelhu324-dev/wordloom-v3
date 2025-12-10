'use client';

import React from 'react';
import { BlockItem } from './BlockItem';
import { InlineCreateBar } from './InlineCreateBar';
import styles from './bookEditor.module.css';
import { useBlockEditorContext } from '../model/BlockEditorContext';
import { announceFocusIntent, focusIntentStore } from '../model/selectionStore';
import { SlashMenu } from './SlashMenu';
import { buildQuickInsertActions, type QuickInsertAction } from '../model/quickActions';
import { getSlashMenuAnchor } from '../model/getSlashMenuAnchor';
import { useI18n } from '@/i18n/useI18n';

interface BlockListProps {
  pendingFocusBlockId?: string | null;
  onPendingFocusConsumed?: () => void;
  onBlockCreated?: (blockId: string) => void;
  onBlockDeleted?: (blockId: string) => void;
}

export const BlockList: React.FC<BlockListProps> = ({
  pendingFocusBlockId,
  onPendingFocusConsumed,
  onBlockCreated,
  onBlockDeleted,
}) => {
  const { blocks } = useBlockEditorContext();
  const { t } = useI18n();
  const quickInsertActions = React.useMemo(() => buildQuickInsertActions(t), [t]);
  const [localFocus, setLocalFocus] = React.useState<{ id: string; position: 'start' | 'end' } | null>(null);
  const noBlocks = blocks.length === 0;
  const lastFractionalIndex = noBlocks ? undefined : blocks[blocks.length - 1]?.fractional_index;
  const editorRootRef = React.useRef<HTMLDivElement | null>(null);
  const [slashMenuState, setSlashMenuState] = React.useState<{
    open: boolean;
    x: number;
    y: number;
    blockId: string | null;
    onSelect?: (action: QuickInsertAction) => void;
  }>({ open: false, x: 0, y: 0, blockId: null, onSelect: undefined });

  const renderEmptyState = (withInlineCreateBar: boolean) => (
    <div className={styles.emptyState}>
      <p>{t('books.blocks.editor.empty.title')}</p>
      <p className={styles.emptyHint}>{t('books.blocks.editor.empty.hint')}</p>
      {withInlineCreateBar ? <InlineCreateBar onBlockCreated={onBlockCreated} /> : null}
    </div>
  );

  const handleFocusAdjacent = React.useCallback((options: { currentIndex: number; direction: 'prev' | 'next' }) => {
    const { currentIndex, direction } = options;
    const targetIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= blocks.length) {
      return;
    }
    const targetBlock = blocks[targetIndex];
    const targetEdge = direction === 'prev' ? 'end' : 'start';
    announceFocusIntent('keyboard', targetBlock.id, {
      payload: { edge: targetEdge },
      source: 'block-list.focus-adjacent',
    });
    setLocalFocus({
      id: targetBlock.id,
      position: targetEdge,
    });
  }, [blocks]);

  const handleBlockDeletedInternal = React.useCallback((blockId: string, index: number) => {
    onBlockDeleted?.(blockId);
    const fallbackIndex = index > 0 ? index - 1 : index + 1;
    if (fallbackIndex < 0 || fallbackIndex >= blocks.length) {
      return;
    }
    const targetBlock = blocks[fallbackIndex];
    const targetEdge = index > 0 ? 'end' : 'start';
    announceFocusIntent('keyboard', targetBlock.id, {
      payload: { edge: targetEdge },
      source: 'block-list.delete-fallback',
    });
    setLocalFocus({
      id: targetBlock.id,
      position: targetEdge,
    });
  }, [blocks, onBlockDeleted]);

  const handleSlashMenuRequest = React.useCallback((payload: { blockId: string; onSelect: (action: QuickInsertAction) => void }) => {
    const root = editorRootRef.current;
    const anchor = root ? getSlashMenuAnchor(root) : null;
    setSlashMenuState({
      open: true,
      x: anchor?.x ?? 16,
      y: anchor?.y ?? 16,
      blockId: payload.blockId,
      onSelect: payload.onSelect,
    });
  }, []);

  const closeSlashMenu = React.useCallback(() => {
    setSlashMenuState((prev) => ({ ...prev, open: false, blockId: null, onSelect: undefined }));
  }, []);

  const handleSlashMenuAction = React.useCallback((action: QuickInsertAction) => {
    if (slashMenuState.onSelect) {
      void slashMenuState.onSelect(action);
    }
    setSlashMenuState((prev) => ({ ...prev, open: false, blockId: null, onSelect: undefined }));
  }, [slashMenuState.onSelect]);

  React.useEffect(() => {
    const unsubscribe = focusIntentStore.subscribe(() => {
      const intent = focusIntentStore.getIntent();
      if (!intent || intent.kind !== 'pointer') {
        return;
      }
      setLocalFocus((prev) => (prev ? null : prev));
      if (pendingFocusBlockId) {
        onPendingFocusConsumed?.();
      }
    });
    return () => unsubscribe();
  }, [onPendingFocusConsumed, pendingFocusBlockId]);

  if (noBlocks) {
    return renderEmptyState(true);
  }

  return (
    <div className={styles.bookEditorShell} ref={editorRootRef}>
      {blocks.map((block, index) => (
        <BlockItem
          key={block.id}
          block={block}
          index={index}
          nextFractionalIndex={blocks[index + 1]?.fractional_index}
          autoFocus={pendingFocusBlockId === block.id || localFocus?.id === block.id}
          focusPosition={localFocus?.id === block.id ? localFocus.position : pendingFocusBlockId === block.id ? 'start' : undefined}
          onAutoFocusComplete={() => {
            if (localFocus?.id === block.id) {
              setLocalFocus(null);
            }
            if (pendingFocusBlockId === block.id) {
              onPendingFocusConsumed?.();
            }
          }}
          onBlockCreated={onBlockCreated}
          onBlockDeleted={({ blockId, index: deletedIndex }) => handleBlockDeletedInternal(blockId, deletedIndex)}
          onRequestFocusAdjacent={handleFocusAdjacent}
          onRequestSlashMenu={handleSlashMenuRequest}
        />
      ))}
      <InlineCreateBar
        lastFractionalIndex={lastFractionalIndex}
        onBlockCreated={onBlockCreated}
      />
      {slashMenuState.open && (
        <SlashMenu
          x={slashMenuState.x}
          y={slashMenuState.y}
          actions={quickInsertActions}
          onSelect={handleSlashMenuAction}
          onClose={closeSlashMenu}
        />
      )}
    </div>
  );
};
