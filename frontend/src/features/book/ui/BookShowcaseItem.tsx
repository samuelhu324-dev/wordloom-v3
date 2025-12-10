import React from 'react';
import { BookDto, BookMaturity } from '@/entities/book';
import type { MessageKey } from '@/i18n/I18nContext';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookDisplayCabinet.module.css';
import { BookFlatCard } from './BookFlatCard';
import { MATURITY_META, formatRelativeTime } from './bookVisuals';
import { Layers, Clock } from 'lucide-react';

export interface BookShowcaseItemProps extends React.HTMLAttributes<HTMLDivElement> {
  book?: BookDto;
  maturity?: BookMaturity;
  backgroundColor?: string;
  glyph?: string;
  status?: BookDto['status'];
  statusColor?: string;
  isPinned?: boolean;
  coverUrl?: string | null;
  showShadow?: boolean;
  accentColor?: string;
  accentStrength?: number;
  onEdit?: () => void;
  onDelete?: () => void;
  onTogglePin?: (nextPinned: boolean) => void;
  tagDescriptionsMap?: Record<string, string>;
}

export const BookShowcaseItem: React.FC<BookShowcaseItemProps> = ({
  book,
  maturity,
  backgroundColor,
  glyph,
  status,
  statusColor,
  isPinned = false,
  coverUrl,
  showShadow = true,
  className = '',
  accentColor,
  accentStrength: _accentStrength,
  onEdit,
  onDelete,
  onTogglePin,
  tagDescriptionsMap,
  ...rest
}) => {
  const { t, lang } = useI18n();
  const resolvedMaturity = (book?.maturity || maturity || 'seed') as BookMaturity;
  const maturityMeta = MATURITY_META[resolvedMaturity];
  const maturityLabelKey = `books.maturity.labels.${resolvedMaturity}` as MessageKey;
  const maturityLabel = t(maturityLabelKey);
  const relativeUpdatedAt = formatRelativeTime(book?.updated_at, lang);
  const blockCount = book?.block_count ?? 0;
  const blockCountLabel = t('books.meta.blocks', { count: blockCount });

  return (
    <div
      className={`${styles.wrapper} ${className}`.trim()}
      data-maturity={resolvedMaturity}
      {...rest}
    >
      <div className={styles.bookColumn}>
        <BookFlatCard
          book={book}
          maturity={resolvedMaturity}
          glyph={glyph}
          status={status}
          statusColor={statusColor}
          isPinned={isPinned}
          coverUrl={coverUrl ?? undefined}
          showShadow={showShadow}
          accentColor={backgroundColor ?? accentColor}
          tagNames={book?.tagsSummary}
          primaryTagName={book?.tagsSummary?.[0]}
          onEdit={onEdit}
          onDelete={onDelete}
          onTogglePin={onTogglePin}
          tagDescriptionsMap={tagDescriptionsMap}
        />
      </div>

      <div className={styles.plaque} data-maturity={resolvedMaturity}>
        <div className={styles.title} title={book?.title || maturityLabel}>
          {book?.title || maturityLabel}
        </div>
        <div className={styles.metaRow}>
          <span className={styles.metaStat} aria-label={blockCountLabel}>
            <Layers size={12} strokeWidth={1.6} />
            {blockCount}
          </span>
          <span className={styles.metaStat} aria-label={t('books.meta.updatedAria', { value: relativeUpdatedAt })}>
            <Clock size={12} strokeWidth={1.6} />
            {relativeUpdatedAt}
          </span>
        </div>
      </div>
    </div>
  );
};
