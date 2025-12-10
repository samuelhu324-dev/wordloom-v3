import React from 'react';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookMaturityFilterBar.module.css';

const VIEW_OPTIONS = ['combined', 'layered'] as const;

type ViewOptionValue = (typeof VIEW_OPTIONS)[number];

interface BookMaturityFilterBarProps {
  isCombinedView: boolean;
  onCombinedViewChange: (value: boolean) => void;
}

export const BookMaturityFilterBar: React.FC<BookMaturityFilterBarProps> = ({
  isCombinedView,
  onCombinedViewChange,
}) => {
  const { t } = useI18n();
  const selectValue: ViewOptionValue = isCombinedView ? 'combined' : 'layered';
  const labelText = t('books.filter.view.label');
  const ariaLabel = t('books.filter.view.aria');

  return (
    <div className={styles.filterBar}>
      <label htmlFor="book-maturity-view-mode" className={styles.visuallyHidden}>
        {labelText}
      </label>
      <select
        id="book-maturity-view-mode"
        className={styles.modeSelect}
        value={selectValue}
        aria-label={ariaLabel}
        onChange={(event) => onCombinedViewChange(event.target.value === 'combined')}
      >
        {VIEW_OPTIONS.map((option) => (
          <option key={option} value={option}>
            {option === 'combined'
              ? t('books.filter.view.combined')
              : t('books.filter.view.layered')}
          </option>
        ))}
      </select>
    </div>
  );
};
