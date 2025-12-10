"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import ImageUrlDialog from '@/features/media/ui/ImageUrlDialog';
import { Card, Button } from '@/shared/ui';
import styles from './BookshelfCard.module.css';

interface BookshelfCardProps {
  bookshelf: BookshelfDto;
  onSelect?: (id: string) => void;
  onDelete?: (id: string) => void;
  viewMode?: 'grid' | 'list';
}

const COVER_PLACEHOLDER = 'https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1200&auto=format&fit=crop';

export const BookshelfCard = React.forwardRef<HTMLDivElement, BookshelfCardProps>(
  ({ bookshelf, onSelect, onDelete, viewMode = 'grid' }, ref) => {
    const coverTone = bookshelf.color || bookshelf.coverColor || 'var(--color-primary)';
    const isBasement = bookshelf.type === 'BASEMENT';
    const isPinned = Boolean(bookshelf.is_pinned);
    const isFavorite = Boolean(bookshelf.is_favorite);
    const statusLabel = bookshelf.status ? bookshelf.status.toUpperCase() : undefined;
    const bookCountLabel = typeof bookshelf.book_count === 'number' ? `${bookshelf.book_count} 本书` : undefined;
    const storageKey = useMemo(() => `bookshelf:cover:${bookshelf.id}`, [bookshelf.id]);
    const [coverUrl, setCoverUrl] = useState<string | null>(null);
    const [isCoverDialogOpen, setCoverDialogOpen] = useState(false);

    useEffect(() => {
      if (typeof window === 'undefined') return;
      setCoverUrl(null);
      try {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          setCoverUrl(stored);
        }
      } catch (error) {
        console.warn('恢复书橱封面失败', error);
      }
    }, [storageKey]);

    const handleCoverConfirm = (url: string) => {
      setCoverUrl(url);
      try {
        localStorage.setItem(storageKey, url);
      } catch (error) {
        console.warn('持久化书橱封面失败', error);
      }
      setCoverDialogOpen(false);
    };

    const coverSrc = coverUrl || COVER_PLACEHOLDER;

    const statusChip = isPinned
      ? { label: 'PINNED', className: styles.statusPinned }
      : isFavorite
        ? { label: 'FAVORITE', className: styles.statusFavorite }
        : null;

    const wrapperClass = [
      styles.card,
      viewMode === 'list' ? styles.list : styles.grid,
      onSelect ? styles.clickable : '',
    ].filter(Boolean).join(' ');
    const handleKey = (e: React.KeyboardEvent) => {
      if (!onSelect) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onSelect(bookshelf.id);
      }
    };
    return (
      <Card
        ref={ref}
        className={wrapperClass}
        {...(onSelect
          ? {
              role: 'button',
              tabIndex: 0,
              onClick: () => onSelect(bookshelf.id),
              onKeyDown: handleKey,
            }
          : {})}
      >
        <div className={styles.media} style={{ background: coverTone }}>
          <img src={coverSrc} alt="bookshelf cover" className={styles.mediaImage} loading="lazy" />
          <div className={styles.mediaOverlay} />
          <button
            type="button"
            aria-label="设置插图"
            className={styles.coverButton}
            onClick={(event) => {
              event.stopPropagation();
              setCoverDialogOpen(true);
            }}
          >
            🖼️
          </button>
          <div className={styles.mediaContent}>
            <div className={styles.mediaTopRow}>
              <span className={styles.mediaInitial}>{bookshelf.name.slice(0, 1).toUpperCase()}</span>
              {statusChip && (
                <span className={[styles.statusBadge, statusChip.className].filter(Boolean).join(' ')}>
                  {statusChip.label}
                </span>
              )}
            </div>
            <div className={styles.mediaTitleBlock}>
              <h3 className={styles.mediaTitle}>{bookshelf.name}</h3>
            </div>
          </div>
        </div>

        <div className={styles.meta}>
          <div className={styles.headerRow}>
            <div className={styles.badgesRow}>
              <span className={styles.typeBadge}>{isBasement ? 'Basement' : 'Active Shelf'}</span>
              {statusLabel && statusLabel !== 'ACTIVE' && (
                <span className={styles.statusTag}>{statusLabel}</span>
              )}
            </div>
            {onDelete && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(bookshelf.id);
                }}
              >
                ×
              </Button>
            )}
          </div>

          {bookshelf.description && (
            <p className={styles.description}>{bookshelf.description}</p>
          )}

          <div className={styles.footer}>
            <div className={styles.footerMeta}>
              {bookCountLabel && <span>{bookCountLabel}</span>}
              {isPinned && bookshelf.pinned_at && (
                <span>{new Date(bookshelf.pinned_at).toLocaleDateString()}</span>
              )}
            </div>
            {onSelect && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(bookshelf.id);
                }}
              >
                查看书籍
              </Button>
            )}
          </div>
        </div>
        {isCoverDialogOpen && (
          <ImageUrlDialog
            open={isCoverDialogOpen}
            initialUrl={coverUrl ?? undefined}
            onClose={() => setCoverDialogOpen(false)}
            onConfirm={handleCoverConfirm}
          />
        )}
      </Card>
    );
  }
);

BookshelfCard.displayName = 'BookshelfCard';
