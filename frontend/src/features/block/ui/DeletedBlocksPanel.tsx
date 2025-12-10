'use client';
import React from 'react';
import type { BlockDto, TodoListBlockContent } from '@/entities/block';
import { useDeletedBlocks, useRestoreBlock } from '@/features/block/model/hooks';
import styles from './DeletedBlocksPanel.module.css';

interface Props { bookId: string; }

export const DeletedBlocksPanel: React.FC<Props> = ({ bookId }) => {
  const { data, isLoading } = useDeletedBlocks(bookId);
  const restore = useRestoreBlock();
  const items = data?.items || [];
  const getPreviewText = React.useCallback((block: BlockDto): string => {
    if (!block?.content) return '';
    if (typeof block.content === 'string') {
      return block.content;
    }
    if ('text' in block.content && typeof block.content.text === 'string') {
      return block.content.text;
    }
    if ('items' in block.content) {
      const list = (block.content as TodoListBlockContent).items ?? [];
      return list
        .map((item) => item?.text || '')
        .filter(Boolean)
        .join(' · ');
    }
    return '';
  }, []);
  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>已删除块 (Paperballs)</h3>
      {isLoading && <p>加载中...</p>}
      {!isLoading && items.length === 0 && <p className={styles.empty}>暂无删除的块</p>}
      <ul className={styles.list}>
        {items.map(b => (
          <li key={b.id} className={styles.item}>
            <div className={styles.row}>
              <span className={styles.type}>{b.type}</span>
              <span className={styles.preview}>{getPreviewText(b).slice(0, 60) || '无内容'}</span>
              <button
                disabled={restore.isPending}
                onClick={() => restore.mutate(b.id)}
                className={styles.restoreBtn}
              >恢复</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DeletedBlocksPanel;