'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { useBooks, useToggleBookPin, useMoveBookToBasement } from '@/features/book/model/hooks';
import { BookEditDialog } from '@/features/book/ui/BookEditDialog';
import type { BookDto, BookMaturity } from '@/entities/book';
import type { LibraryDto } from '@/entities/library';
import { useLibraryTagCatalog } from '@/features/library';
import { useDebouncedValue } from '@/shared/lib/hooks/useDebouncedValue';
import { ErrorBoundary } from '@/shared/ui/ErrorBoundary';
import { showToast } from '@/shared/ui/toast';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookMainWidget.module.css';
import {
  BookMaturityView,
  sortForPresentation,
  type BookViewMode,
} from './main-widget/maturity';
import { BookMainWidgetHeader } from './main-widget/BookMainWidgetHeader';
import { useBookMaturitySnapshot } from './main-widget/hooks/useBookMaturitySnapshot';
import { BookMaturityFilterBar } from './main-widget/BookMaturityFilterBar';
import { BookMaturitySearchBar } from './main-widget/BookMaturitySearchBar';
import { useBookFilters, getOrderForPreset } from './main-widget/hooks/useBookFilters';

interface BookMainWidgetProps {
  bookshelfId: string;
  libraryId: string; // 新增：创建书籍需要 library_id
  library?: LibraryDto;
  onSelectBook?: (bookId: string) => void;
  onAddBook?: () => void; // 仍保留外部触发能力（可选）
  viewMode?: BookViewMode;
  onViewModeChange?: (mode: BookViewMode) => void;
  showCreate?: boolean;
  onShowCreateChange?: (open: boolean) => void;
  hideInternalActions?: boolean;
  onCreatePendingChange?: (pending: boolean) => void;
  headerPortalTarget?: HTMLElement | null;
}

const STAGE_KEYS: BookMaturity[] = ['seed', 'growing', 'stable', 'legacy'];

const matchesKeyword = (book: BookDto, keyword: string) => {
  if (!keyword) return true;
  const normalized = keyword.toLowerCase();
  const haystack = [
    book.title,
    book.summary,
    book.tagsSummary?.join(' '),
    book.maturity,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return haystack.includes(normalized);
};

export const BookMainWidget = React.forwardRef<HTMLDivElement, BookMainWidgetProps>(
  (
    {
      bookshelfId,
      libraryId,
      library,
      onSelectBook,
      onAddBook,
      viewMode: controlledViewMode,
      onViewModeChange,
      showCreate: controlledShowCreate,
      onShowCreateChange,
      hideInternalActions = false,
      onCreatePendingChange,
      headerPortalTarget,
    },
    ref,
  ) => {
    const { t } = useI18n();
    const [internalViewMode, setInternalViewMode] = useState<BookViewMode>('showcase');
    const viewMode = controlledViewMode ?? internalViewMode;
    const setViewMode = (mode: BookViewMode) => {
      if (onViewModeChange) {
        onViewModeChange(mode);
      } else {
        setInternalViewMode(mode);
      }
    };

    const [internalShowCreate, setInternalShowCreate] = useState(false);
    const showCreate = controlledShowCreate ?? internalShowCreate;
    const setShowCreate = (next: boolean) => {
      if (onShowCreateChange) {
        onShowCreateChange(next);
      } else {
        setInternalShowCreate(next);
      }
    };

    const [createPending, setCreatePending] = useState(false);
    const toggleShowCreate = () => {
      if (createPending) return;
      setShowCreate(!showCreate);
    };

    const {
      state: filterState,
      setSearchScope,
      setSearchText,
      clearSearch,
      setCombinedView,
    } = useBookFilters();

    const debouncedSearch = useDebouncedValue(filterState.searchText.trim(), 300);
    const sectionOrder = getOrderForPreset(filterState.orderPreset);
    const { data: booksData, isLoading, error } = useBooks(bookshelfId);
    const books = booksData?.items ?? [];
    const togglePinMutation = useToggleBookPin();
    const moveBookToBasementMutation = useMoveBookToBasement();
    const [editingBookId, setEditingBookId] = useState<string | null>(null);

    const editingBook = useMemo(() => {
      if (!editingBookId) return null;
      return books.find((book) => book.id === editingBookId) ?? null;
    }, [books, editingBookId]);

    useEffect(() => {
      console.log('[BookMainWidget] books updated', {
        bookshelfId,
        total: booksData?.total ?? books.length,
        isLoading,
        error: error ? (error as Error).message : null,
        sample: books.slice(0, 2),
      });
    }, [books, bookshelfId, isLoading, error, booksData?.total]);

    const handleDeleteBook = (bookId: string) => {
      const basementId = library?.basement_bookshelf_id;
      if (!basementId) {
        showToast(t('books.widget.toast.basementMissing'));
        return;
      }

      const confirmed = confirm(t('books.widget.confirm.moveToBasement'));
      if (!confirmed) {
        return;
      }

      moveBookToBasementMutation.mutate(
        { bookId, basementBookshelfId: basementId },
        {
          onSuccess: () => {
            showToast(t('books.widget.toast.basementMoved'));
          },
          onError: (error) => {
            const fallback = t('books.widget.toast.basementMoveFailed');
            const message = error instanceof Error && error.message
              ? error.message
              : fallback;
            showToast(message);
          },
        },
      );
    };

    const handleEditBook = (bookId: string) => {
      setEditingBookId(bookId);
    };

    const handleTogglePin = (bookId: string, nextPinned: boolean) => {
      togglePinMutation.mutate({ bookId, isPinned: nextPinned });
    };

    const snapshot = useBookMaturitySnapshot({ books, totalFromApi: booksData?.total });

    const requiredTagLabels = useMemo(() => {
      if (!books.length) {
        return [] as string[];
      }
      const unique = new Set<string>();
      books.forEach((book) => {
        if (!Array.isArray(book.tagsSummary)) {
          return;
        }
        book.tagsSummary.forEach((tag) => {
          const trimmed = tag?.trim();
          if (trimmed) {
            unique.add(trimmed);
          }
        });
      });
      return Array.from(unique);
    }, [books]);

    const { tagDescriptionsMap } = useLibraryTagCatalog({
      libraryId,
      inlineTags: library?.tags ?? null,
      requiredTagLabels,
      enabled: requiredTagLabels.length > 0,
    });

    useEffect(() => {
      if (filterState.searchScope !== 'local') {
        setSearchScope('local');
      }
    }, [filterState.searchScope, setSearchScope]);

    const isLocalSearchActive = debouncedSearch.length > 0;

    const groupedWithFilters = useMemo(() => {
      const result: Record<BookMaturity, BookDto[]> = {
        seed: [],
        growing: [],
        stable: [],
        legacy: [],
      };

      STAGE_KEYS.forEach((stage) => {
        const source = snapshot.groupedBooks[stage] ?? [];
        const ordered = source.length <= 1 ? source.slice() : [...source].sort(sortForPresentation);
        let working = ordered;
        if (isLocalSearchActive) {
          working = ordered.filter((book) => matchesKeyword(book, debouncedSearch));
        }
        if (working !== ordered) {
          working = [...working];
        }
        result[stage] = working;
      });

      return result;
    }, [snapshot, isLocalSearchActive, debouncedSearch]);

    const hiddenSections = useMemo(() => {
      const record: Partial<Record<BookMaturity, boolean>> = {};
      STAGE_KEYS.forEach((stage) => {
        record[stage] = !filterState.stageVisibility[stage];
      });
      return record;
    }, [filterState.stageVisibility]);

    const visibleSnapshot = useMemo(() => ({
      groupedBooks: groupedWithFilters,
      counts: snapshot.counts,
      combinedBooks: filterState.combinedView
        ? sectionOrder.flatMap((stage) => groupedWithFilters[stage])
        : undefined,
    }), [groupedWithFilters, snapshot.counts, filterState.combinedView, sectionOrder]);

    const localVisibleCount = sectionOrder.reduce((acc, stage) => {
      if (!filterState.stageVisibility[stage]) return acc;
      return acc + groupedWithFilters[stage].length;
    }, 0);

    const noLocalMatches = isLocalSearchActive && localVisibleCount === 0;

    const searchMeta = debouncedSearch
      ? {
          scope: 'local' as const,
          keyword: debouncedSearch,
          hasMatches: !noLocalMatches,
          onClear: clearSearch,
        }
      : undefined;

    useEffect(() => {
      onCreatePendingChange?.(createPending);
    }, [createPending, onCreatePendingChange]);

    const headerContent = (
      <div
        className={headerPortalTarget
          ? `${styles.widgetHeaderArea} ${styles.widgetHeaderAreaExternal}`
          : styles.widgetHeaderArea}
      >
        <BookMainWidgetHeader
          heading={headerPortalTarget ? null : t('books.widget.heading')}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          showCreate={showCreate}
          createPending={createPending}
          onToggleCreate={toggleShowCreate}
          hideInternalActions={hideInternalActions}
          searchSlot={(
            <BookMaturitySearchBar
              searchText={filterState.searchText}
              onSearchTextChange={setSearchText}
              onClearSearch={clearSearch}
            />
          )}
          viewModeControls={(
            <BookMaturityFilterBar
              isCombinedView={filterState.combinedView}
              onCombinedViewChange={setCombinedView}
            />
          )}
        />
      </div>
    );

    const headerSlot = headerPortalTarget ? null : headerContent;
    const headerPortal = headerPortalTarget ? createPortal(headerContent, headerPortalTarget) : null;

    if (error) {
      return (
        <div ref={ref} className={styles.widget}>
          <div className={styles.error}>
            <p>{t('books.widget.error.title')}</p>
            <span>{(error as Error)?.message || t('books.widget.error.unknown')}</span>
          </div>
        </div>
      );
    }

    return (
      <div ref={ref} className={styles.widget}>
        {headerPortal}
        <ErrorBoundary
          resetKeys={[bookshelfId, booksData?.total, viewMode, filterState.orderPreset, filterState.searchText]}
          fallback={({ reset }) => (
            <div className={styles.maturityError}>
              <div>
                <strong>{t('books.widget.maturityError.title')}</strong>
                <p>{t('books.widget.maturityError.subtitle')}</p>
              </div>
              <button type="button" onClick={reset}>
                {t('books.widget.maturityError.retry')}
              </button>
            </div>
          )}
        >
          <BookMaturityView
            snapshot={visibleSnapshot}
            isLoading={isLoading}
            onSelectBook={onSelectBook}
            onEditBook={handleEditBook}
            onDeleteBook={handleDeleteBook}
            onTogglePin={handleTogglePin}
            emptyHintSeed={t('books.widget.empty.seed')}
            viewMode={viewMode}
            sectionOrder={sectionOrder}
            hiddenSections={hiddenSections}
            searchMeta={searchMeta}
            combinedView={filterState.combinedView}
            headerSlot={headerSlot}
            booksHeading={filterState.combinedView ? t('books.widget.heading') : undefined}
            tagDescriptionsMap={tagDescriptionsMap}
          />
        </ErrorBoundary>
        <BookEditDialog
          mode="create"
          isOpen={showCreate}
          bookshelfId={bookshelfId}
          libraryId={libraryId}
          onClose={() => setShowCreate(false)}
          onCreated={(_payload) => {
            onAddBook?.();
            setShowCreate(false);
          }}
          onPendingChange={setCreatePending}
        />
        <BookEditDialog
          isOpen={Boolean(editingBookId)}
          book={editingBook}
          onClose={() => setEditingBookId(null)}
          onSaved={() => {
            setEditingBookId(null);
          }}
        />
      </div>
    );
  },
);

BookMainWidget.displayName = 'BookMainWidget';

export { BookMaturityView, buildBookMaturitySnapshot } from './main-widget/maturity';
export type {
  BookMaturitySnapshot,
  BookMaturityCounts,
  GroupedBooks,
  BookViewMode,
} from './main-widget/maturity';
