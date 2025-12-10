import React from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import { Spinner } from '@/shared/ui';
import { BookshelfCard } from './BookshelfCard';
import { BookshelfDashboardCard } from './BookshelfDashboardCard';
import styles from './BookshelfList.module.css';

interface BookshelfListProps {
  bookshelves: BookshelfDto[];
  isLoading?: boolean;
  onSelectBookshelf?: (id: string) => void;
  onDeleteBookshelf?: (id: string) => void;
  viewMode?: 'grid' | 'list';
}

export const BookshelfList = React.forwardRef<HTMLDivElement, BookshelfListProps>(
  ({ bookshelves, isLoading, onSelectBookshelf, onDeleteBookshelf, viewMode = 'grid' }, ref) => {
    if (isLoading) {
      return (
        <div className={styles.container} ref={ref}>
          <Spinner />
        </div>
      );
    }

    if (bookshelves.length === 0) {
      return (
        <div className={styles.empty} ref={ref}>
          <p>还没有书橱，点击“新建书橱”开始吧。</p>
        </div>
      );
    }

    const pinnedShelves = bookshelves.filter((b) => b.is_pinned);
    const otherShelves = bookshelves.filter((b) => !b.is_pinned);

    const sortedPinned = [...pinnedShelves].sort((a, b) => {
      const aTs = a.pinned_at ? new Date(a.pinned_at).getTime() : 0;
      const bTs = b.pinned_at ? new Date(b.pinned_at).getTime() : 0;
      return bTs - aTs;
    });

    const renderCollection = (collection: BookshelfDto[]) => {
      if (viewMode === 'list') {
        return (
          <div className={styles.listTable} role="table" aria-label="bookshelf list">
            <div className={styles.headerRow} role="row">
              <span>封面</span>
              <span>名称</span>
              <span>标签</span>
              <span>状态</span>
              <span>次数</span>
              <span>操作</span>
            </div>
            {collection.map((bookshelf) => (
              <BookshelfDashboardCard
                key={bookshelf.id}
                item={bookshelf as any}
                libraryName={undefined}
              />
            ))}
          </div>
        );
      }
      return (
        <div className={styles.grid}>
          {collection.map((bookshelf) => (
            <BookshelfCard
              key={bookshelf.id}
              bookshelf={bookshelf}
              viewMode="grid"
              onSelect={onSelectBookshelf}
              onDelete={onDeleteBookshelf}
            />
          ))}
        </div>
      );
    };

    return (
      <div className={styles.wrapper} ref={ref}>
        {sortedPinned.length > 0 && (
          <section className={styles.section} aria-label="已置顶书橱">
            <div className={styles.sectionHeader}>
              <h3>置顶书橱</h3>
              <span>{sortedPinned.length}</span>
            </div>
            {renderCollection(sortedPinned)}
          </section>
        )}

        {otherShelves.length > 0 && (
          <section className={styles.section} aria-label="其他书橱">
            <div className={styles.sectionHeader}>
              <h3>其他书橱</h3>
              <span>{otherShelves.length}</span>
            </div>
            {renderCollection(otherShelves)}
          </section>
        )}
      </div>
    );
  }
);

BookshelfList.displayName = 'BookshelfList';
