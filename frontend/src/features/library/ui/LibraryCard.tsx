'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Image,
  Trash2,
  Edit3,
  Eye,
  Library as LibraryIcon,
  BookOpen,
  Pin,
  PinOff,
  Archive,
  ArchiveRestore,
} from 'lucide-react';
import { LibraryDto } from '@/entities/library';
import { DEFAULT_LIBRARY_SILVER_GRADIENT } from '@/entities/library';
import { showToast } from '@/shared/ui/toast';
import { uploadLibraryCover } from '../model/api';
import styles from './LibraryCard.module.css';
import { LibraryTagsRow } from './LibraryTagsRow';
import { useI18n } from '@/i18n/useI18n';

export interface LibraryCardProps {
  library: LibraryDto;
  onEdit?: (library: LibraryDto) => void;
  onDelete?: (id: string) => void;
  onClick?: (id: string) => void;
  bookshelvesCount?: number | null;
  booksCount?: number | null;
  onTogglePin?: (library: LibraryDto) => void;
  onToggleArchive?: (library: LibraryDto) => void;
  actionsDisabled?: boolean;
  className?: string;
}

const COVER_SIZE_LIMIT = 10 * 1024 * 1024; // 10MB

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

function formatRelative(isoDate?: string | null, formatter?: Intl.RelativeTimeFormat, locale = 'zh-CN'): string {
  if (!isoDate) return '—';
  const timestamp = new Date(isoDate).getTime();
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

export const LibraryCard: React.FC<LibraryCardProps> = ({
  library,
  onEdit,
  onDelete,
  onClick,
  bookshelvesCount,
  booksCount,
  onTogglePin,
  onToggleArchive,
  actionsDisabled,
  className,
}) => {
  const { t, lang } = useI18n();
  const [coverUrl, setCoverUrl] = useState<string | null>(library.coverUrl ?? null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const relativeFormatter = useMemo(() => createRelativeTimeFormatter(lang), [lang]);

  const gradient = DEFAULT_LIBRARY_SILVER_GRADIENT;
  const isPinned = library.pinned;
  const isArchived = Boolean(library.archived_at);
  const descriptionTooltip = library.description?.trim();
  const bookshelvesTooltip = bookshelvesCount == null
    ? t('libraries.list.tooltip.bookshelvesUnknown')
    : t('libraries.list.tooltip.bookshelves', { count: bookshelvesCount });
  const booksTooltip = booksCount == null
    ? t('libraries.list.tooltip.booksUnknown')
    : t('libraries.list.tooltip.books', { count: booksCount });
  const viewsCount = library.views_count ?? 0;
  const viewsTooltip = t('libraries.list.tooltip.views', { count: viewsCount });
  const createdDate = formatDate(library.created_at, lang);
  const usageRelative = formatRelative(library.last_viewed_at, relativeFormatter, lang);

  useEffect(() => {
    setCoverUrl(library.coverUrl ?? null);
  }, [library.coverUrl, library.cover_media_id, library.updated_at]);

  const disableQuickActions = actionsDisabled || isUploading;

  const handleActivate = useCallback(
    (event?: React.MouseEvent<HTMLDivElement> | React.KeyboardEvent<HTMLDivElement>) => {
      if (uploadOpen) return;
      if (event) {
        const target = event.target as Node | null;
        if (overlayRef.current && target && overlayRef.current.contains(target)) return;
        if (dialogRef.current && target && dialogRef.current.contains(target)) return;
      }
      if (!onClick) return;
      onClick(library.id);
    },
    [uploadOpen, onClick, library.id]
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleActivate(event);
      }
    },
    [handleActivate]
  );

  let rootClassName = onClick ? `${styles.cardRoot} ${styles.clickable}` : styles.cardRoot;
  if (className) rootClassName += ` ${className}`;
  if (className === 'wl-highlighted') rootClassName += ` ${styles.highlighted}`;

  const isInteractive = Boolean(onClick);

  const handleCoverFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const input = event.target;
      const file = input.files?.[0];
      input.value = '';
      if (!file) return;

      if (!file.type.startsWith('image/')) {
        showToast(t('libraries.card.toast.imageType'));
        return;
      }

      if (file.size > COVER_SIZE_LIMIT) {
        showToast(t('libraries.card.toast.imageSize'));
        return;
      }

      setSelectedFileName(file.name);

      const previousCover = coverUrl;
      let previewUrl: string | null = null;
      let shouldCloseDialog = false;

      try {
        setIsUploading(true);
        previewUrl = URL.createObjectURL(file);
        setCoverUrl(previewUrl);

        const updated = await uploadLibraryCover(library.id, file);
        setCoverUrl(updated.coverUrl ?? null);
        showToast(t('libraries.card.toast.coverUpdated'));
        shouldCloseDialog = true;
      } catch (error) {
        console.error('[library] cover upload failed', error);
        showToast(t('libraries.card.toast.coverFailed'));
        setCoverUrl(previousCover ?? null);
      } finally {
        setIsUploading(false);
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl);
        }
        if (shouldCloseDialog) {
          setUploadOpen(false);
          setSelectedFileName(null);
        }
      }
    },
    [coverUrl, library.id, t]
  );

  return (
    <div
      className={rootClassName}
      role={isInteractive ? 'button' : 'group'}
      tabIndex={isInteractive ? 0 : -1}
      aria-label={t('libraries.card.ariaLabel', { name: library.name })}
      onClick={isInteractive ? handleActivate : undefined}
      onKeyDown={isInteractive ? handleKeyDown : undefined}
    >
      <div
        ref={overlayRef}
        className={styles.actionsOverlay}
        aria-label={t('libraries.card.quickActionsAria')}
        onMouseDownCapture={(e) => e.stopPropagation()}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className={styles.actionButton}
          aria-label={isPinned ? t('libraries.list.actions.unpin') : t('libraries.list.actions.pin')}
          data-tooltip={isPinned ? t('libraries.list.actions.unpin') : t('libraries.list.actions.pin')}
          disabled={disableQuickActions}
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin?.(library);
          }}
        >
          {isPinned ? <PinOff size={16} /> : <Pin size={16} />}
        </button>
        <button
          type="button"
          className={styles.actionButton}
          aria-label={isArchived ? t('libraries.list.actions.restore') : t('libraries.list.actions.archive')}
          data-tooltip={isArchived ? t('libraries.list.actions.restore') : t('libraries.list.actions.archive')}
          disabled={disableQuickActions}
          onClick={(e) => {
            e.stopPropagation();
            onToggleArchive?.(library);
          }}
        >
          {isArchived ? <ArchiveRestore size={16} /> : <Archive size={16} />}
        </button>
        <button
          type="button"
          className={styles.actionButton}
          aria-label={t('libraries.card.actions.changeCover')}
          data-tooltip={t('libraries.card.actions.changeCover')}
          onClick={(e) => {
            e.stopPropagation();
            setSelectedFileName(null);
            setUploadOpen(true);
          }}
        >
          <Image size={16} />
        </button>
        <button
          type="button"
          className={styles.actionButton}
          aria-label={t('libraries.list.actions.edit')}
          data-tooltip={t('libraries.list.actions.edit')}
          disabled={disableQuickActions}
          onClick={(e) => {
            e.stopPropagation();
            onEdit?.(library);
          }}
        >
          <Edit3 size={16} />
        </button>
        <button
          type="button"
          className={styles.actionButton}
          aria-label={t('libraries.list.actions.delete')}
          data-tooltip={t('libraries.list.actions.delete')}
          onClick={(e) => {
            e.stopPropagation();
            showToast(t('libraries.card.toast.deletePlaceholder'));
            onDelete?.(library.id);
          }}
        >
          <Trash2 size={16} />
        </button>
      </div>

      <div
        className={styles.cover}
        aria-label={t('libraries.card.coverAria')}
        style={!coverUrl ? { background: gradient } : undefined}
      >
        {coverUrl ? (
          <img
            src={coverUrl}
            alt={t('libraries.card.coverAlt', { name: library.name })}
            style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', inset: 0 }}
          />
        ) : (
          <div className={styles.coverGradient} style={{ background: gradient }} />
        )}
        <div className={styles.coverOverlay} />
        <h3 className={styles.coverTitle}>{library.name}</h3>
      </div>

      {uploadOpen && (
        <div
          ref={dialogRef}
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(255,255,255,0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--card-radius)',
            zIndex: 20,
          }}
          role="dialog"
          aria-label={t('libraries.card.dialog.title')}
          onMouseDownCapture={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
        >
          <div
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border-soft)',
              padding: 'var(--spacing-lg)',
              borderRadius: 'var(--radius-md)',
              width: '280px',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--spacing-md)',
              boxShadow: 'var(--card-shadow)',
            }}
          >
            <h4 style={{ margin: 0, fontSize: 'var(--font-size-md)' }}>{t('libraries.card.dialog.title')}</h4>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              disabled={isUploading}
              aria-busy={isUploading}
              onChange={handleCoverFileChange}
              style={{ display: 'none' }}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                disabled={isUploading}
                style={{
                  background: 'var(--color-brand-soft)',
                  border: '1px solid var(--color-border-soft)',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 500,
                  color: 'var(--color-text-primary)',
                }}
              >
                {t('libraries.card.dialog.chooseFile')}
              </button>
              <span
                style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}
                aria-live="polite"
              >
                {selectedFileName
                  ? t('libraries.card.dialog.selectedFile', { name: selectedFileName })
                  : t('libraries.card.dialog.noFile')}
              </span>
            </div>
            {isUploading && (
              <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                {t('libraries.card.dialog.uploading')}
              </p>
            )}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--spacing-sm)' }}>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setUploadOpen(false);
                  setSelectedFileName(null);
                }}
                style={{
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: 'var(--font-size-sm)',
                }}
              >
                {t('button.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className={styles.body}>
        <div className={styles.titleRow}>
          <div className={styles.titleBlock}>
            <div className={styles.titleLine}>
              <h3 className={styles.title}>{library.name}</h3>
            </div>
            <div className={styles.tagsSection} aria-label={t('libraries.card.tagsAria')}>
              <LibraryTagsRow
                tags={library.tags}
                total={library.tag_total_count}
                placeholder={t('libraries.tags.placeholder')}
              />
            </div>
          </div>
          <div className={styles.badges}>
            {library.pinned && (
              <span
                className={`${styles.badge} ${styles.badgePinned}`}
                data-tooltip={t('libraries.list.status.pinned')}
                aria-label={t('libraries.list.status.pinned')}
              >
                {t('libraries.list.status.pinned')}
              </span>
            )}
            {library.archived_at && (
              <span
                className={`${styles.badge} ${styles.badgeArchived}`}
                data-tooltip={t('libraries.list.status.archived')}
                aria-label={t('libraries.list.status.archived')}
              >
                {t('libraries.list.status.archived')}
              </span>
            )}
          </div>
        </div>

        <div className={styles.metricsRow} aria-label={t('libraries.list.columns.metrics')}>
          <span
            className={styles.metricValue}
            style={{ opacity: bookshelvesCount == null ? 0.55 : 1 }}
            data-tooltip={bookshelvesTooltip}
            aria-label={bookshelvesTooltip}
          >
            <LibraryIcon size={12} /> {bookshelvesCount == null ? '—' : bookshelvesCount}
          </span>
          <span
            className={styles.metricValue}
            style={{ opacity: booksCount == null ? 0.55 : 1 }}
            data-tooltip={booksTooltip}
            aria-label={booksTooltip}
          >
            <BookOpen size={12} /> {booksCount == null ? '—' : booksCount}
          </span>
          <span className={styles.metricValue} data-tooltip={viewsTooltip} aria-label={viewsTooltip}>
            <Eye size={12} /> {viewsCount}
          </span>
        </div>

        <div className={styles.footer}>
          <span>{t('libraries.card.created', { date: createdDate })}</span>
          <span className={styles.usageStat} aria-label={t('libraries.card.usageAria')}>
            {t('libraries.card.usage', { relative: usageRelative })}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LibraryCard;
