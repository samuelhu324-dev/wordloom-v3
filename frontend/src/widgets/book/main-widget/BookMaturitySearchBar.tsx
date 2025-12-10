import React from 'react';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookMaturitySearchBar.module.css';

interface BookMaturitySearchBarProps {
  searchText: string;
  onSearchTextChange: (value: string) => void;
  onClearSearch: () => void;
  placeholder?: string;
}

export const BookMaturitySearchBar: React.FC<BookMaturitySearchBarProps> = ({
  searchText,
  onSearchTextChange,
  onClearSearch,
  placeholder,
}) => {
  const { t } = useI18n();
  const resolvedPlaceholder = placeholder ?? t('books.search.placeholder');
  const label = t('books.search.label');

  return (
    <div className={styles.simpleSearch}>
      <label htmlFor="book-maturity-search" className={styles.visuallyHidden}>
        {label}
      </label>
      <input
        id="book-maturity-search"
        type="search"
        autoComplete="off"
        placeholder={resolvedPlaceholder}
        value={searchText}
        onChange={(event) => onSearchTextChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && searchText) {
            onClearSearch();
          }
        }}
      />
    </div>
  );
};
