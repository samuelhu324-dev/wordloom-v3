import {
  Library as LibraryIcon,
  Sprout,
  TreeDeciduous,
  BookOpen,
  Archive,
  Edit3,
  Eye,
  Pin,
  PinOff,
  ArchiveRestore,
  Trash2,
  Clock,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { KeyboardEvent } from 'react';
import type { BookshelfDashboardItemDto, BookshelfDashboardCounts } from '@/entities/bookshelf';
import { LibraryCoverAvatar } from '@/entities/library';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import { buildMediaFileUrl } from '@/shared/api';
import { resolveTagDescription as resolveTagDescriptionFromMap } from '@/features/tag/lib/tagCatalog';
import styles from './BookshelfDashboardBoard.module.css';

export interface BookshelfDashboardCardProps {
  item: BookshelfDashboardItemDto;
  libraryName?: string;
  tagDescriptionsMap?: Record<string, string>;
  onEdit?: (item: BookshelfDashboardItemDto) => void;
  onPinToggle?: (item: BookshelfDashboardItemDto) => void;
  onArchiveToggle?: (item: BookshelfDashboardItemDto) => void;
  onDelete?: (item: BookshelfDashboardItemDto) => void;
  onOpen?: (item: BookshelfDashboardItemDto) => void;
  actionsDisabled?: boolean;
}

const MATURITY_ITEMS: Array<{
  key: keyof BookshelfDashboardCounts;
  labelKey: MessageKey;
  Icon: typeof Sprout;
}> = [
  { key: 'seed', labelKey: 'bookshelves.card.maturity.seed', Icon: Sprout },
  { key: 'growing', labelKey: 'bookshelves.card.maturity.growing', Icon: TreeDeciduous },
  { key: 'stable', labelKey: 'bookshelves.card.maturity.stable', Icon: BookOpen },
  { key: 'legacy', labelKey: 'bookshelves.card.maturity.legacy', Icon: Archive },
];

const MAX_TAGS = 3;

type TagCandidate = {
  id?: string | null;
  name?: string | null;
  color?: string | null;
  description?: string | null;
};

const sortTagsByName = <T extends { name: string }>(tags: T[]): T[] =>
  [...tags].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN', { sensitivity: 'accent', numeric: true }));

export const BookshelfDashboardCard = ({
  item,
  libraryName,
  tagDescriptionsMap,
  onEdit,
  onPinToggle,
  onArchiveToggle,
  onDelete,
  onOpen,
  actionsDisabled,
}: BookshelfDashboardCardProps) => {
  const { t, lang } = useI18n();
  const resolvedCoverUrl = item.cover_media_id
    ? buildMediaFileUrl(item.cover_media_id, item.updated_at)
    : undefined;

  const maturityItems = MATURITY_ITEMS.map(({ key, labelKey, Icon }) => ({
    key,
    Icon,
    label: t(labelKey),
  }));
  const formatRelativeValue = (value?: string | null): string => {
    if (!value) return '';
    const ts = new Date(value).getTime();
    if (Number.isNaN(ts)) return '';
    const diff = Date.now() - ts;
    const MINUTE = 60 * 1000;
    const HOUR = 60 * MINUTE;
    const DAY = 24 * HOUR;
    if (diff < HOUR) {
      return t('bookshelves.card.relative.minutes', { count: Math.max(1, Math.floor(diff / MINUTE)) });
    }
    if (diff < DAY) {
      return t('bookshelves.card.relative.hours', { count: Math.floor(diff / HOUR) });
    }
    if (diff < 7 * DAY) {
      return t('bookshelves.card.relative.days', { count: Math.floor(diff / DAY) });
    }
    const formatted = new Date(ts).toLocaleDateString(lang);
    return t('bookshelves.card.relative.date', { value: formatted });
  };

  const fromMeta: TagCandidate[] = Array.isArray(item.tagsMeta)
    ? (item.tagsMeta as TagCandidate[])
    : Array.isArray((item as { tags?: TagCandidate[] }).tags)
      ? ((item as { tags?: TagCandidate[] }).tags ?? [])
      : [];

  const normalizedMeta = fromMeta
    .map((tag, index) => {
      const trimmed = (tag.name ?? '').trim();
      if (!trimmed) return null;
      return {
        id: tag.id || item.tagIds?.[index] || `${trimmed}-${index}`,
        name: trimmed,
        color: tag.color || '#E2E8F0',
        description: tag.description ?? undefined,
      };
    })
    .filter(Boolean) as Array<{ id: string; name: string; color: string; description?: string }>;

  const fallbackNames = normalizedMeta.length === 0 && Array.isArray(item.tagsSummary)
    ? item.tagsSummary
        .map((name, index) => {
          const trimmed = (name ?? '').trim();
          if (!trimmed) return null;
          return {
            id: item.tagIds?.[index] || `${trimmed}-${index}`,
            name: trimmed,
            color: '#E2E8F0',
            description: undefined,
          };
        })
        .filter(Boolean) as Array<{ id: string; name: string; color: string; description?: string }>
    : [];

  const effectiveTagsBase = normalizedMeta.length > 0 ? normalizedMeta : fallbackNames;
  const hydratedTags = effectiveTagsBase.map((tag) => {
    if (tag.description && tag.description.trim()) {
      return tag;
    }
    if (!tagDescriptionsMap) {
      return tag;
    }
    const resolved = resolveTagDescriptionFromMap(tag.name, tagDescriptionsMap, { libraryId: item.library_id });
    return resolved ? { ...tag, description: resolved } : tag;
  });
  const effectiveTags = sortTagsByName(hydratedTags);
  const visibleTags = effectiveTags.slice(0, MAX_TAGS);
  const extraTagCount = effectiveTags.length > MAX_TAGS ? effectiveTags.length - MAX_TAGS : 0;

  const isPinned = Boolean(item.is_pinned);
  const normalizedStatus = (item.status || '').toLowerCase();
  const isArchived = Boolean(item.is_archived || normalizedStatus === 'archived');
  const statusDescription = isArchived
    ? t('bookshelves.card.statusDescription.archived')
    : t('bookshelves.card.statusDescription.active');
  const pinnedTooltip = t('bookshelves.card.tooltip.pinnedBadge');
  const archivedTooltip = t('bookshelves.card.tooltip.archivedBadge');
  const activeTooltip = t('bookshelves.card.tooltip.activeBadge');

  const totalBooksTitle = t('bookshelves.card.metrics.totalBooks', { count: item.book_counts.total });
  const editsTitle = t('bookshelves.card.metrics.edits7d', { count: item.edits_last_7d });
  const viewsTitle = t('bookshelves.card.metrics.views7d', { count: item.views_last_7d });
  const relativeLastActivity = formatRelativeValue(item.last_activity_at) || t('bookshelves.card.relative.none');
  const lastActivityTitle = t('bookshelves.card.metrics.lastActive', { value: relativeLastActivity });

  const handleRowClick = () => {
    onOpen?.(item);
  };

  const handleRowKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!onOpen) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onOpen(item);
    }
  };

  const rowClassName = [styles.row, onOpen ? styles.rowInteractive : '']
    .filter(Boolean)
    .join(' ');

  type ActionDef = {
    label: string;
    tooltip: string;
    Icon: LucideIcon;
    handler?: (item: BookshelfDashboardItemDto) => void;
    ariaPressed?: boolean;
    intent: 'default' | 'danger';
  };

  const actions: ActionDef[] = [
    {
      label: isPinned ? t('bookshelves.card.actions.unpin') : t('bookshelves.card.actions.pin'),
      tooltip: isPinned ? t('bookshelves.card.tooltip.unpin') : t('bookshelves.card.tooltip.pin'),
      Icon: isPinned ? PinOff : Pin,
      handler: onPinToggle,
      ariaPressed: isPinned,
      intent: 'default',
    },
    {
      label: t('bookshelves.card.actions.edit'),
      tooltip: t('bookshelves.card.tooltip.edit'),
      Icon: Edit3,
      handler: onEdit,
      intent: 'default',
    },
    {
      label: isArchived ? t('bookshelves.card.actions.restore') : t('bookshelves.card.actions.archive'),
      tooltip: isArchived ? t('bookshelves.card.tooltip.restore') : t('bookshelves.card.tooltip.archive'),
      Icon: isArchived ? ArchiveRestore : Archive,
      handler: onArchiveToggle,
      intent: 'default',
    },
    {
      label: t('bookshelves.card.actions.delete'),
      tooltip: t('bookshelves.card.tooltip.delete'),
      Icon: Trash2,
      handler: onDelete,
      intent: 'danger',
    },
  ];

  return (
    <div
      className={rowClassName}
      role="row"
      tabIndex={onOpen ? 0 : undefined}
      onClick={onOpen ? handleRowClick : undefined}
      onKeyDown={onOpen ? handleRowKeyDown : undefined}
      aria-label={onOpen ? t('bookshelves.card.aria.open', { name: item.name || '' }) : undefined}
    >
      <div className={styles.cellCover} role="gridcell">
        <LibraryCoverAvatar
          libraryId={item.library_id}
          name={libraryName || item.name}
          coverUrl={resolvedCoverUrl}
          size="var(--bs-avatar-size)"
        />
      </div>

      <div className={styles.cellName} role="gridcell">
        <div className={styles.nameLine}>
          <span>{item.name}</span>
        </div>
      </div>

      <div className={styles.cellTags} role="gridcell">
        <div className={styles.tagBadges}>
          {isPinned && (
            <span
              className={`${styles.pinnedBadge} ${styles.tooltipAnchor}`}
              data-tooltip={pinnedTooltip}
              aria-label={pinnedTooltip}
            >
              {t('bookshelves.card.badge.pinned')}
            </span>
          )}
          {isArchived ? (
            <span
              className={`${styles.archivedBadge} ${styles.tooltipAnchor}`}
              data-tooltip={statusDescription}
              aria-label={statusDescription}
            >
              {t('bookshelves.card.badge.archived')}
            </span>
          ) : (
            <span
              className={`${styles.activeBadge} ${styles.tooltipAnchor}`}
              data-tooltip={statusDescription || activeTooltip}
              aria-label={statusDescription || activeTooltip}
            >
              {t('bookshelves.card.badge.active')}
            </span>
          )}
        </div>
        <div className={styles.tagsBlock}>
          {visibleTags.length > 0 ? (
            <div className={styles.tagsRow} role="list">
              {visibleTags.map((tag) => (
                <span
                  key={tag.id}
                  role="listitem"
                  className={`${styles.tagChip} ${styles.tooltipAnchor}`}
                  data-tooltip={tag.description ? `${tag.name}｜${tag.description}` : tag.name}
                  aria-label={tag.description ? `${tag.name}：${tag.description}` : tag.name}
                  tabIndex={tag.description ? 0 : undefined}
                >
                  <span className={styles.tagChipLabel}>
                    {tag.name.length > 12 ? `${tag.name.slice(0, 12)}…` : tag.name}
                  </span>
                </span>
              ))}
              {extraTagCount > 0 && (
                <span
                  className={`${styles.tagChipMore} ${styles.tooltipAnchor}`}
                    data-tooltip={t('bookshelves.card.tooltip.extraTags', { count: extraTagCount })}
                    aria-label={t('bookshelves.card.tooltip.extraTags', { count: extraTagCount })}
                >
                  +{extraTagCount}
                </span>
              )}
            </div>
          ) : (
              <span className={styles.tagsEmpty}>{t('bookshelves.card.tags.empty')}</span>
          )}
        </div>
      </div>

      <div className={styles.cellStatus} role="gridcell">
        <div className={styles.statusMaturityLine} role="list">
          {maturityItems.map(({ key, label, Icon }) => {
            const count = item.book_counts[key];
            const maturityTitle = t('bookshelves.card.maturity.tooltip', { label, count });
            return (
              <span
                key={key}
                className={`${styles.maturityItem} ${styles.tooltipAnchor}`}
                role="listitem"
                data-tooltip={maturityTitle}
                aria-label={maturityTitle}
              >
                <Icon size={14} className={styles.iconMuted} aria-hidden="true" />
                <span>{count}</span>
              </span>
            );
          })}
        </div>
      </div>

      <div className={styles.cellMetrics} role="gridcell">
        <span className={styles.tooltipAnchor} data-tooltip={totalBooksTitle} aria-label={totalBooksTitle}>
          <LibraryIcon size={14} className={styles.iconMuted} aria-hidden="true" />
          {item.book_counts.total}
        </span>
        <span className={styles.tooltipAnchor} data-tooltip={editsTitle} aria-label={editsTitle}>
          <Edit3 size={14} className={styles.iconMuted} aria-hidden="true" />
          {item.edits_last_7d}
        </span>
        <span className={styles.tooltipAnchor} data-tooltip={viewsTitle} aria-label={viewsTitle}>
          <Eye size={14} className={styles.iconMuted} aria-hidden="true" />
          {item.views_last_7d}
        </span>
        <span className={styles.tooltipAnchor} data-tooltip={lastActivityTitle} aria-label={lastActivityTitle}>
          <Clock size={14} className={styles.iconMuted} aria-hidden="true" />
          {relativeLastActivity}
        </span>
      </div>

      <div className={styles.cellActions} role="gridcell">
        {actions.map(({ label, tooltip, Icon, handler, ariaPressed, intent }) => (
          <button
            key={label}
            type="button"
            className={`${styles.actionButton} ${styles.tooltipAnchor} ${intent === 'danger' ? styles.actionDanger : ''}`}
            onClick={handler
              ? (event) => {
                  event.stopPropagation();
                  handler(item);
                }
              : undefined}
            data-tooltip={tooltip || label}
            aria-label={tooltip || label}
            aria-pressed={typeof ariaPressed === 'boolean' ? ariaPressed : undefined}
            disabled={actionsDisabled || !handler}
          >
            <Icon size={16} aria-hidden="true" />
          </button>
        ))}
      </div>
    </div>
  );
};

BookshelfDashboardCard.displayName = 'BookshelfDashboardCard';
