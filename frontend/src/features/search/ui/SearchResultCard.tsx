import React from 'react';
import { SearchResultDto } from '@/entities/search';
import { Card } from '@/shared/ui';
import styles from './SearchResultCard.module.css';

interface SearchResultCardProps {
  result: SearchResultDto;
  onSelect?: (id: string) => void;
}

export const SearchResultCard = React.forwardRef<HTMLDivElement, SearchResultCardProps>(
  ({ result, onSelect }, ref) => {
    return (
      <Card
        ref={ref}
        className={styles.card}
        onClick={() => onSelect?.(result.id)}
        style={{ cursor: 'pointer' }}
      >
        <h4 className={styles.title}>{result.title}</h4>
        <p className={styles.excerpt}>{result.excerpt}</p>
        <div className={styles.meta}>
          <span className={styles.type}>{result.type}</span>
          <span className={styles.score}>Score: {result.score.toFixed(2)}</span>
        </div>
      </Card>
    );
  }
);

SearchResultCard.displayName = 'SearchResultCard';
