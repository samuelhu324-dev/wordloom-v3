import React from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import { BookshelfList } from '@/features/bookshelf';
import { Button } from '@/shared/ui';
import styles from './BookshelfMainWidget.module.css';

interface BookshelfMainWidgetProps {
  bookshelves: BookshelfDto[];
  isLoading?: boolean;
  onSelectBookshelf?: (id: string) => void;
}

export const BookshelfMainWidget = React.forwardRef<HTMLDivElement, BookshelfMainWidgetProps>(
  ({ bookshelves, isLoading, onSelectBookshelf }, ref) => {
    return (
      <div ref={ref} className={styles.widget}>
        <div className={styles.header}>
          <h2>Bookshelves</h2>
          <Button variant="primary">+ New</Button>
        </div>
        <BookshelfList
          bookshelves={bookshelves}
          isLoading={isLoading}
          onSelectBookshelf={onSelectBookshelf}
        />
      </div>
    );
  }
);

BookshelfMainWidget.displayName = 'BookshelfMainWidget';
