import React from 'react';
import { SearchResultDto } from '@/entities/search';
import { Spinner } from '@/shared/ui';
import { SearchResultCard } from './SearchResultCard';
import styles from './SearchResultsList.module.css';

interface SearchResultsListProps {
  results: SearchResultDto[];
  isLoading?: boolean;
  onSelectResult?: (id: string) => void;
}

export const SearchResultsList = React.forwardRef<HTMLDivElement, SearchResultsListProps>(
  ({ results, isLoading, onSelectResult }, ref) => {
    if (isLoading) {
      return (
        <div className={styles.container} ref={ref}>
          <Spinner />
        </div>
      );
    }

    if (results.length === 0) {
      return (
        <div className={styles.empty} ref={ref}>
          <p>No results found</p>
        </div>
      );
    }

    return (
      <div className={styles.list} ref={ref}>
        {results.map((result) => (
          <SearchResultCard key={result.id} result={result} onSelect={onSelectResult} />
        ))}
      </div>
    );
  }
);

SearchResultsList.displayName = 'SearchResultsList';
