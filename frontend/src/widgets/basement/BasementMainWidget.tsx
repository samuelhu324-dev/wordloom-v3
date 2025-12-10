"use client";
import React from 'react';
import { useBasementGroups } from '@/features/basement/hooks/useBasementGroups';
import { useLibraries } from '@/features/library/model/hooks';
import type { DeletedBookDto } from '@/entities/basement/types';
import type { LibraryDto } from '@/entities/library';
import { Button } from '@/shared/ui';
import RestoreBookModal from '@/widgets/RestoreBookModal';
import styles from './BasementMainWidget.module.css';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';

interface BasementMainWidgetProps {
  onExit?: () => void;
  initialLibraryId?: string;
}

export const BasementMainWidget: React.FC<BasementMainWidgetProps> = ({ onExit, initialLibraryId }) => {
  const [search, setSearch] = React.useState('');
  const [selectedLibraryId, setSelectedLibraryId] = React.useState<string | null>(initialLibraryId ?? null);
  const [restoreTarget, setRestoreTarget] = React.useState<DeletedBookDto | null>(null);
  const { t, lang } = useI18n();
  const formatRelative = React.useCallback((iso?: string | null) => formatRelativeTime(iso, lang, t), [lang, t]);

  const {
    data: libraries,
    isLoading: librariesLoading,
    error: libraryError,
  } = useLibraries({ query: search, includeArchived: true });

  React.useEffect(() => {
    if (!libraries || libraries.length === 0) return;
    if (selectedLibraryId && libraries.some((lib) => lib.id === selectedLibraryId)) {
      return;
    }
    const fallback = initialLibraryId && libraries.some((lib) => lib.id === initialLibraryId)
      ? initialLibraryId
      : libraries[0].id;
    setSelectedLibraryId(fallback);
  }, [libraries, selectedLibraryId, initialLibraryId]);

  const activeLibrary: LibraryDto | null = React.useMemo(() => {
    if (!libraries) return null;
    return libraries.find((lib) => lib.id === selectedLibraryId) ?? null;
  }, [libraries, selectedLibraryId]);

  const basementQuery = useBasementGroups({
    libraryId: selectedLibraryId ?? undefined,
    limit: 60,
  });

  const groups = basementQuery.data?.items ?? [];
  const stats = basementQuery.data?.stats;
  const availableBookshelves = basementQuery.data?.availableBookshelves ?? [];
  const isGroupsEmpty = !basementQuery.isLoading && !basementQuery.isFetching && groups.length === 0;

  const heroStats: Array<{ label: string; value: string | number }> = [
    { label: t('basement.stats.deletedBooks'), value: stats?.bookTotal ?? basementQuery.data?.total ?? 0 },
    { label: t('basement.stats.groups'), value: stats?.groupTotal ?? groups.length },
    { label: t('basement.stats.lostShelves'), value: stats?.lostShelves ?? 0 },
    { label: t('basement.stats.latestDeleted'), value: formatRelative(stats?.latestDeletedAt) },
  ];

  const handleSelectLibrary = (libraryId: string) => {
    setSelectedLibraryId(libraryId);
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <h1 className={styles.title}>{t('basement.title')}</h1>
          <p className={styles.subtitle}>
            {activeLibrary
              ? t('basement.subtitle.active', { name: activeLibrary.name })
              : t('basement.subtitle.empty')}
          </p>
        </div>
        <div className={styles.headerActions}>
          {basementQuery.isFetching && (
            <span className={styles.refreshIndicator}>{t('basement.groups.loading')}</span>
          )}
          {onExit && (
            <button className={styles.actionButton} onClick={onExit} aria-label={t('basement.actions.backAria')}>
              {t('basement.actions.back')}
            </button>
          )}
        </div>
      </header>

      <div className={styles.layout}>
        <section className={styles.libraryPanel}>
          <div className={styles.panelHeader}>
            <h3 className={styles.panelTitle}>{t('basement.libraryPanel.title')}</h3>
            <input
              className={styles.searchInput}
              type="search"
              placeholder={t('basement.libraryPanel.search')}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          {libraryError && (
            <div className={styles.errorBanner}>
              {t('basement.libraryPanel.error', {
                message: (libraryError as Error)?.message ?? t('basement.libraryPanel.errorUnknown'),
              })}
            </div>
          )}
          {librariesLoading && (!libraries || libraries.length === 0) && (
            <div className={styles.placeholder}>{t('basement.libraryPanel.loading')}</div>
          )}
          {!librariesLoading && (!libraries || libraries.length === 0) && (
            <div className={styles.placeholder}>{t('basement.libraryPanel.empty')}</div>
          )}
          {libraries && libraries.length > 0 && (
            <ul className={styles.libraryList}>
              {libraries.map((library) => {
                const isActive = library.id === selectedLibraryId;
                const isArchived = Boolean(library.archived_at);
                const className = isActive
                  ? `${styles.libraryItem} ${styles.libraryItemActive}`
                  : styles.libraryItem;
                return (
                  <li key={library.id}>
                    <button type="button" className={className} onClick={() => handleSelectLibrary(library.id)}>
                      <div className={styles.libraryNameRow}>
                        <span className={styles.libraryName}>{library.name}</span>
                        {isArchived && (
                          <span className={`${styles.libraryStatusBadge} ${styles.libraryStatusBadgeArchived}`}>
                            {t('basement.libraryPanel.badge.archived')}
                          </span>
                        )}
                      </div>
                      <span className={styles.libraryMeta}>
                        {t('basement.libraryPanel.lastActive', {
                          relative: formatRelative(library.last_activity_at),
                        })}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className={styles.groupsPanel}>
          <div className={styles.statsRow}>
            {heroStats.map((stat) => (
              <article key={stat.label} className={styles.statCard}>
                <span className={styles.statLabel}>{stat.label}</span>
                <span className={styles.statValue}>{stat.value}</span>
              </article>
            ))}
          </div>

          {availableBookshelves.length > 0 && (
            <p className={styles.libraryMeta}>
              {t('basement.stats.restorableShelves', { count: availableBookshelves.length })}
            </p>
          )}

          {basementQuery.isLoading && <div className={styles.placeholder}>{t('basement.groups.loading')}</div>}
          {basementQuery.isError && (
            <div className={styles.errorBanner}>
              {t('basement.groups.error')}
              <button className={styles.actionButton} onClick={() => basementQuery.refetch()}>
                {t('basement.groups.retry')}
              </button>
            </div>
          )}
          {isGroupsEmpty && <div className={styles.placeholder}>{t('basement.groups.empty')}</div>}

          {!basementQuery.isLoading && !basementQuery.isError && groups.length > 0 && (
            <div className={styles.groupsGrid}>
              {groups.map((group) => {
                const className = group.bookshelf_exists
                  ? styles.groupCard
                  : `${styles.groupCard} ${styles.groupCardOrphan}`;
                const shelfStatus = group.bookshelf_exists
                  ? t('basement.group.shelfAvailable')
                  : t('basement.group.shelfMissing');
                const bookCountLabel = t('basement.group.bookCount', { count: group.count });
                return (
                  <article key={group.bookshelf_id} className={className}>
                    <div className={styles.groupHeader}>
                      <div>
                        <h4 className={styles.groupTitle}>{group.name}</h4>
                        <div className={styles.groupMeta}>
                          {shelfStatus} · {bookCountLabel}
                        </div>
                      </div>
                      <div className={styles.groupMeta}>{formatRelative(group.latest_deleted_at)}</div>
                    </div>
                    <ul className={styles.bookList}>
                      {group.items.slice(0, 5).map((book) => (
                        <li key={book.book_id} className={styles.bookItem}>
                          <div className={styles.bookInfo}>
                            <p className={styles.bookTitle}>{book.title}</p>
                            <p className={styles.bookMeta}>{formatRelative(book.deleted_at)}</p>
                          </div>
                          <div className={styles.bookActions}>
                            <button
                              type="button"
                              className={styles.bookActionButton}
                              onClick={() => setRestoreTarget(book)}
                            >
                              {t('basement.group.restore')}
                            </button>
                          </div>
                        </li>
                      ))}
                      {group.count > 5 && (
                        <li className={styles.moreHint}>
                          {t('basement.group.moreHint', { count: group.count - 5 })}
                        </li>
                      )}
                    </ul>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>

      {restoreTarget && (
        <RestoreBookModal
          book={restoreTarget}
          shelves={availableBookshelves}
          onClose={() => setRestoreTarget(null)}
          onSuccess={() => basementQuery.refetch()}
        />
      )}
    </div>
  );
};

function formatRelativeTime(
  iso: string | null | undefined,
  lang: string,
  t: (key: MessageKey, params?: Record<string, unknown>) => string,
): string {
  if (!iso) return t('basement.relative.none');
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return t('basement.relative.none');
  const diff = Date.now() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return t('basement.relative.justNow');
  if (minutes < 60) return t('basement.relative.minutes', { count: minutes });
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return t('basement.relative.hours', { count: hours });
  const days = Math.floor(hours / 24);
  if (days < 7) return t('basement.relative.days', { count: days });
  try {
    return date.toLocaleDateString(lang, { month: '2-digit', day: '2-digit' });
  } catch {
    return date.toLocaleDateString();
  }
}

export default BasementMainWidget;