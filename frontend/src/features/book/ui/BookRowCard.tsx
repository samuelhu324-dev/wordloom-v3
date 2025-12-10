import React from 'react';
import { Pin, Pencil, Trash2, Star } from 'lucide-react';
import { BookDto } from '@/entities/book';
import { useI18n } from '@/i18n/useI18n';
import styles from './BookRowCard.module.css';
import { formatRelativeTime } from './bookVisuals';
import { buildMediaFileUrl } from '@/shared/api';
import { getBookTheme } from '@/shared/theme/theme-pure';
import { getCoverIconComponent } from './bookCoverIcons';
import { resolveTagDescription as resolveTagDescriptionFromMap } from '@/features/tag/lib/tagCatalog';

const PIN_STAR_BG = '#fef9c3';
const PIN_STAR_FG = '#854d0e';
const PIN_STAR_BORDER = '#facc15';

type BaseDivProps = Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'>;

interface BookRowCardProps extends BaseDivProps {
  book: BookDto;
  tags?: string[];
  onSelect?: (bookId: string) => void;
  onEdit?: (bookId: string) => void;
  onDelete?: (bookId: string) => void;
  onTogglePin?: (bookId: string, nextPinned: boolean) => void;
  tagDescriptionsMap?: Record<string, string>;
}

export const BookRowCard: React.FC<BookRowCardProps> = ({
  book,
  tags,
  onSelect,
  onEdit,
  onDelete,
  onTogglePin,
  tagDescriptionsMap,
  className = '',
  ...rest
}) => {
  const { t, lang } = useI18n();
  const blockCountValue = book.block_count ?? 0;
  const blockCountLabel = t('books.meta.blocks', { count: blockCountValue });
  const updatedLabel = formatRelativeTime(book.updated_at, lang);
  const resolvedTags = (tags ?? book.tagsSummary) ?? [];
  const MAX_TAGS = 3;
  const displayTags = resolvedTags.slice(0, MAX_TAGS);
  const overflowCount = resolvedTags.length - displayTags.length;
  const clickable = typeof onSelect === 'function';
  const maturity = book.legacyFlag ? 'legacy' : book.maturity;
  const theme = getBookTheme({
    id: book.id,
    title: book.title,
    stage: maturity,
    legacyFlag: Boolean(book.legacyFlag),
    coverIconId: book.coverIconId ?? null,
    coverColor: book.library_theme_color ?? null,
    libraryColorSeed: book.library_id ?? book.bookshelf_id ?? null,
  });
  const coverUrl = book.cover_media_id ? buildMediaFileUrl(book.cover_media_id, book.updated_at) : undefined;
  const glyph = theme.glyph;
  const coverIconId = theme.iconType === 'lucide' ? theme.iconId : null;
  const CoverIconComponent = getCoverIconComponent(coverIconId);
  const coverAlt = book.title ? t('books.card.coverAlt', { title: book.title }) : t('books.cover.altFallback');

  const adjustColor = (hex: string, delta: number) => {
    const normalized = hex.startsWith('#') ? hex.slice(1) : hex;
    if (normalized.length !== 6) {
      return hex;
    }
    const num = parseInt(normalized, 16);
    const clampChannel = (value: number) => Math.max(0, Math.min(255, value));
    const r = clampChannel(((num >> 16) & 0xff) + delta);
    const g = clampChannel(((num >> 8) & 0xff) + delta);
    const b = clampChannel((num & 0xff) + delta);
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  };

  const spineColor = adjustColor(theme.accentColor, -35);

  const handleClick = () => {
    if (onSelect) {
      onSelect(book.id);
    }
  };

  const togglePin = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onTogglePin?.(book.id, !book.is_pinned);
  };

  const handleEdit = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onEdit?.(book.id);
  };

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onDelete?.(book.id);
  };

  const showActions = Boolean(onEdit || onDelete || onTogglePin);

  const showIconInFace = Boolean(CoverIconComponent && !coverUrl);

  const { style, ...restProps } = rest;
  const pinStyleVars = book.is_pinned
    ? ({
        '--book-row-pin-bg': PIN_STAR_BG,
        '--book-row-pin-fg': PIN_STAR_FG,
        '--book-row-pin-border': PIN_STAR_BORDER,
      } as React.CSSProperties)
    : undefined;
  const mergedStyle = pinStyleVars || style
    ? ({
        ...(pinStyleVars ?? {}),
        ...(style ?? {}),
      } as React.CSSProperties)
    : undefined;

  const formatTagTooltip = React.useCallback((tagLabel: string) => {
    const trimmed = tagLabel?.trim();
    if (!trimmed) {
      return '';
    }
    const description = resolveTagDescriptionFromMap(trimmed, tagDescriptionsMap, { libraryId: book.library_id });
    return description
      ? t('books.tags.withDescription', { label: trimmed, description })
      : t('books.tags.label', { label: trimmed });
  }, [book.library_id, tagDescriptionsMap, t]);

  return (
    <div
      className={`${styles.card} ${className}`.trim()}
      data-clickable={clickable ? 'true' : 'false'}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      onClick={clickable ? handleClick : undefined}
      onKeyDown={clickable ? (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          handleClick();
        }
      } : undefined}
      style={mergedStyle}
      {...restProps}
    >
      <div className={styles.left}>
        <div className={styles.flatCover}>
          <span
            className={styles.flatSpine}
            style={{ backgroundColor: spineColor }}
            aria-hidden
          />
          <div
            className={styles.flatFace}
            style={!coverUrl ? { backgroundColor: theme.accentColor } : undefined}
            data-has-icon={showIconInFace ? 'true' : undefined}
          >
            {coverUrl ? (
              <img src={coverUrl} alt={coverAlt} loading="lazy" />
            ) : showIconInFace && CoverIconComponent ? (
              <span className={styles.flatGlyphIcon} aria-hidden>
                <CoverIconComponent size={28} strokeWidth={1.8} />
              </span>
            ) : (
              <span className={styles.flatGlyph} aria-hidden>
                {glyph}
              </span>
            )}
          </div>
          {book.is_pinned && (
            <span className={styles.pinBadge} title={t('books.meta.pinLabel')} aria-label={t('books.meta.pinLabel')}>
              <Star size={12} strokeWidth={2} aria-hidden />
            </span>
          )}
        </div>
      </div>
      <div className={styles.right}>
        <div className={styles.titleRow}>
          <span className={styles.title} title={book.title}>
            {book.title}
          </span>
          {showActions && (
            <div className={styles.actions}>
              {onEdit && (
                <button
                  type="button"
                  className={styles.actionButton}
                  aria-label={t('books.card.actions.edit')}
                  onClick={handleEdit}
                >
                  <Pencil size={14} strokeWidth={1.8} />
                </button>
              )}
              {onDelete && (
                <button
                  type="button"
                  className={styles.actionButton}
                  aria-label={t('books.card.actions.delete')}
                  onClick={handleDelete}
                >
                  <Trash2 size={14} strokeWidth={1.8} />
                </button>
              )}
              {onTogglePin && (
                <button
                  type="button"
                  className={`${styles.actionButton} ${styles.pinButton}`}
                  aria-label={book.is_pinned ? t('books.card.actions.unpin') : t('books.card.actions.pin')}
                  onClick={togglePin}
                  disabled={!onTogglePin}
                  data-active={book.is_pinned ? 'true' : undefined}
                >
                  <Pin size={14} strokeWidth={1.8} />
                </button>
              )}
            </div>
          )}
        </div>
        {book.summary && (
          <div className={styles.description} title={book.summary}>
            {book.summary}
          </div>
        )}
        <div
          className={styles.tagRow}
          data-empty={displayTags.length === 0 ? 'true' : undefined}
        >
          {displayTags.map((tag) => {
            const tooltip = formatTagTooltip(tag);
            return (
              <span
                key={tag}
                className={styles.tag}
                data-tooltip={tooltip}
                aria-label={tooltip || tag}
              >
                {tag}
              </span>
            );
          })}
          {overflowCount > 0 && (
            <span
              className={`${styles.tag} ${styles.tagOverflow}`}
              data-tooltip={t('books.tags.more', { count: overflowCount })}
              aria-label={t('books.tags.more', { count: overflowCount })}
            >
              +{overflowCount}
            </span>
          )}
          <div className={styles.metaRow} aria-label={t('books.meta.blockAndTimeAria')}>
            <span className={styles.metaText}>{blockCountLabel}</span>
            <span className={styles.dot} />
            <span className={styles.metaText}>{updatedLabel}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
