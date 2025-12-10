import React from 'react';
import type { VirtualBasementLibraryDto } from '@/entities/basement/types';
import { useVirtualBasementLibrary } from '@/features/basement/hooks/useVirtualBasementLibrary';
import styles from './style.module.css';

interface Props {
  onOpen?: () => void;
  stats?: Partial<VirtualBasementLibraryDto['stats']>;
  loading?: boolean;
}

export const BasementLibraryCard: React.FC<Props> = ({ onOpen, stats, loading }) => {
  // Keep the lazy stats endpoint disabled unless we truly need it.
  const { data, isFetching } = useVirtualBasementLibrary({ enabled: !stats });
  const basement = data;
  const mergedStats = React.useMemo(() => ({
    deleted_books: stats?.deleted_books ?? basement?.stats.deleted_books ?? 0,
    deleted_bookshelves: stats?.deleted_bookshelves ?? basement?.stats.deleted_bookshelves ?? 0,
  }), [stats, basement]);
  const effectiveLoading = loading ?? (!stats && isFetching);

  return (
    <div
      className={`${styles.card} ${styles.basement}`}
      role="button"
      aria-label="Basement 回收站入口"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => { if (e.key === 'Enter') onOpen?.(); }}
    >
      <div className={styles.header}>
        <span className={styles.title}>{basement?.name ?? 'Basement'}</span>
        <span className={styles.locked} title="回收站，不可删除">🔒</span>
      </div>
      <div className={styles.stats}>
        <div className={styles.stat}>
          <strong>{effectiveLoading ? '—' : mergedStats.deleted_books}</strong>
          <span>删除书籍</span>
        </div>
        <div className={styles.stat}>
          <strong>{effectiveLoading ? '—' : mergedStats.deleted_bookshelves}</strong>
          <span>删除书架</span>
        </div>
      </div>
      <div className={styles.action}>进入回收站 →</div>
    </div>
  );
};

export default BasementLibraryCard;
