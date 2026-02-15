"use client";

import React, { useEffect, useState } from 'react';
import { LibraryDto } from '@/entities/library';
import { Card, Button } from '@/shared/ui';
import { LibraryTagsRow } from './LibraryTagsRow';
import { useI18n } from '@/i18n/useI18n';

export interface LibraryCardHorizontalProps {
  library: LibraryDto;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onClick?: (id: string) => void;
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

// 横向展示：封面(左) + 主要信息(右)
export const LibraryCardHorizontal: React.FC<LibraryCardHorizontalProps> = ({
  library,
  onEdit,
  onDelete,
  onClick,
}) => {
  const { t, lang } = useI18n();
  const [coverUrl, setCoverUrl] = useState<string | null>(library.coverUrl ?? null);
  useEffect(() => {
    setCoverUrl(library.coverUrl ?? null);
  }, [library.coverUrl]);

  const rawDescription = library.description?.trim();
  const hasDescription = Boolean(rawDescription);
  const descriptionText = hasDescription ? rawDescription : t('libraries.list.description.empty');
  const tagsPlaceholder = t('libraries.tags.placeholder');
  const pinnedLabel = t('libraries.list.status.pinned');
  const archivedLabel = t('libraries.list.status.archived');
  const createdLabel = t('libraries.cardHorizontal.created', { date: formatDate(library.created_at, lang) });
  const lastActivityLabel = library.last_activity_at
    ? t('libraries.cardHorizontal.lastActivity', { date: formatDate(library.last_activity_at, lang) })
    : undefined;
  const viewsLabel = t('libraries.cardHorizontal.views', { count: library.views_count ?? 0 });

  return (
    <Card
      style={{
        display: 'flex',
        flexDirection: 'row',
        gap: 'var(--spacing-lg)',
        alignItems: 'stretch',
        cursor: onClick ? 'pointer' : 'default',
        padding: 'var(--spacing-lg)',
      }}
      aria-label={t('libraries.card.ariaLabel', { name: library.name })}
      onClick={() => onClick?.(library.id)}
    >
      {/* 封面区域 */}
      <div
        style={{
          width: 120,
          flexShrink: 0,
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
          background: 'var(--color-surface-alt)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.75rem',
          color: 'var(--color-text-muted)',
          position: 'relative',
        }}
      >
        {coverUrl ? (
          // 等后端提供真实媒资地址后替换 img src
          <img
            src={coverUrl}
            alt={t('libraries.card.coverAlt', { name: library.name })}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onError={() => setCoverUrl(null)}
          />
        ) : (
          <span style={{ padding: 'var(--spacing-sm)', textAlign: 'center' }}>{t('libraries.cardHorizontal.noCover')}</span>
        )}
      </div>

      {/* 信息区域 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--spacing-lg)' }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: 0 }} title={descriptionText}>
              {library.name}
            </h3>
            <LibraryTagsRow
              tags={library.tags}
              total={library.tag_total_count}
              placeholder={tagsPlaceholder}
            />
            <p
              style={{
                margin: '4px 0 0 0',
                lineHeight: 1.4,
                color: hasDescription ? 'var(--color-text-secondary)' : 'var(--color-text-tertiary)',
              }}
            >
              {descriptionText}
            </p>
            {(library.pinned || library.archived_at) && (
              <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                {library.pinned && (
                  <span
                    style={{ fontSize: '0.65rem', background: 'var(--color-primary-soft)', color: 'var(--color-primary)', padding: '2px 6px', borderRadius: 'var(--radius-sm)', textTransform: 'uppercase', letterSpacing: '.5px' }}
                    data-tooltip={pinnedLabel}
                    aria-label={pinnedLabel}
                  >
                    {pinnedLabel}
                  </span>
                )}
                {library.archived_at && (
                  <span
                    style={{ fontSize: '0.65rem', background: 'var(--color-border)', color: 'var(--color-text-secondary)', padding: '2px 6px', borderRadius: 'var(--radius-sm)', textTransform: 'uppercase', letterSpacing: '.5px' }}
                    data-tooltip={archivedLabel}
                    aria-label={archivedLabel}
                  >
                    {archivedLabel}
                  </span>
                )}
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
            {onEdit && (
              <Button size="sm" variant="secondary" onClick={(e) => { e.stopPropagation(); onEdit(library.id); }}>
                {t('button.edit')}
              </Button>
            )}
            {onDelete && (
              <Button size="sm" variant="danger" onClick={(e) => { e.stopPropagation(); onDelete(library.id); }}>
                {t('button.delete')}
              </Button>
            )}
          </div>
        </div>
        <small style={{ color: 'var(--color-text-muted)', display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
          <span>{createdLabel}</span>
          {lastActivityLabel && <span>{lastActivityLabel}</span>}
          <span>{viewsLabel}</span>
        </small>
      </div>
    </Card>
  );
};

export default LibraryCardHorizontal;
