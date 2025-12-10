import React from 'react';
import { BookDto, BookMaturity } from '@/entities/book';
import { BookDisplayCabinet } from '@/features/book/ui/BookDisplayCabinet';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookshelfBooksSection.module.css';
import type { LucideIcon } from 'lucide-react';

interface BookshelfBooksSectionProps {
  books: BookDto[];
  title?: string;
  description?: string;
  icon?: LucideIcon;
  isLoading?: boolean;
  onSelectBook?: (bookId: string) => void;
  onEditBook?: (bookId: string) => void;
  onDeleteBook?: (bookId: string) => void;
  onTogglePin?: (bookId: string, nextPinned: boolean) => void;
  emptyHint?: string;
  tone?: BookMaturity;
  showHeader?: boolean;
  tagDescriptionsMap?: Record<string, string>;
}

export const BookshelfBooksSection: React.FC<BookshelfBooksSectionProps> = ({
  books,
  title,
  description,
  icon: Icon = undefined,
  isLoading = false,
  onSelectBook,
  onEditBook,
  onDeleteBook,
  onTogglePin,
  emptyHint,
  tone = 'seed',
  showHeader = true,
  tagDescriptionsMap,
}) => {
  const { t } = useI18n();
  const resolvedTitle = title ?? t('books.section.defaultTitle');
  const resolvedDescription = description ?? t('books.section.defaultDescription');
  const resolvedEmptyHint = emptyHint ?? t('books.section.empty');
  const sectionAriaLabel = resolvedTitle || t('books.section.aria');
  const eyebrowLabel = t('books.section.eyebrow');
  const loadingLabel = t('books.section.loading');
  const showEmpty = !isLoading && books.length === 0;

  return (
    <section
      className={styles.bookshelfSection}
      data-tone={tone}
      aria-label={sectionAriaLabel}
    >
      {showHeader && (
        <header className={styles.bookshelfHeader}>
          <div className={styles.headerText}>
            {Icon && (
              <span className={styles.headerIcon} aria-hidden>
                <Icon size={20} strokeWidth={1.6} />
              </span>
            )}
            <div className={styles.headerCopy}>
              <p className={styles.headerEyebrow}>{eyebrowLabel}</p>
              <h3>{resolvedTitle}</h3>
              <p>{resolvedDescription}</p>
            </div>
          </div>
        </header>
      )}

      <div
        className={styles.shelfStrip}
        data-empty={showEmpty ? 'true' : undefined}
        data-tone={tone}
      >
        <div className={styles.shelfBoard} aria-hidden />

        {isLoading ? (
          <div className={styles.loadingState}>{loadingLabel}</div>
        ) : showEmpty ? (
          <div className={styles.emptyState}>{resolvedEmptyHint}</div>
        ) : (
          <div className={styles.shelfBooks}>
            {books.map((book) => {
              const interactiveProps = onSelectBook
                ? {
                    role: 'button' as const,
                    tabIndex: 0,
                    onClick: () => onSelectBook(book.id),
                    onKeyDown: (event: React.KeyboardEvent<HTMLDivElement>) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        onSelectBook(book.id);
                      }
                    },
                    'aria-label': book.title
                      ? t('books.section.openAria', { title: book.title })
                      : t('books.section.openFallback'),
                    'data-clickable': 'true',
                  }
                : {
                    'aria-label': book.title ?? t('books.section.openFallback'),
                    'data-clickable': 'false',
                  };

              return (
                <BookDisplayCabinet
                  key={book.id}
                  book={book}
                  className={styles.bookSlot}
                  onEdit={onEditBook ? () => onEditBook(book.id) : undefined}
                  onDelete={onDeleteBook ? () => onDeleteBook(book.id) : undefined}
                  onTogglePin={onTogglePin ? (nextPinned) => onTogglePin(book.id, nextPinned) : undefined}
                  tagDescriptionsMap={tagDescriptionsMap}
                  {...interactiveProps}
                />
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
};
