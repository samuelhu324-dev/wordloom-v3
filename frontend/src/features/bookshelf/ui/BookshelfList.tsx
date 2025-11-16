import React from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import { Spinner } from '@/shared/ui';
import { BookshelfCard } from './BookshelfCard';
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
          <p>No bookshelves yet. Create one to get started!</p>
        </div>
      );
    }

    return (
      <div className={styles.grid} ref={ref}>
        {bookshelves.map((bookshelf) => (
          <BookshelfCard
            key={bookshelf.id}
            bookshelf={bookshelf}
            onSelect={onSelectBookshelf}
            onDelete={onDeleteBookshelf}
          />
        ))}
      </div>
    );
  }
);

BookshelfList.displayName = 'BookshelfList';
