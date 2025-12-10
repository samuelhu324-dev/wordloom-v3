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
        {result.preview && <p className={styles.excerpt}>{result.preview}</p>}
        <div className={styles.meta}>
          <span className={styles.type}>{result.entity_type}</span>
          <span className={styles.score}>得分: {result.score.toFixed(2)}</span>
        </div>
      </Card>
    );
  }
);

SearchResultCard.displayName = 'SearchResultCard';
