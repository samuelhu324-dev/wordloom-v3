import React from 'react';
import { BookDto, BookMaturity } from '@/entities/book';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import { BookRowCard } from '@/features/book/ui/BookRowCard';
import { BookshelfBooksSection } from '../BookshelfBooksSection';
import styles from '../BookMainWidget.module.css';

export type BookViewMode = 'showcase' | 'row';

export type GroupedBooks = Record<BookMaturity, BookDto[]>;

export interface BookMaturityCounts {
  seed: number;
  growing: number;
  stable: number;
  legacy: number;
  total: number;
  active: number;
  progress: number;
}

export interface BookMaturitySnapshot {
  groupedBooks: GroupedBooks;
  counts: BookMaturityCounts;
  combinedBooks?: BookDto[];
}

const parseTimestamp = (value?: string) => {
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
};

export const sortForPresentation = (a: BookDto, b: BookDto) => {
  const aPinned = Boolean(a.is_pinned);
  const bPinned = Boolean(b.is_pinned);
  if (aPinned && !bPinned) return -1;
  if (!aPinned && bPinned) return 1;
  const updatedDiff = parseTimestamp(b.updated_at) - parseTimestamp(a.updated_at);
  if (updatedDiff !== 0) return updatedDiff;
  return parseTimestamp(b.created_at) - parseTimestamp(a.created_at);
};

export const buildBookMaturitySnapshot = (books: BookDto[], totalFromApi?: number): BookMaturitySnapshot => {
  const grouped: GroupedBooks = {
    seed: [],
    growing: [],
    stable: [],
    legacy: [],
  };

  books.forEach((book) => {
    const rawMaturity = (book.maturity || 'seed') as BookMaturity;
    const key = book.legacyFlag ? 'legacy' : rawMaturity;
    grouped[key].push(book);
  });

  (Object.keys(grouped) as BookMaturity[]).forEach((key) => {
    grouped[key].sort(sortForPresentation);
  });

  const total = totalFromApi ?? books.length;
  const legacyCount = grouped.legacy.length;
  const stableCount = grouped.stable.length;
  const active = Math.max(total - legacyCount, 0);
  const rawProgress = active === 0 ? 0 : Math.round((stableCount / active) * 100);
  const progress = Math.min(Math.max(rawProgress, 0), 100);

  return {
    groupedBooks: grouped,
    counts: {
      seed: grouped.seed.length,
      growing: grouped.growing.length,
      stable: stableCount,
      legacy: legacyCount,
      total,
      active,
      progress,
    },
  };
};

const SECTION_ORDER_DEFAULT: BookMaturity[] = ['seed', 'growing', 'stable', 'legacy'];

const MATURITY_SECTION_META: Record<BookMaturity, {
  titleKey: MessageKey;
  emptyKey: MessageKey;
}> = {
  seed: {
    titleKey: 'books.maturity.labels.seed',
    emptyKey: 'books.maturity.empty.seed',
  },
  growing: {
    titleKey: 'books.maturity.labels.growing',
    emptyKey: 'books.maturity.empty.growing',
  },
  stable: {
    titleKey: 'books.maturity.labels.stable',
    emptyKey: 'books.maturity.empty.stable',
  },
  legacy: {
    titleKey: 'books.maturity.labels.legacy',
    emptyKey: 'books.maturity.empty.legacy',
  },
};

const capitalize = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

export interface BookMaturityViewProps {
  snapshot: BookMaturitySnapshot;
  isLoading?: boolean;
  onSelectBook?: (bookId: string) => void;
  onEditBook?: (bookId: string) => void;
  onDeleteBook?: (bookId: string) => void;
  onTogglePin?: (bookId: string, nextPinned: boolean) => void;
  emptyHintSeed?: string;
  viewMode?: BookViewMode;
  sectionOrder?: BookMaturity[];
  hiddenSections?: Partial<Record<BookMaturity, boolean>>;
  searchMeta?: {
    scope: 'local' | 'global';
    keyword?: string;
    hasMatches: boolean;
    onClear?: () => void;
  };
  combinedView?: boolean;
  headerSlot?: React.ReactNode;
  booksHeading?: string;
  tagDescriptionsMap?: Record<string, string>;
}

export const BookMaturityView = React.forwardRef<HTMLDivElement, BookMaturityViewProps>(
  (
    {
      snapshot,
      isLoading = false,
      onSelectBook,
      onEditBook,
      onDeleteBook,
      onTogglePin,
      emptyHintSeed,
      viewMode = 'showcase',
      sectionOrder,
      hiddenSections,
      searchMeta,
      combinedView = false,
      headerSlot,
      booksHeading,
      tagDescriptionsMap,
    },
    ref,
  ) => {
    const { t } = useI18n();
    const { groupedBooks, counts, combinedBooks } = snapshot;
    const isEmpty = counts.total === 0;
    const orderedSections = (sectionOrder?.length ? sectionOrder : SECTION_ORDER_DEFAULT).map((key) => ({
      key,
      title: t(MATURITY_SECTION_META[key].titleKey),
      emptyKey: MATURITY_SECTION_META[key].emptyKey,
    }));
    const summaryStages: BookMaturity[] = ['seed', 'growing', 'stable', 'legacy'];

    return (
      <div ref={ref} className={styles.viewRoot}>
        <div className={styles.summaryBar} data-empty={isEmpty ? 'true' : undefined}>
          <div
            className={styles.summaryProgress}
            role="progressbar"
            aria-valuenow={counts.progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuetext={`${counts.progress}%`}
          >
            <span className={styles.summaryProgressLabel}>{t('books.summary.progress')}</span>
            <div className={styles.summaryProgressTrack}>
              <div className={styles.summaryProgressFill} style={{ width: `${counts.progress}%` }} />
            </div>
            <span className={styles.summaryProgressValue}>{counts.progress}%</span>
          </div>
          <div className={styles.summaryCounters}>
            {summaryStages.map((key) => (
              <div key={key} className={styles.summaryCounter} data-maturity={key}>
                <span className={styles.summaryCounterValue}>{counts[key]}</span>
                <span className={styles.summaryCounterLabel}>{t(MATURITY_SECTION_META[key].titleKey)}</span>
              </div>
            ))}
            <div className={styles.summaryCounterTotal}>
              <span className={styles.summaryCounterValue}>{counts.total}</span>
              <span className={styles.summaryCounterLabel}>{t('books.summary.total')}</span>
            </div>
          </div>
          {isEmpty && <div className={styles.summaryEmptyHint}>{t('books.summary.emptyHint')}</div>}
        </div>
        {headerSlot}
        {searchMeta && searchMeta.scope === 'local' && searchMeta.keyword && (
          <div className={styles.searchFeedback} data-state={searchMeta.hasMatches ? 'match' : 'empty'}>
            {searchMeta.hasMatches
              ? t('books.search.localMatch', { keyword: searchMeta.keyword })
              : (
                <>
                  {t('books.search.localEmpty', { keyword: searchMeta.keyword })}
                  {searchMeta.onClear && (
                    <button type="button" onClick={searchMeta.onClear}>
                      {t('books.search.clear')}
                    </button>
                  )}
                </>
              )}
          </div>
        )}
        {combinedView && booksHeading ? (
          <p className={styles.booksHeading}>{booksHeading}</p>
        ) : null}
        {combinedView ? (
          <div className={styles.combinedSection}>
            {isLoading && !combinedBooks?.length ? (
              <div className={styles.sectionEmpty}>{t('books.sections.loading')}</div>
            ) : combinedBooks && combinedBooks.length > 0 ? (
              viewMode === 'showcase'
                ? (
                  <BookshelfBooksSection
                    books={combinedBooks}
                    tone="seed"
                    isLoading={isLoading}
                    onSelectBook={onSelectBook}
                    onEditBook={onEditBook}
                    onDeleteBook={onDeleteBook}
                    onTogglePin={onTogglePin}
                    title={t('books.sections.allBooks')}
                    emptyHint={emptyHintSeed}
                    showHeader={false}
                    tagDescriptionsMap={tagDescriptionsMap}
                  />
                ) : (
                  <div className={styles.rowList}>
                    {combinedBooks.map((book) => (
                      <BookRowCard
                        key={book.id}
                        book={book}
                        onSelect={onSelectBook}
                        onEdit={onEditBook}
                        onDelete={onDeleteBook}
                        onTogglePin={onTogglePin}
                        tagDescriptionsMap={tagDescriptionsMap}
                      />
                    ))}
                  </div>
                )
            ) : (
              <div className={styles.sectionEmpty}>{t('books.sections.empty')}</div>
            )}
          </div>
        ) : (
          <div className={styles.maturitySections}>
            {orderedSections.map((section) => {
              const items = groupedBooks[section.key] ?? [];
              const sectionClass = styles[`section${capitalize(section.key)}`] || '';
              const isHidden = Boolean(hiddenSections?.[section.key]);
              const defaultEmpty = t(section.emptyKey);
              const emptyHint = section.key === 'seed' && emptyHintSeed ? emptyHintSeed : defaultEmpty;

              return (
                <section key={section.key} className={`${styles.maturitySection} ${sectionClass}`}>
                  <header className={styles.sectionHeader}>
                    <div className={styles.sectionTitleBlock}>
                      <p className={styles.sectionLabel}>{section.title}</p>
                      <span className={styles.sectionCount}>{items.length}</span>
                    </div>
                  </header>

                  {isLoading && !items.length ? (
                    <div className={styles.sectionEmpty}>{t('books.sections.loading')}</div>
                  ) : isHidden ? (
                    <div className={styles.sectionHidden}>{t('books.sections.hidden')}</div>
                  ) : viewMode === 'showcase' ? (
                    <BookshelfBooksSection
                      books={items}
                      tone={section.key}
                      isLoading={isLoading}
                      onSelectBook={onSelectBook}
                      onEditBook={onEditBook}
                      onDeleteBook={onDeleteBook}
                      onTogglePin={onTogglePin}
                      title={section.title}
                      emptyHint={emptyHint}
                      showHeader={false}
                      tagDescriptionsMap={tagDescriptionsMap}
                    />
                  ) : items.length === 0 ? (
                    <div className={styles.sectionEmpty}>{emptyHint}</div>
                  ) : (
                    <div className={styles.rowList}>
                      {items.map((book) => (
                        <BookRowCard
                          key={book.id}
                          book={book}
                          onSelect={onSelectBook}
                          onEdit={onEditBook}
                          onDelete={onDeleteBook}
                          onTogglePin={onTogglePin}
                          tagDescriptionsMap={tagDescriptionsMap}
                        />
                      ))}
                    </div>
                  )}
                </section>
              );
            })}
          </div>
        )}
      </div>
    );
  },
);

BookMaturityView.displayName = 'BookMaturityView';
