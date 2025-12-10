import React from 'react';
import { BookDto } from '@/entities/book';
import { Spinner } from '@/shared/ui';
import { BookCard } from './BookCard';
import styles from './BookList.module.css';

interface BookListProps {
  books: BookDto[];
  isLoading?: boolean;
  onSelectBook?: (id: string) => void;
  onDeleteBook?: (id: string) => void;
}

export const BookList = React.forwardRef<HTMLDivElement, BookListProps>(
  ({ books, isLoading, onSelectBook, onDeleteBook }, ref) => {
    if (isLoading) {
      return (
        <div className={styles.container} ref={ref}>
          <Spinner />
        </div>
      );
    }

    if (books.length === 0) {
      return (
        <div className={styles.empty} ref={ref}>
          <p>No books yet. Create one to get started!</p>
        </div>
      );
    }

    return (
      <div className={styles.grid} ref={ref}>
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            onSelect={onSelectBook}
            onDelete={onDeleteBook}
          />
        ))}
      </div>
    );
  }
);

BookList.displayName = 'BookList';
