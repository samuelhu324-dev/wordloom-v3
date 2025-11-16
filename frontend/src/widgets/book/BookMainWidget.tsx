import React from 'react';
import { BookDto } from '@/entities/book';
import { BookList } from '@/features/book';
import { Button } from '@/shared/ui';
import styles from './BookMainWidget.module.css';

interface BookMainWidgetProps {
  books: BookDto[];
  isLoading?: boolean;
  onSelectBook?: (id: string) => void;
}

export const BookMainWidget = React.forwardRef<HTMLDivElement, BookMainWidgetProps>(
  ({ books, isLoading, onSelectBook }, ref) => {
    return (
      <div ref={ref} className={styles.widget}>
        <div className={styles.header}>
          <h2>Books</h2>
          <Button variant="primary">+ New</Button>
        </div>
        <BookList books={books} isLoading={isLoading} onSelectBook={onSelectBook} />
      </div>
    );
  }
);

BookMainWidget.displayName = 'BookMainWidget';
