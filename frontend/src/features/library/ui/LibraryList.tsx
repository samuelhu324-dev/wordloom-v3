'use client';

import React, { useMemo, useState } from 'react';
import {
  Archive as ArchiveIcon,
  BookOpen,
  Edit3,
  Eye,
  Library as LibraryIcon,
  Pin,
  PinOff,
  RotateCcw,
  Trash2,
} from 'lucide-react';
import type { LibraryDto } from '@/entities/library';
import { LibraryCoverAvatar } from '@/entities/library';
import type { LibrarySortOption } from '../model/api';
import { useLibraries, useRecordLibraryView, useQuickUpdateLibrary } from '../model/hooks';
import { useLibraryMetrics } from '../model/useLibraryMetrics';
import { LibraryCard } from './LibraryCard';
import { LibraryTagsRow } from './LibraryTagsRow';
import listStyles from './LibraryList.module.css';
import { LibraryCardSkeleton } from './LibraryCardSkeleton';
import { showToast } from '@/shared/ui/toast';
import { useI18n } from '@/i18n/useI18n';

export interface LibraryListProps {
  onSelectLibrary?: (id: string) => void;
  onEditLibrary?: (library: LibraryDto) => void;
  onDeleteLibrary?: (id: string) => void;
  viewMode?: 'grid' | 'list';
  search?: string;
  sort?: LibrarySortOption;
  includeArchived?: boolean;
  highlightedLibraryId?: string;
  initialData?: LibraryDto[];
}

interface LibrarySection {
  key: string;
  title: string;
  items: LibraryDto[];
}

const parseTimestamp = (value?: string | null) => {
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
};

const sortLibrariesForPresentation = (a: LibraryDto, b: LibraryDto) => {
  const aPinned = Boolean(a.pinned);
  const bPinned = Boolean(b.pinned);
  if (aPinned && !bPinned) return -1;
  if (!aPinned && bPinned) return 1;
  const updatedDiff = parseTimestamp(b.updated_at) - parseTimestamp(a.updated_at);
  if (updatedDiff !== 0) return updatedDiff;
  return parseTimestamp(b.created_at) - parseTimestamp(a.created_at);
};

const LIST_VIEW_COVER_SIZE = 96;

const descriptionClampStyle: React.CSSProperties = {
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
  whiteSpace: 'normal',
  color: 'var(--color-text-secondary)',
  maxWidth: '100%',
};

const RELATIVE_TABLE: Array<{ unit: Intl.RelativeTimeFormatUnit; seconds: number }> = [
  { unit: 'year', seconds: 60 * 60 * 24 * 365 },
  { unit: 'month', seconds: 60 * 60 * 24 * 30 },
  { unit: 'week', seconds: 60 * 60 * 24 * 7 },
  { unit: 'day', seconds: 60 * 60 * 24 },
  { unit: 'hour', seconds: 60 * 60 },
  { unit: 'minute', seconds: 60 },
  { unit: 'second', seconds: 1 },
];

const EN_RELATIVE_UNIT_LABELS: Partial<Record<Intl.RelativeTimeFormatUnit, { singular: string; plural: string }>> = {
  year: { singular: 'yr', plural: 'yrs' },
  month: { singular: 'mo', plural: 'mos' },
  week: { singular: 'wk', plural: 'wks' },
  day: { singular: 'day', plural: 'days' },
  hour: { singular: 'hr', plural: 'hrs' },
  minute: { singular: 'min', plural: 'mins' },
  second: { singular: 'sec', plural: 'secs' },
};

function formatEnglishRelative(value: number, unit: Intl.RelativeTimeFormatUnit): string {
  const absValue = Math.abs(value);
  const labels = EN_RELATIVE_UNIT_LABELS[unit] ?? { singular: unit, plural: `${unit}s` };
  if (absValue === 0) {
    return unit === 'second' ? 'just now' : `0 ${labels.plural}`;
  }
  const unitLabel = absValue === 1 ? labels.singular : labels.plural;
  return value < 0 ? `${absValue} ${unitLabel} ago` : `in ${absValue} ${unitLabel}`;
}

function formatRelative(iso: string | null | undefined, formatter?: Intl.RelativeTimeFormat, locale = 'zh-CN'): string {
  if (!iso) return '—';
  const timestamp = new Date(iso).getTime();
  if (Number.isNaN(timestamp)) return '—';
  const deltaSeconds = Math.round((timestamp - Date.now()) / 1000);
  const absSeconds = Math.abs(deltaSeconds);
  for (const entry of RELATIVE_TABLE) {
    if (absSeconds >= entry.seconds || entry.unit === 'second') {
      const value = Math.round(deltaSeconds / entry.seconds);
      if (locale?.startsWith('en')) {
        return formatEnglishRelative(value, entry.unit);
      }
      if (formatter) {
        return formatter.format(value, entry.unit);
      }
      return `${value} ${entry.unit}`;
    }
  }
  return '—';
}

function formatDate(iso?: string | null, locale = 'zh-CN'): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  try {
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return date.toLocaleDateString();
  }
}

function createRelativeTimeFormatter(locale: string): Intl.RelativeTimeFormat | undefined {
  if (typeof Intl === 'undefined') return undefined;
  try {
    return new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  } catch {
    return undefined;
  }
}

export const LibraryList: React.FC<LibraryListProps> = ({
  onSelectLibrary,
  onEditLibrary,
  onDeleteLibrary,
  viewMode = 'grid',
  search,
  sort,
  includeArchived = false,
  highlightedLibraryId,
  initialData,
}) => {
  const { t, lang } = useI18n();
  const relativeFormatter = useMemo(() => createRelativeTimeFormatter(lang), [lang]);

  const {
    data,
    isLoading,
    isInitialLoading,
    isFetching,
    error,
    fetchStatus,
  } = useLibraries(
    {
      query: search,
      sort,
      includeArchived,
    },
    initialData,
  );

  const libraries = data ?? initialData ?? [];
  const visibleLibraries = libraries;
  const hasLibraries = visibleLibraries.length > 0;
  const cached = isFetching && fetchStatus === 'idle';

  const recordView = useRecordLibraryView();
  const quickUpdate = useQuickUpdateLibrary();
  const isUpdating = quickUpdate.isPending;
  const [hoveredLibraryId, setHoveredLibraryId] = useState<string | null>(null);

  const { metrics } = useLibraryMetrics(visibleLibraries);

  const sections = useMemo<LibrarySection[]>(() => {
    if (!hasLibraries) return [];

    const active = visibleLibraries
      .filter((library) => !library.archived_at)
      .slice()
      .sort(sortLibrariesForPresentation);
    const archivedList = (includeArchived
      ? visibleLibraries.filter((library) => Boolean(library.archived_at))
      : [])
      .slice()
      .sort(sortLibrariesForPresentation);

    const list: LibrarySection[] = [];
    if (active.length) list.push({ key: 'active', title: t('libraries.list.section.all'), items: active });
    if (archivedList.length) list.push({ key: 'archived', title: t('libraries.list.section.archived'), items: archivedList });
    if (!list.length) list.push({ key: 'all', title: t('libraries.list.section.all'), items: visibleLibraries });
    return list;
  }, [hasLibraries, visibleLibraries, includeArchived, t]);

  const handleSelect = (id: string) => {
    onSelectLibrary?.(id);
    recordView.mutate(id);
  };

  const handleTogglePin = (library: LibraryDto) => {
    // 立即在前端缓存中体现 pinned 变化，复用 quickUpdate 的缓存写入逻辑
    quickUpdate.mutate({ libraryId: library.id, data: { pinned: !library.pinned } });
  };

  const handleToggleArchive = (library: LibraryDto) => {
    // 立即在前端缓存中体现 archived 变化，复用 quickUpdate 的缓存写入逻辑
    quickUpdate.mutate({ libraryId: library.id, data: { archived: !library.archived_at } });
  };

  if (isInitialLoading) {
    const skeletonCount = viewMode === 'list' ? 4 : 6;
    const skeletonClass = viewMode === 'list' ? listStyles.skeletonList : listStyles.skeletonGrid;
    return (
      <div className={skeletonClass} aria-live="polite" aria-busy>
        {Array.from({ length: skeletonCount }).map((_, index) => (
          <LibraryCardSkeleton key={index} variant={viewMode} />
        ))}
      </div>
    );
  }

  if (error) {
    return <div style={{ color: 'var(--color-danger)' }}>{t('libraries.list.error.loadFailed')}</div>;
  }

  if (!hasLibraries) {
    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 'var(--spacing-lg)',
          color: 'var(--color-text-secondary)',
        }}
      >
        <div style={{ gridColumn: '1 / -1', fontSize: 'var(--font-size-md)' }}>{t('libraries.list.empty.title')}</div>
        <div
          style={{ gridColumn: '1 / -1', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-tertiary)' }}
        >
          {t('libraries.list.empty.subtitle')}
        </div>
      </div>
    );
  }

  if (viewMode === 'list') {
    const listGridTemplate = '120px 120px minmax(210px, 1fr) minmax(150px, max-content) minmax(260px, max-content)';
    const headerRow = (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: listGridTemplate,
          padding: '14px 12px',
          fontSize: 'var(--font-size-xs)',
          textTransform: 'uppercase',
          letterSpacing: '.5px',
          color: 'var(--color-text-secondary)',
          columnGap: 'var(--spacing-sm)',
          alignItems: 'center',
        }}
      >
        <div>{t('libraries.list.columns.cover')}</div>
        <div>{t('libraries.list.columns.name')}</div>
        <div>{t('libraries.list.columns.description')}</div>
        <div>{t('libraries.list.columns.metrics')}</div>
        <div>{t('libraries.list.columns.timestamps')}</div>
      </div>
    );

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {sections.map((section) => (
          <React.Fragment key={section.key}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-xs)',
                padding: '12px 0 4px',
                color: 'var(--color-text-tertiary)',
                fontSize: 'var(--font-size-xs)',
                textTransform: 'uppercase',
                letterSpacing: '.4px',
              }}
            >
              <span>{section.title}</span>
            </div>
            {headerRow}
            {section.items.map((library) => {
              const isHovered = hoveredLibraryId === library.id;
              const libraryMetrics = metrics[library.id] ?? {};
              const bookshelvesCount = libraryMetrics.bookshelves;
              const booksCount = libraryMetrics.books;
              const viewsCount = library.views_count ?? 0;
              const resolvedBookshelvesCount = bookshelvesCount == null ? 1 : Math.max(1, bookshelvesCount);
              const bookshelvesTooltip = t('libraries.list.tooltip.bookshelves', { count: resolvedBookshelvesCount });
              const booksTooltip = booksCount == null
                ? t('libraries.list.tooltip.booksUnknown')
                : t('libraries.list.tooltip.books', { count: booksCount });
              const viewsTooltip = t('libraries.list.tooltip.views', { count: viewsCount });
              const editTooltip = t('libraries.list.actions.edit');
              const deleteTooltip = t('libraries.list.actions.delete');
              const pinTooltip = library.pinned ? t('libraries.list.actions.unpin') : t('libraries.list.actions.pin');
              const archiveTooltip = library.archived_at
                ? t('libraries.list.actions.restore')
                : t('libraries.list.actions.archive');
              return (
                <div
                  key={library.id}
                  onClick={() => handleSelect(library.id)}
                  onMouseEnter={() => setHoveredLibraryId(library.id)}
                  onMouseLeave={() => setHoveredLibraryId((prev) => (prev === library.id ? null : prev))}
                  style={{
                    position: 'relative',
                    display: 'grid',
                    gridTemplateColumns: listGridTemplate,
                    padding: '16px 12px',
                    cursor: 'pointer',
                    background: isHovered ? 'var(--color-surface-hover)' : 'var(--color-surface)',
                    border: '1px solid var(--color-border-light)',
                    borderRadius: 'var(--radius-lg)',
                    margin: '4px 0',
                    fontSize: 'var(--font-size-sm)',
                    transition: 'background var(--transition-fast), box-shadow var(--transition-fast)',
                    columnGap: 'var(--spacing-sm)',
                    alignItems: 'center',
                    boxShadow: isHovered ? '0 4px 16px rgba(15,23,42,0.08)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <LibraryCoverAvatar
                      libraryId={library.id}
                      name={library.name}
                      coverUrl={library.coverUrl}
                      size={LIST_VIEW_COVER_SIZE}
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontWeight: 600 }}>
                    <div className={listStyles.statusRow}>
                      {library.pinned && (
                        <span
                          className={`${listStyles.statusBadge} ${listStyles.statusBadgePinned} ${listStyles.tooltipAnchor}`}
                          data-tooltip={t('libraries.list.status.pinned')}
                          aria-label={t('libraries.list.status.pinned')}
                        >
                          {t('libraries.list.status.pinned')}
                        </span>
                      )}
                      {library.archived_at && (
                        <span
                          className={`${listStyles.statusBadge} ${listStyles.statusBadgeArchived} ${listStyles.tooltipAnchor}`}
                          data-tooltip={t('libraries.list.status.archived')}
                          aria-label={t('libraries.list.status.archived')}
                        >
                          {t('libraries.list.status.archived')}
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: '1rem', color: 'var(--color-text-secondary)' }}>{library.name}</span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 8,
                      width: '100%',
                      maxWidth: 390,
                      paddingLeft: 'var(--spacing-xs)',
                    }}
                  >
                    <span style={descriptionClampStyle} title={library.description?.trim() || undefined}>
                      {library.description?.trim() || t('libraries.list.description.empty')}
                    </span>
                    <LibraryTagsRow
                      tags={library.tags}
                      total={library.tag_total_count}
                      placeholder={t('libraries.tags.placeholder')}
                      size="compact"
                      className="wl-list-tags"
                    />
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '10px',
                      fontSize: '0.78rem',
                      color: 'var(--color-text-tertiary)',
                      justifySelf: 'flex-start',
                    }}
                  >
                    <span
                      className={listStyles.tooltipAnchor}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        opacity: 1,
                      }}
                      data-tooltip={bookshelvesTooltip}
                      aria-label={bookshelvesTooltip}
                    >
                      <LibraryIcon size={14} /> {resolvedBookshelvesCount}
                    </span>
                    <span
                      className={listStyles.tooltipAnchor}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        opacity: booksCount == null ? 0.55 : 1,
                      }}
                      data-tooltip={booksTooltip}
                      aria-label={booksTooltip}
                    >
                      <BookOpen size={14} /> {booksCount ?? '—'}
                    </span>
                    <span
                      className={listStyles.tooltipAnchor}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                      data-tooltip={viewsTooltip}
                      aria-label={viewsTooltip}
                    >
                      <Eye size={14} /> {viewsCount}
                    </span>
                  </div>
                  <div
                    style={{
                      color: 'var(--color-text-tertiary)',
                      fontSize: '0.78rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 4,
                      justifySelf: 'flex-start',
                    }}
                  >
                    <span>{t('libraries.list.meta.created')} {formatDate(library.created_at, lang)}</span>
                    <span style={{ whiteSpace: 'nowrap' }}>
                      {t('libraries.list.meta.updated')} {formatDate(library.updated_at, lang)}（{formatRelative(library.updated_at, relativeFormatter, lang)}）
                    </span>
                  </div>
                  <div
                    style={{
                      position: 'absolute',
                      top: 12,
                      right: 12,
                      display: 'flex',
                      gap: '8px',
                      opacity: isHovered ? 1 : 0,
                      pointerEvents: isHovered ? 'auto' : 'none',
                      transition: 'opacity var(--transition-fast)',
                    }}
                  >
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditLibrary?.(library);
                      }}
                      style={{
                        padding: '6px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border-light)',
                        background: 'var(--color-surface-alt)',
                        color: 'var(--color-text-secondary)',
                        cursor: isUpdating ? 'wait' : 'pointer',
                      }}
                      className={listStyles.tooltipAnchor}
                      data-tooltip={editTooltip}
                      aria-label={editTooltip}
                    >
                      <Edit3 size={16} />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        showToast(t('libraries.card.toast.deletePlaceholder'));
                        onDeleteLibrary?.(library.id);
                      }}
                      style={{
                        padding: '6px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border-light)',
                        background: 'var(--color-surface-alt)',
                        color: 'var(--color-text-secondary)',
                        cursor: isUpdating ? 'wait' : 'pointer',
                      }}
                      className={listStyles.tooltipAnchor}
                      data-tooltip={deleteTooltip}
                      aria-label={deleteTooltip}
                      disabled={isUpdating}
                    >
                      <Trash2 size={16} />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTogglePin(library);
                      }}
                      disabled={isUpdating}
                      style={{
                        padding: '6px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border-light)',
                        background: 'var(--color-surface-alt)',
                        color: 'var(--color-text-secondary)',
                        cursor: isUpdating ? 'wait' : 'pointer',
                      }}
                      className={listStyles.tooltipAnchor}
                      data-tooltip={pinTooltip}
                      aria-label={pinTooltip}
                    >
                      {library.pinned ? <PinOff size={16} /> : <Pin size={16} />}
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleArchive(library);
                      }}
                      disabled={isUpdating}
                      style={{
                        padding: '6px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border-light)',
                        background: 'var(--color-surface-alt)',
                        color: 'var(--color-text-secondary)',
                        cursor: isUpdating ? 'wait' : 'pointer',
                      }}
                      className={listStyles.tooltipAnchor}
                      data-tooltip={archiveTooltip}
                      aria-label={archiveTooltip}
                    >
                      {library.archived_at ? <RotateCcw size={16} /> : <ArchiveIcon size={16} />}
                    </button>
                  </div>
                </div>
              );
            })}
          </React.Fragment>
        ))}
                      {cached && (
          <div
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              padding: '4px 8px',
            }}
          >
            {t('libraries.list.cacheNotice')}
          </div>
        )}
                      <div
                        style={{
                          fontSize: 'var(--font-size-sm)',
                          color: 'var(--color-text-tertiary)',
                          marginTop: 'var(--spacing-lg)',
                          padding: '0 12px 8px',
                        }}
                      >
                        <span>{t('libraries.list.basementHint.prefix')}</span>
                        <a
                          href="/admin/basement"
                          style={{
                            color: 'var(--color-primary)',
                            textDecoration: 'underline',
                            textDecorationStyle: 'dashed',
                            textDecorationThickness: '1.5px',
                            margin: '0 4px',
                          }}
                        >
                          {t('libraries.list.basementHint.link')}
                        </a>
                        <span>{t('libraries.list.basementHint.suffix')}</span>
                      </div>
      </div>
    );
  }

  return (
    <div
      style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--spacing-lg)' }}
    >
      {sections.length
        ? sections.map((section) => (
            <React.Fragment key={section.key}>
              <div
                style={{
                  gridColumn: '1 / -1',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--spacing-xs)',
                  color: 'var(--color-text-tertiary)',
                  fontSize: 'var(--font-size-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '.4px',
                }}
              >
                <span>{section.title}</span>
              </div>
              {section.items.map((library) => (
                <LibraryCard
                  key={library.id}
                  library={library}
                  onClick={handleSelect}
                  onEdit={onEditLibrary}
                  onDelete={onDeleteLibrary}
                  bookshelvesCount={metrics[library.id]?.bookshelves}
                  booksCount={metrics[library.id]?.books}
                  onTogglePin={handleTogglePin}
                  onToggleArchive={handleToggleArchive}
                  actionsDisabled={isUpdating}
                  className={library.id === highlightedLibraryId ? 'wl-highlighted' : undefined}
                />
              ))}
            </React.Fragment>
          ))
        : visibleLibraries.map((library) => (
            <LibraryCard
              key={library.id}
              library={library}
              onClick={handleSelect}
              onEdit={onEditLibrary}
              onDelete={onDeleteLibrary}
              bookshelvesCount={metrics[library.id]?.bookshelves}
              booksCount={metrics[library.id]?.books}
              onTogglePin={handleTogglePin}
              onToggleArchive={handleToggleArchive}
              actionsDisabled={isUpdating}
              className={library.id === highlightedLibraryId ? 'wl-highlighted' : undefined}
            />
          ))}
      {cached && isLoading && (
        <div style={{ gridColumn: '1 / -1', fontSize: 12, color: 'var(--color-text-muted)' }}>
          {t('libraries.list.cacheNotice')}
        </div>
      )}
      <div
        style={{
          gridColumn: '1 / -1',
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-tertiary)',
          marginTop: 'var(--spacing-sm)',
        }}
      >
        <span>{t('libraries.list.basementHint.prefix')}</span>
        <a
          href="/admin/basement"
          style={{
            color: 'var(--color-primary)',
            textDecoration: 'underline',
            textDecorationStyle: 'dashed',
            textDecorationThickness: '1.5px',
            margin: '0 4px',
          }}
        >
          {t('libraries.list.basementHint.link')}
        </a>
        <span>{t('libraries.list.basementHint.suffix')}</span>
      </div>
    </div>
  );
};
