import React from 'react';
import { BookDto } from '@/entities/book';
import { Card, Button } from '@/shared/ui';
import styles from './BookCard.module.css';

interface BookCardProps {
  book: BookDto;
  onSelect?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const BookCard = React.forwardRef<HTMLDivElement, BookCardProps>(
  ({ book, onSelect, onDelete }, ref) => {
    return (
      <Card ref={ref} className={styles.card}>
        <div className={styles.header}>
          <h3>{book.title}</h3>
          {onDelete && (
            <Button variant="secondary" size="sm" onClick={() => onDelete(book.id)}>
              ×
            </Button>
          )}
        </div>
        {book.summary && <p className={styles.description}>{book.summary}</p>}
        {onSelect && (
          <Button variant="secondary" size="sm" onClick={() => onSelect(book.id)}>
            查看
          </Button>
        )}
      </Card>
    );
  }
);

BookCard.displayName = 'BookCard';
