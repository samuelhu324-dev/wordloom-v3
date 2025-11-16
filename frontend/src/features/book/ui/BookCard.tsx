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
            <Button variant="ghost" size="sm" onClick={() => onDelete(book.id)}>
              ×
            </Button>
          )}
        </div>
        {book.description && <p className={styles.description}>{book.description}</p>}
        <div className={styles.meta}>
          <span>{book.blocks_count || 0} blocks</span>
        </div>
        {onSelect && (
          <Button variant="secondary" size="sm" onClick={() => onSelect(book.id)}>
            View Blocks
          </Button>
        )}
      </Card>
    );
  }
);

BookCard.displayName = 'BookCard';
