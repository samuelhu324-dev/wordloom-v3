import React from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import { Spinner } from '@/shared/ui';
import { BookshelfDashboardCard } from './BookshelfDashboardCard';
import styles from './BookshelfList.module.css';

interface BookshelfListProps {
  bookshelves: BookshelfDto[];
  isLoading?: boolean;
  onSelectBookshelf?: (id: string) => void;
  onDeleteBookshelf?: (id: string) => void;
}

export const BookshelfList = React.forwardRef<HTMLDivElement, BookshelfListProps>(
  ({ bookshelves, isLoading, onSelectBookshelf, onDeleteBookshelf }, ref) => {
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
          <p>No bookshelves yet</p>
        </div>
      );
    }

    const activeShelves = bookshelves.filter((b) => (b.status || 'active').toLowerCase() !== 'archived');
    const archivedShelves = bookshelves.filter((b) => (b.status || '').toLowerCase() === 'archived');

    const renderSection = (title: string, data: BookshelfDto[]) => (
      <section className={styles.section} aria-label={title}>
        <div className={styles.sectionHeader}>
          <h3>{title}</h3>
          <span>{data.length}</span>
        </div>
        {data.length === 0 ? (
          <div className={styles.empty}>
            <p>No bookshelves yet</p>
          </div>
        ) : (
          <div className={styles.listTable} role="table" aria-label="bookshelf list">
            <div className={styles.headerRow} role="row">
              <span>封面</span>
              <span>名称</span>
              <span>标签</span>
              <span>状态</span>
              <span>次数</span>
              <span>操作</span>
            </div>
            {data.map((bookshelf) => (
              <BookshelfDashboardCard
                key={bookshelf.id}
                item={bookshelf as any}
                libraryName={undefined}
              />
            ))}
          </div>
        )}
      </section>
    );

    return (
      <div className={styles.wrapper} ref={ref}>
        {renderSection('ALL BOOKSHELVES', activeShelves)}
        {renderSection('ARCHIVED BOOKSHELVES', archivedShelves)}
      </div>
    );
  }
);

BookshelfList.displayName = 'BookshelfList';
