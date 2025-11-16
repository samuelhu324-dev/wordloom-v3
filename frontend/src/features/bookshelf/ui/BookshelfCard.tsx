import React from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import { Card, Button } from '@/shared/ui';
import styles from './BookshelfCard.module.css';

interface BookshelfCardProps {
  bookshelf: BookshelfDto;
  onSelect?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const BookshelfCard = React.forwardRef<HTMLDivElement, BookshelfCardProps>(
  ({ bookshelf, onSelect, onDelete }, ref) => {
    return (
      <Card ref={ref} className={styles.card}>
        <div className={styles.header}>
          <h3>{bookshelf.name}</h3>
          {onDelete && (
            <Button variant="ghost" size="sm" onClick={() => onDelete(bookshelf.id)}>
              ×
            </Button>
          )}
        </div>
        {bookshelf.description && <p className={styles.description}>{bookshelf.description}</p>}
        {onSelect && (
          <Button variant="secondary" size="sm" onClick={() => onSelect(bookshelf.id)}>
            View Books
          </Button>
        )}
      </Card>
    );
  }
);

BookshelfCard.displayName = 'BookshelfCard';
