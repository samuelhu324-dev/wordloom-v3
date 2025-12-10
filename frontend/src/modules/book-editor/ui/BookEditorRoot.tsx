'use client';

import React from 'react';
import { useBlocks } from '@/features/block/model/hooks';
import { sortBlocksByFractionalIndex } from '@/features/block/lib/fractionalOrder';
import { BlockList } from './BlockList';
import styles from './bookEditor.module.css';
import { announceFocusIntent } from '../model/selectionStore';
import { BlockEditorProvider, type BlockEditorRenderable } from '../model/BlockEditorContext';
import { reconcileRenderableBlocks } from '../model/localBlocks';
import { useI18n } from '@/i18n/useI18n';

interface BookEditorRootProps {
  bookId: string;
  onBlockCreated?: (blockId: string) => void;
  onBlockDeleted?: (blockId: string) => void;
}

export const BookEditorRoot: React.FC<BookEditorRootProps> = ({ bookId, onBlockCreated, onBlockDeleted }) => {
  const { data, isLoading, error } = useBlocks(bookId);
  const [pendingFocusBlockId, setPendingFocusBlockId] = React.useState<string | null>(null);
  const [localBlocks, setLocalBlocks] = React.useState<BlockEditorRenderable[]>([]);
  const { t } = useI18n();

  const orderedBlocks = React.useMemo(() => {
    return sortBlocksByFractionalIndex(data ?? []);
  }, [data]);

  React.useEffect(() => {
    if (!orderedBlocks.length) {
      setLocalBlocks([]);
      return;
    }
    setLocalBlocks((prev) => reconcileRenderableBlocks(prev, orderedBlocks));
  }, [orderedBlocks]);

  const handleBlockCreated = React.useCallback((blockId: string) => {
    setPendingFocusBlockId(blockId);
    announceFocusIntent('initial', blockId, { source: 'book-editor-root.block-created' });
    onBlockCreated?.(blockId);
  }, [onBlockCreated]);

  const handleBlockDeleted = React.useCallback((blockId: string) => {
    onBlockDeleted?.(blockId);
  }, [onBlockDeleted]);

  if (!bookId) {
    return <div>{t('books.blocks.editor.shell.missingBook')}</div>;
  }

  if (isLoading) {
    return <div>{t('books.blocks.editor.shell.loading')}</div>;
  }

  if (error) {
    return <div>{t('books.blocks.editor.shell.error')}</div>;
  }

  return (
    <BlockEditorProvider value={{ bookId, blocks: localBlocks, setBlocks: setLocalBlocks }}>
      <div className={styles.editorRoot}>
        <BlockList
          pendingFocusBlockId={pendingFocusBlockId}
          onPendingFocusConsumed={() => setPendingFocusBlockId(null)}
          onBlockCreated={handleBlockCreated}
          onBlockDeleted={handleBlockDeleted}
        />
      </div>
    </BlockEditorProvider>
  );
};
