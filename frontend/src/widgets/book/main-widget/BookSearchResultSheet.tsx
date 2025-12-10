import React from 'react';
import { ExternalLink, Loader2, Search } from 'lucide-react';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookSearchResultSheet.module.css';
import type { BookFilterScope } from './hooks/useBookFilters';
import type { BookSearchHit } from '@/features/search';

interface BookSearchResultSheetProps {
  query: string;
  scope: BookFilterScope;
  minChars?: number;
  hits?: BookSearchHit[];
  total?: number;
  isLoading: boolean;
  error?: string;
  onSelectHit?: (bookId: string) => void;
}

const stripHtml = (value?: string) => {
  if (!value) return '';
  return value.replace(/<[^>]+>/g, '');
};

export const BookSearchResultSheet: React.FC<BookSearchResultSheetProps> = ({
  query,
  scope,
  minChars = 3,
  hits,
  total,
  isLoading,
  error,
  onSelectHit,
}) => {
  const { t } = useI18n();
  if (scope !== 'global') return null;
  const trimmed = query.trim();
  const hitCount = hits?.length ?? 0;
  const hasHits = hitCount > 0;
  const minCharsText = t('books.search.global.hintShort', { count: minChars });

  return (
    <div className={styles.sheet}>
      <header className={styles.sheetHeader}>
        <Search size={18} strokeWidth={2.2} />
        <div>
          <strong>{t('books.search.global.title')}</strong>
          <p>{t('books.search.global.subtitle')}</p>
        </div>
      </header>

      {!trimmed && <p className={styles.hint}>{t('books.search.global.hintEmpty')}</p>}
      {trimmed && trimmed.length < minChars && (
        <p className={styles.hint}>{minCharsText}</p>
      )}

      {trimmed.length >= minChars && (
        <div className={styles.resultBody}>
          {isLoading && (
            <div className={styles.stateRow}>
              <Loader2 className={styles.spinner} size={18} /> {t('books.search.global.loading')}
            </div>
          )}
          {error && !isLoading && (
            <div className={styles.stateRowError}>{t('books.search.global.error', { message: error })}</div>
          )}
          {!isLoading && !error && hitCount === 0 && (
            <div className={styles.stateRow}>{t('books.search.global.noResults')}</div>
          )}

          {hasHits && (
            <ul className={styles.resultList}>
              {hits?.map((hit) => (
                <li key={`${hit.book_id}-${hit.path ?? hit.title}`}>
                  <div>
                    <strong>{hit.title}</strong>
                    {hit.bookshelf_name && <span className={styles.meta}> · {hit.bookshelf_name}</span>}
                    {hit.maturity && <span className={styles.meta}> · {hit.maturity.toUpperCase()}</span>}
                    {hit.snippet && <p className={styles.snippet}>{stripHtml(hit.snippet)}</p>}
                  </div>
                  {hit.book_id && (
                    <button
                      type="button"
                      className={styles.openButton}
                      onClick={() => onSelectHit?.(hit.book_id!)}
                    >
                      {t('books.search.global.open')} <ExternalLink size={14} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}

          {hasHits && typeof total === 'number' && hits && total > hitCount && (
            <p className={styles.meta}>{t('books.search.global.summary', { shown: hitCount, total })}</p>
          )}
        </div>
      )}
    </div>
  );
};
