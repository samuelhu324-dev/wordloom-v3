import { ChangeEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { useBookshelfDashboard, useDeleteBookshelf, useQuickUpdateBookshelf } from '../model/hooks';
import type { LibraryTagSummaryDto } from '@/entities/library';
import { useLibraryTagCatalog } from '@/features/library';
import type {
  BookshelfDashboardFilter,
  BookshelfDashboardItemDto,
  BookshelfDashboardSort,
  BookshelfHealth,
  BookshelfDashboardSnapshot,
} from '@/entities/bookshelf';
import { useI18n } from '@/i18n/useI18n';
import { Button, Spinner } from '@/shared/ui';
import { showToast } from '@/shared/ui/toast';
import styles from './BookshelfDashboardBoard.module.css';
import { BookshelfDashboardCard } from './BookshelfDashboardCard';
import { BookshelfTagEditDialog } from './BookshelfTagEditDialog';
const HEADER_COLUMNS = [
  'bookshelves.dashboard.columns.cover',
  'bookshelves.dashboard.columns.name',
  'bookshelves.dashboard.columns.tags',
  'bookshelves.dashboard.columns.status',
  'bookshelves.dashboard.columns.metrics',
  'bookshelves.dashboard.columns.actions',
] as const;

const STATUS_FILTERS: BookshelfDashboardFilter[] = ['active', 'all', 'archived'];

export interface BookshelfDashboardBoardProps {
  libraryId: string;
  sort?: BookshelfDashboardSort;
  statusFilter?: BookshelfDashboardFilter;
  pageSize?: number;
  fallbackThemeColor?: string;
  libraryName?: string;
  libraryTags?: LibraryTagSummaryDto[];
  onSortChange?: (value: BookshelfDashboardSort) => void;
  onStatusFilterChange?: (value: BookshelfDashboardFilter) => void;
  onSnapshotChange?: (snapshot: BookshelfDashboardSnapshot) => void;
  onOpenBookshelf?: (item: BookshelfDashboardItemDto) => void;
  onEditBookshelf?: (item: BookshelfDashboardItemDto) => void;
  onCreateBookshelf?: () => void;
}

const fallbackSort: BookshelfDashboardSort = 'recent_activity';
const fallbackFilter: BookshelfDashboardFilter = 'active';

const EMPTY_HEALTH: Record<BookshelfHealth, number> = {
  active: 0,
  slowing: 0,
  cooling: 0,
  archived: 0,
};

const createEmptySnapshot = (): BookshelfDashboardSnapshot => ({
  total: 0,
  pinned: 0,
  health: { ...EMPTY_HEALTH },
});

const deriveSnapshotFromItems = (items: BookshelfDashboardItemDto[]): BookshelfDashboardSnapshot => {
  if (!items || items.length === 0) {
    return createEmptySnapshot();
  }
  const health = items.reduce<Record<BookshelfHealth, number>>((acc, item) => {
    acc[item.health] = (acc[item.health] ?? 0) + 1;
    return acc;
  }, { ...EMPTY_HEALTH });
  const pinnedCount = items.filter((item) => item.is_pinned).length;
  return {
    total: items.length,
    pinned: pinnedCount,
    health,
  };
};

export const BookshelfDashboardBoard = ({
  libraryId,
  sort = fallbackSort,
  statusFilter = fallbackFilter,
  pageSize = 20,
  fallbackThemeColor,
  libraryName,
  libraryTags,
  onSortChange,
  onStatusFilterChange,
  onSnapshotChange,
  onOpenBookshelf,
  onEditBookshelf,
  onCreateBookshelf,
}: BookshelfDashboardBoardProps) => {
  const { t } = useI18n();
  const sortLabelMap = useMemo<Record<BookshelfDashboardSort, string>>(() => ({
    recent_activity: t('bookshelves.dashboard.sort.recentActivity'),
    name_asc: t('bookshelves.dashboard.sort.nameAsc'),
    created_desc: t('bookshelves.dashboard.sort.createdDesc'),
    book_count_desc: t('bookshelves.dashboard.sort.bookCountDesc'),
  }), [t]);
  const filterLabelMap = useMemo<Partial<Record<BookshelfDashboardFilter, string>>>(() => ({
    active: t('bookshelves.dashboard.filter.active'),
    all: t('bookshelves.dashboard.filter.all'),
    archived: t('bookshelves.dashboard.filter.archived'),
  }), [t]);
  const { data, isLoading, isError, refetch, error } = useBookshelfDashboard({
    libraryId,
    sort,
    statusFilter,
    size: pageSize,
    fallbackThemeColor,
  });
  const deleteMutation = useDeleteBookshelf();
  const quickUpdateMutation = useQuickUpdateBookshelf();
  const isMutating = deleteMutation.isPending || quickUpdateMutation.isPending;
  const resolvedErrorMessage = (error as Error)?.message ?? t('libraries.error.unknown');
  const [editingItem, setEditingItem] = useState<BookshelfDashboardItemDto | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const items = useMemo(() => data?.items ?? [], [data?.items]);

  const normalizedSearch = useMemo(() => searchTerm.trim().toLowerCase(), [searchTerm]);

  const filteredItems = useMemo(() => {
    if (!normalizedSearch) return items;
    return items.filter((item) => {
      const haystack = [
        item.name ?? '',
        (item as any)?.description ?? '',
        Array.isArray((item as any)?.tags)
          ? ((item as any).tags as Array<{ name?: string }>).map((tag) => tag?.name ?? '').join(' ')
          : '',
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedSearch);
    });
  }, [items, normalizedSearch]);

  const requiredTagLabels = useMemo(() => {
    if (!filteredItems.length) {
      return [] as string[];
    }
    const unique = new Set<string>();
    filteredItems.forEach((item) => {
      const metaSource = Array.isArray(item.tagsMeta)
        ? item.tagsMeta
        : (Array.isArray((item as any)?.tags) ? ((item as any).tags as Array<{ name?: string | null }>) : []);
      metaSource.forEach((tag) => {
        const trimmed = tag?.name?.trim();
        if (trimmed) {
          unique.add(trimmed);
        }
      });
      if (Array.isArray(item.tagsSummary)) {
        item.tagsSummary.forEach((label) => {
          const trimmed = label?.trim();
          if (trimmed) {
            unique.add(trimmed);
          }
        });
      }
    });
    return Array.from(unique);
  }, [filteredItems]);

  const { tagDescriptionsMap } = useLibraryTagCatalog({
    libraryId,
    inlineTags: libraryTags,
    requiredTagLabels,
    enabled: requiredTagLabels.length > 0,
  });

  const pinned = useMemo(() => {
    if (!filteredItems.length) return [] as BookshelfDashboardItemDto[];
    const toTimestamp = (item: BookshelfDashboardItemDto) => {
      const candidates = [item.last_activity_at, item.updated_at, item.created_at];
      const ts = candidates.find((value) => value && !Number.isNaN(new Date(value).getTime()));
      return ts ? new Date(ts as string).getTime() : 0;
    };
    return filteredItems
      .filter((item) => item.is_pinned)
      .sort((a, b) => toTimestamp(b) - toTimestamp(a));
  }, [filteredItems]);

  const others = useMemo(() => {
    if (!filteredItems.length) return [] as BookshelfDashboardItemDto[];
    return filteredItems.filter((item) => !item.is_pinned);
  }, [filteredItems]);

  const snapshot = useMemo<BookshelfDashboardSnapshot>(() => {
    if (data?.snapshot) {
      return {
        total: data.snapshot.total,
        pinned: data.snapshot.pinned,
        health: { ...data.snapshot.health },
      };
    }
    if (!items.length) {
      return createEmptySnapshot();
    }
    return deriveSnapshotFromItems(items);
  }, [data?.snapshot, items]);

  useEffect(() => {
    onSnapshotChange?.(snapshot);
  }, [snapshot, onSnapshotChange]);

  const handleOpen = useCallback(
    (item: BookshelfDashboardItemDto) => {
      onOpenBookshelf?.(item);
    },
    [onOpenBookshelf],
  );

  const handleEdit = useCallback(
    (item: BookshelfDashboardItemDto) => {
      if (onEditBookshelf) {
        onEditBookshelf(item);
        return;
      }
      setEditingItem(item);
    },
    [onEditBookshelf, setEditingItem],
  );

  const handlePinToggle = useCallback(
    (item: BookshelfDashboardItemDto) => {
      quickUpdateMutation.mutate(
        { bookshelfId: item.id, data: { is_pinned: !item.is_pinned } },
        {
          onSuccess: () => {
            showToast(item.is_pinned ? t('bookshelves.dashboard.toast.unpin') : t('bookshelves.dashboard.toast.pin'));
            refetch();
          },
          onError: (mutationError: unknown) => {
            const message = (mutationError as Error)?.message || t('bookshelves.dashboard.toast.pinFailed');
            showToast(message);
          },
        },
      );
    },
    [quickUpdateMutation, refetch, t],
  );

  const handleArchiveToggle = useCallback(
    (item: BookshelfDashboardItemDto) => {
      const isArchived = Boolean(item.is_archived || item.status?.toLowerCase() === 'archived');
      const nextStatus = isArchived ? 'active' : 'archived';
      quickUpdateMutation.mutate(
        { bookshelfId: item.id, data: { status: nextStatus } },
        {
          onSuccess: () => {
            showToast(isArchived ? t('bookshelves.dashboard.toast.restored') : t('bookshelves.dashboard.toast.archived'));
            refetch();
          },
          onError: (mutationError: unknown) => {
            const message = (mutationError as Error)?.message || t('bookshelves.dashboard.toast.statusFailed');
            showToast(message);
          },
        },
      );
    },
    [quickUpdateMutation, refetch, t],
  );

  const handleDelete = useCallback(
    (item: BookshelfDashboardItemDto) => {
      if (!window.confirm(t('bookshelves.dashboard.confirm.delete', { name: item.name ?? '' }))) {
        return;
      }
      deleteMutation.mutate(
        item.id,
        {
          onSuccess: () => {
            showToast(t('bookshelves.dashboard.toast.deleted'));
            refetch();
          },
          onError: (mutationError: unknown) => {
            const message = (mutationError as Error)?.message || t('bookshelves.dashboard.toast.deleteFailed');
            showToast(message);
          },
        },
      );
    },
    [deleteMutation, refetch, t],
  );

  const handleDialogClose = useCallback(() => {
    setEditingItem(null);
  }, [setEditingItem]);

  const handleDialogSaved = useCallback((
    _payload?: { bookshelfId: string; name: string; description?: string; tags: string[] },
  ) => {
    refetch();
    setEditingItem(null);
  }, [refetch, setEditingItem]);

  const handleSearchChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  }, []);

  const handleSearchClear = useCallback(() => {
    setSearchTerm('');
  }, []);

  const handleCreateClick = useCallback(() => {
    if (onCreateBookshelf) {
      onCreateBookshelf();
    }
  }, [onCreateBookshelf]);

  const hasOriginalItems = items.length > 0;
  const hasFilteredItems = filteredItems.length > 0;
  const isSearchActive = Boolean(normalizedSearch);

  const showEmptyState = !isLoading && !isError && !hasOriginalItems;
  const showNoMatchState = !isLoading && !isError && hasOriginalItems && !hasFilteredItems && isSearchActive;
  const showTable = !isLoading && !isError && hasFilteredItems;

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.actions}>
          <label className={styles.label}>
            {t('bookshelves.dashboard.sortLabel')}
            <select
              className={styles.select}
              value={sort}
              onChange={(e) => onSortChange?.(e.target.value as BookshelfDashboardSort)}
            >
              {(Object.keys(sortLabelMap) as BookshelfDashboardSort[]).map((value) => (
                <option key={value} value={value}>
                  {sortLabelMap[value]}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.label}>
            {t('bookshelves.dashboard.filterLabel')}
            <select
              className={styles.select}
              value={statusFilter}
              onChange={(e) =>
                onStatusFilterChange?.(e.target.value as BookshelfDashboardFilter)
              }
            >
              {STATUS_FILTERS.map((value) => (
                <option key={value} value={value}>
                  {filterLabelMap[value] ?? value.toUpperCase()}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className={styles.headerRight}>
          <div className={styles.searchGroup}>
            <input
              type="search"
              className={styles.searchInput}
              placeholder={t('bookshelves.dashboard.search.placeholder')}
              aria-label={t('bookshelves.dashboard.search.aria')}
              value={searchTerm}
              onChange={handleSearchChange}
            />
            {searchTerm && (
              <button
                type="button"
                className={styles.searchClear}
                onClick={handleSearchClear}
                aria-label={t('bookshelves.dashboard.search.clearAria')}
              >
                &times;
              </button>
            )}
          </div>
          {onCreateBookshelf && (
            <Button size="sm" variant="primary" onClick={handleCreateClick}>
              {t('bookshelves.dashboard.actions.new')}
            </Button>
          )}
        </div>
      </div>

      {isLoading && (
        <div className={styles.state}>
          <Spinner size="sm" />
          <span>{t('bookshelves.dashboard.state.loading')}</span>
        </div>
      )}

      {isError && (
        <div className={styles.stateError}>
          <p>{t('bookshelves.dashboard.state.error', { message: resolvedErrorMessage })}</p>
          <Button size="sm" variant="secondary" onClick={() => refetch()}>
            {t('button.retry')}
          </Button>
        </div>
      )}

      {showEmptyState && (
        <div className={styles.empty}>
          <p>{t('bookshelves.dashboard.state.empty')}</p>
        </div>
      )}

      {showNoMatchState && (
        <div className={styles.empty}>
          <p>{t('bookshelves.dashboard.state.noMatch', { keyword: searchTerm.trim() })}</p>
          <Button size="sm" variant="secondary" onClick={handleSearchClear}>
            {t('bookshelves.dashboard.state.clearSearch')}
          </Button>
        </div>
      )}

      {showTable && (
        <div className={styles.table} role="table" aria-label={t('bookshelves.dashboard.table.aria')}>
          {pinned.length > 0 && (
            <section className={styles.section} aria-label={t('bookshelves.dashboard.table.pinnedAria')}>
              <div className={styles.sectionLabel}>{t('bookshelves.dashboard.section.pinned')}</div>
              <div className={styles.headerRow} role="row">
                {HEADER_COLUMNS.map((columnKey) => (
                  <span key={columnKey}>{t(columnKey)}</span>
                ))}
              </div>
              <div className={styles.sectionRows} role="presentation">
                {pinned.map((item) => (
                  <BookshelfDashboardCard
                    key={item.id}
                    item={item}
                    libraryName={libraryName}
                    tagDescriptionsMap={tagDescriptionsMap}
                    onOpen={handleOpen}
                    onEdit={handleEdit}
                    onPinToggle={handlePinToggle}
                    onArchiveToggle={handleArchiveToggle}
                    onDelete={handleDelete}
                    actionsDisabled={isMutating}
                  />
                ))}
              </div>
            </section>
          )}

          <section className={styles.section} aria-label={t('bookshelves.dashboard.table.aria')}>
            <div className={styles.sectionLabel}>{t('bookshelves.dashboard.section.all')}</div>
            <div className={styles.headerRow} role="row">
              {HEADER_COLUMNS.map((columnKey) => (
                <span key={columnKey}>{t(columnKey)}</span>
              ))}
            </div>
            <div className={styles.sectionRows} role="presentation">
              {others.length > 0 ? (
                others.map((item) => (
                  <BookshelfDashboardCard
                    key={item.id}
                    item={item}
                    libraryName={libraryName}
                    tagDescriptionsMap={tagDescriptionsMap}
                    onOpen={handleOpen}
                    onEdit={handleEdit}
                    onPinToggle={handlePinToggle}
                    onArchiveToggle={handleArchiveToggle}
                    onDelete={handleDelete}
                    actionsDisabled={isMutating}
                  />
                ))
              ) : (
                <div className={`${styles.row} ${styles.emptyRow}`} role="row">
                  <div className={styles.cellCover} role="gridcell" />
                  <div className={styles.cellName} role="gridcell">
                    {t(isSearchActive ? 'bookshelves.dashboard.table.noSearchResults' : 'bookshelves.dashboard.table.noData')}
                  </div>
                  <div className={styles.cellTags} role="gridcell" />
                  <div className={styles.cellStatus} role="gridcell" />
                  <div className={styles.cellMetrics} role="gridcell" />
                  <div className={styles.cellActions} role="gridcell" />
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      <BookshelfTagEditDialog
        isOpen={Boolean(editingItem)}
        bookshelf={editingItem ?? undefined}
        onClose={handleDialogClose}
        onSaved={handleDialogSaved}
      />
    </div>
  );
};

BookshelfDashboardBoard.displayName = 'BookshelfDashboardBoard';
