import React from 'react';
import { createPortal } from 'react-dom';
import {
  Archive,
  Copy,
  ExternalLink,
  FolderInput,
  Image,
  MoreHorizontal,
  Pencil,
  Star,
  Tag,
  Trash2,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { BookDto, BookMaturity, buildBookRibbon } from '@/entities/book';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import { buildMediaFileUrl } from '@/shared/api';
import { showToast } from '@/shared/ui/toast';
import { useUploadBookCover } from '@/features/book/model/hooks';
import { getBookTheme } from '@/shared/theme/theme-pure';
import { ImageLoadHandle, reportImageError, reportImageLoaded, startImageLoad } from '@/shared/telemetry/imageMetrics';
import { UiRequestHandle, emitUiRendered, markUiResponse, startUiRequest } from '@/shared/telemetry/uiRequestMetrics';
import styles from './BookFlatCard.module.css';
import { MATURITY_META, STATUS_COLORS } from './bookVisuals';
import { getCoverIconComponent } from './bookCoverIcons';
import { resolveTagDescription as resolveTagDescriptionFromMap } from '@/features/tag/lib/tagCatalog';

export interface BookFlatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  book?: BookDto;
  maturity?: BookMaturity;
  glyph?: string;
  status?: BookDto['status'];
  statusColor?: string;
  isPinned?: boolean;
  coverUrl?: string;
  accentColor?: string;
  accentStrength?: number;
  tagNames?: string[];
  primaryTagName?: string;
  tagDescriptionsMap?: Record<string, string>;
  showHover?: boolean;
  showShadow?: boolean;
  showStatusBadge?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  onTogglePin?: (nextPinned: boolean) => void;
  onOpen?: () => void;
  onDuplicate?: () => void;
  onArchive?: () => void;
}

type HexColor = `#${string}`;

const clampChannel = (value: number) => Math.max(0, Math.min(255, value));

const normalizeHex = (color: string | undefined): HexColor | null => {
  if (!color || !color.startsWith('#') || (color.length !== 7 && color.length !== 4)) {
    return null;
  }

  return color.length === 4
    ? (`#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}` as HexColor)
    : (color as HexColor);
};

const adjustColor = (color: string | undefined, delta: number): HexColor => {
  const normalized = normalizeHex(color);
  if (!normalized) {
    return '#1f2937';
  }

  const numeric = parseInt(normalized.slice(1), 16);
  const r = clampChannel(((numeric >> 16) & 0xff) + delta);
  const g = clampChannel(((numeric >> 8) & 0xff) + delta);
  const b = clampChannel((numeric & 0xff) + delta);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
};

const PIN_STAR_BG: HexColor = '#fef9c3';
const PIN_STAR_FG: HexColor = '#854d0e';
const PIN_STAR_BORDER: HexColor = '#facc15';

const COVER_SIZE_LIMIT = 10 * 1024 * 1024; // 10MB

export const BookFlatCard = React.forwardRef<HTMLDivElement, BookFlatCardProps>((props, ref) => {
  const {
    book,
    maturity,
    glyph,
    status,
    statusColor,
    isPinned,
    coverUrl,
    accentColor,
    accentStrength: _accentStrength,
    showHover = true,
    showShadow = true,
    tagNames,
    primaryTagName,
    tagDescriptionsMap,
    showStatusBadge = true,
    onEdit,
    onDelete,
    onTogglePin,
    onOpen,
    onDuplicate,
    onArchive,
    className = '',
    ...rest
  } = props;
  const { t } = useI18n();

  const [localCoverUrl, setLocalCoverUrl] = React.useState<string | null>(null);
  const [coverSrc, setCoverSrc] = React.useState<string | undefined>(undefined);
  const coverLoadRef = React.useRef<ImageLoadHandle | null>(null);
  const coverActionRef = React.useRef<UiRequestHandle | null>(null);
  const nextCoverCidRef = React.useRef<string | null>(null);
  const previewUrlRef = React.useRef<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const uploadCoverMutation = useUploadBookCover();
  const uploadBookCoverAsync = uploadCoverMutation.mutateAsync;
  const isUploadingCover = uploadCoverMutation.isPending;

  const resolvedMaturity = (book?.maturity || maturity || 'seed') as BookMaturity;
  const resolvedStatus = book?.status || status;
  const resolvedStatusColor = statusColor || (resolvedStatus ? STATUS_COLORS[resolvedStatus] : undefined);
  const resolvedPinned = book?.is_pinned ?? isPinned;
  const resolvedTags = tagNames ?? book?.tagsSummary ?? [];
  const ribbon = buildBookRibbon(
    primaryTagName ? [primaryTagName, ...resolvedTags.slice(1)] : resolvedTags,
    resolvedMaturity,
  );
  const allowFallbackBadge = !ribbon.fromTag && showStatusBadge;
  const primaryTagLabel = primaryTagName ?? resolvedTags[0];
  const primaryTagDescription = React.useMemo(
    () => resolveTagDescriptionFromMap(primaryTagLabel, tagDescriptionsMap, { libraryId: book?.library_id }),
    [primaryTagLabel, tagDescriptionsMap, book?.library_id],
  );
  const maturityMeta = MATURITY_META[resolvedMaturity];
  const maturityLabelKey = `books.maturity.labels.${resolvedMaturity}` as MessageKey;
  const maturityLabel = t(maturityLabelKey);
  const badgeTooltip = ribbon.fromTag
        ? primaryTagLabel
          ? primaryTagDescription
            ? t('books.tags.withDescription', { label: primaryTagLabel, description: primaryTagDescription })
            : t('books.tags.label', { label: primaryTagLabel })
          : undefined
    : maturityMeta
      ? t('books.maturity.tooltip', { label: maturityLabel })
      : undefined;

  const theme = getBookTheme({
    id: book?.id,
    title: book?.title ?? glyph ?? resolvedMaturity,
    stage: resolvedMaturity,
    legacyFlag: Boolean(book?.legacyFlag),
    coverIconId: book?.coverIconId ?? null,
    coverColor: book?.library_theme_color ?? null,
    coverImageUrl: undefined,
    libraryColorSeed: book?.library_id ?? book?.bookshelf_id ?? undefined,
  });

  const resolvedCoverUrl = localCoverUrl
    ?? coverUrl
    ?? (book?.cover_media_id ? buildMediaFileUrl(book.cover_media_id, book.updated_at) : undefined);
  const coverAlt = book?.title ? t('books.card.coverAlt', { title: book.title }) : t('books.cover.altFallback');

  const resolvedBackground = accentColor ?? theme.accentColor;
  const resolvedGlyph = glyph ?? theme.glyph;
  const coverIconId = theme.iconType === 'lucide' ? theme.iconId : null;
  const CoverIconComponent = coverIconId ? getCoverIconComponent(coverIconId) : null;
  const showIconInFace = Boolean(CoverIconComponent && !resolvedCoverUrl);
  const allowCoverUpload = Boolean(book && !book.legacyFlag && resolvedMaturity === 'stable');
  React.useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
        previewUrlRef.current = null;
      }
    };
  }, []);
  React.useEffect(() => {
    setLocalCoverUrl(null);
  }, [book?.id, book?.cover_media_id, book?.updated_at, coverUrl]);

  React.useEffect(() => {
    if (!resolvedCoverUrl) {
      coverLoadRef.current = null;
      setCoverSrc(undefined);
      return;
    }

    // Local preview (blob/data) should not produce cid-linked metrics.
    if (resolvedCoverUrl.startsWith('blob:') || resolvedCoverUrl.startsWith('data:')) {
      coverLoadRef.current = null;
      setCoverSrc(resolvedCoverUrl);
      return;
    }

    // Lazy-loaded images still emit onLoad/onError, so we can measure end-to-end.
    const nextCid = nextCoverCidRef.current || undefined;
    const handle = startImageLoad('book.cover.load', resolvedCoverUrl, nextCid);
    coverLoadRef.current = handle;
    setCoverSrc(handle.instrumentedUrl);

    // Only reuse the upload correlation id for the very next server image load.
    if (nextCid) {
      nextCoverCidRef.current = null;
    }
  }, [resolvedCoverUrl, book?.id]);
  const handleTogglePin = React.useCallback(() => {
    if (onTogglePin) {
      onTogglePin(!resolvedPinned);
    }
  }, [onTogglePin, resolvedPinned]);
  const triggerCoverUpload = React.useCallback(() => {
    if (!allowCoverUpload || !book?.id) {
      showToast(t('books.toast.coverOnlyStable'));
      return;
    }
    if (isUploadingCover) {
      return;
    }
    fileInputRef.current?.click();
  }, [allowCoverUpload, book?.id, isUploadingCover, t]);
  const handleCoverFileChange = React.useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const input = event.target;
    const file = input.files?.[0];
    input.value = '';

    if (!file || !book?.id) {
      return;
    }

    if (!allowCoverUpload) {
      showToast(t('books.toast.coverOnlyStable'));
      return;
    }

    if (!file.type || !file.type.startsWith('image/')) {
      showToast(t('books.toast.coverImageType'));
      return;
    }

    if (file.size > COVER_SIZE_LIMIT) {
      showToast(t('books.toast.coverImageSize'));
      return;
    }

    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }

    const action = startUiRequest('book.cover.update');
    coverActionRef.current = action;
    nextCoverCidRef.current = action.correlationId;

    const previewUrl = URL.createObjectURL(file);
    previewUrlRef.current = previewUrl;
    setLocalCoverUrl(previewUrl);

    try {
      const updated = await uploadBookCoverAsync({ bookId: book.id, file, correlationId: action.correlationId });
      coverActionRef.current = markUiResponse(action);
      if (updated.cover_media_id) {
        const freshUrl = buildMediaFileUrl(updated.cover_media_id, updated.updated_at);
        setLocalCoverUrl(freshUrl);
      } else {
        setLocalCoverUrl(null);
      }
      showToast(t('books.toast.coverUpdated'));
    } catch (error) {
      console.error('[BookFlatCard] cover upload failed', error);
      setLocalCoverUrl(null);
      showToast(t('books.toast.coverUploadFailed'));
      coverActionRef.current = null;
      nextCoverCidRef.current = null;
    } finally {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
        previewUrlRef.current = null;
      }
    }
  }, [book?.id, allowCoverUpload, t, uploadBookCoverAsync]);

  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement | null>(null);
  const menuAnchorRef = React.useRef<HTMLButtonElement | null>(null);
  const [menuPosition, setMenuPosition] = React.useState<{
    top: number;
    left: number;
    placement: 'above' | 'below';
  } | null>(null);
  const [isPortalReady, setIsPortalReady] = React.useState(false);
  const badgeAnchorRef = React.useRef<HTMLSpanElement | null>(null);
  const [badgeTooltipVisible, setBadgeTooltipVisible] = React.useState(false);
  const [badgeTooltipCoords, setBadgeTooltipCoords] = React.useState<{
    top: number;
    left: number;
    placement: 'above' | 'below';
  } | null>(null);

  React.useEffect(() => {
    setIsPortalReady(typeof document !== 'undefined');
  }, []);

  const updateBadgeTooltipPosition = React.useCallback(() => {
    if (!badgeTooltip || !badgeAnchorRef.current) {
      return;
    }
    const rect = badgeAnchorRef.current.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const spaceAbove = rect.top;
    const spaceBelow = viewportHeight - rect.bottom;
    const placement: 'above' | 'below' = spaceAbove > spaceBelow ? 'above' : 'below';
    const anchorY = placement === 'above' ? rect.top : rect.bottom;
    setBadgeTooltipCoords({
      top: anchorY,
      left: rect.left + rect.width / 2,
      placement,
    });
  }, [badgeTooltip]);

  React.useEffect(() => {
    if (!badgeTooltipVisible) {
      return undefined;
    }
    updateBadgeTooltipPosition();
    const handle = () => updateBadgeTooltipPosition();
    window.addEventListener('scroll', handle, true);
    window.addEventListener('resize', handle);
    return () => {
      window.removeEventListener('scroll', handle, true);
      window.removeEventListener('resize', handle);
    };
  }, [badgeTooltipVisible, updateBadgeTooltipPosition]);

  React.useEffect(() => {
    if (!badgeTooltip) {
      setBadgeTooltipVisible(false);
    }
  }, [badgeTooltip]);

  const handleBadgePointerEnter = React.useCallback(() => {
    if (!badgeTooltip) {
      return;
    }
    setBadgeTooltipVisible(true);
    requestAnimationFrame(() => {
      updateBadgeTooltipPosition();
    });
  }, [badgeTooltip, updateBadgeTooltipPosition]);

  const handleBadgePointerLeave = React.useCallback(() => {
    setBadgeTooltipVisible(false);
  }, []);

  React.useEffect(() => {
    if (!isMenuOpen) {
      setMenuPosition(null);
      return undefined;
    }

    const handleClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [isMenuOpen]);

  const closeMenu = () => {
    setIsMenuOpen(false);
    setMenuPosition(null);
  };

  const updateMenuPosition = React.useCallback(() => {
    if (!isMenuOpen || !menuAnchorRef.current) {
      return;
    }

    const anchorRect = menuAnchorRef.current.getBoundingClientRect();
    const menuElement = menuRef.current;
    const menuHeight = menuElement?.offsetHeight ?? 0;
    const menuWidth = menuElement?.offsetWidth ?? 0;

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    const spaceBelow = viewportHeight - anchorRect.bottom;
    const spaceAbove = anchorRect.top;
    const shouldOpenAbove = spaceBelow < menuHeight + 16 && spaceAbove > spaceBelow;

    const computedTop = shouldOpenAbove
      ? Math.max(12, anchorRect.top - menuHeight - 12)
      : Math.min(viewportHeight - menuHeight - 12, anchorRect.bottom + 12);

    const anchorCenter = anchorRect.left + anchorRect.width / 2;
    const halfWidth = menuWidth / 2;
    const clampedLeft = Math.min(
      Math.max(anchorCenter, halfWidth + 12),
      viewportWidth - halfWidth - 12,
    );

    setMenuPosition({
      top: computedTop,
      left: clampedLeft,
      placement: shouldOpenAbove ? 'above' : 'below',
    });
  }, [isMenuOpen]);

  React.useEffect(() => {
    if (!isMenuOpen) {
      return undefined;
    }

    const handle = requestAnimationFrame(updateMenuPosition);
    window.addEventListener('resize', updateMenuPosition);
    window.addEventListener('scroll', updateMenuPosition, true);
    return () => {
      cancelAnimationFrame(handle);
      window.removeEventListener('resize', updateMenuPosition);
      window.removeEventListener('scroll', updateMenuPosition, true);
    };
  }, [isMenuOpen, updateMenuPosition]);

  const menuSections = React.useMemo(() => {
    type MenuItem = {
      key: string;
      label: string;
      icon: LucideIcon;
      onSelect?: () => void;
      disabled?: boolean;
      tone?: 'danger';
      alwaysVisible?: boolean;
    };

    const sections: MenuItem[][] = [
      [
        {
          key: 'open',
          label: t('books.menu.openExternal'),
          icon: ExternalLink,
          onSelect: onOpen,
        },
        {
          key: 'rename',
          label: t('books.menu.rename'),
          icon: Pencil,
          onSelect: onEdit,
        },
        {
          key: 'tags',
          label: t('books.menu.editTags'),
          icon: Tag,
          onSelect: onEdit,
        },
        {
          key: 'pin',
          label: resolvedPinned ? t('books.menu.unpin') : t('books.menu.pin'),
          icon: Star,
          onSelect: onTogglePin ? () => handleTogglePin() : undefined,
          disabled: !onTogglePin,
        },
        {
          key: 'cover',
          label: t('books.menu.insertCover'),
          icon: Image,
          onSelect: allowCoverUpload ? () => triggerCoverUpload() : undefined,
          disabled: !allowCoverUpload,
        },
      ],
      [
        {
          key: 'move',
          label: t('books.menu.moveSoon'),
          icon: FolderInput,
          disabled: true,
          alwaysVisible: true,
        },
        {
          key: 'duplicate',
          label: t('books.menu.duplicate'),
          icon: Copy,
          onSelect: onDuplicate,
        },
      ],
      [
        {
          key: 'archive',
          label: t('books.menu.archive'),
          icon: Archive,
          onSelect: onArchive,
        },
        {
          key: 'delete',
          label: t('books.menu.delete'),
          icon: Trash2,
          onSelect: onDelete,
          tone: 'danger',
        },
      ],
    ];

    return sections
      .map((section) => section.filter((item) => item.alwaysVisible || Boolean(item.onSelect)))
      .filter((section) => section.length > 0);
  }, [allowCoverUpload, handleTogglePin, onArchive, onDelete, onDuplicate, onEdit, onOpen, onTogglePin, resolvedPinned, t, triggerCoverUpload]);

  const hasMenuItems = menuSections.length > 0;
  const hasHoverActions = Boolean(onEdit || onTogglePin || hasMenuItems);

  const spineColor = adjustColor(resolvedBackground, -35);
  const pageEdgeColor = adjustColor(resolvedBackground, 35);
  const pinRibbonStart = adjustColor(resolvedBackground, 45);
  const pinRibbonEnd = adjustColor(resolvedBackground, -10);
  const pinBadgeBg = PIN_STAR_BG;
  const pinBadgeFg = PIN_STAR_FG;
  const pinCtaBorder = PIN_STAR_BORDER;

  const cssVars: React.CSSProperties = {
    '--book-flat-spine': spineColor,
    '--book-flat-page': pageEdgeColor,
    '--book-flat-cover-bg': resolvedBackground,
    '--book-flat-pin-start': pinRibbonStart,
    '--book-flat-pin-end': pinRibbonEnd,
    '--book-pin-badge-bg': pinBadgeBg,
    '--book-pin-badge-fg': pinBadgeFg,
    '--book-pin-cta-border': pinCtaBorder,
  } as React.CSSProperties;

  return (
    <div
      ref={ref}
      className={`${styles.root} ${className}`.trim()}
      data-maturity={resolvedMaturity}
      data-menu-open={isMenuOpen ? 'true' : undefined}
      style={cssVars}
      onMouseLeave={() => {
        if (!isMenuOpen) {
          setIsMenuOpen(false);
        }
      }}
      {...rest}
    >
      <div className={styles.bookBody}>
        {resolvedPinned && <span className={styles.pinRibbon} aria-hidden />}
        <span className={styles.spine} aria-hidden />
        <span className={styles.pageEdge} aria-hidden />
        <div
          className={styles.face}
          style={!resolvedCoverUrl ? { backgroundColor: resolvedBackground } : undefined}
          data-has-icon={showIconInFace ? 'true' : undefined}
        >
          {resolvedCoverUrl ? (
            <img
              src={coverSrc || resolvedCoverUrl}
              alt={coverAlt}
              loading="lazy"
              onLoad={(e) => {
                const handle = coverLoadRef.current;
                if (!handle) return;
                reportImageLoaded(handle, e.currentTarget, {
                  entity_type: 'book',
                  entity_id: book?.id ?? null,
                });

                const action = coverActionRef.current;
                if (action && action.correlationId === handle.correlationId) {
                  void emitUiRendered(action, {
                    entity_type: 'book',
                    entity_id: book?.id ?? null,
                    image_url: handle.instrumentedUrl,
                  });
                  coverActionRef.current = null;
                }
              }}
              onError={() => {
                const handle = coverLoadRef.current;
                if (handle) {
                  reportImageError(handle, {
                    entity_type: 'book',
                    entity_id: book?.id ?? null,
                  });
                }
                coverActionRef.current = null;
              }}
            />
          ) : showIconInFace && CoverIconComponent ? (
            <span className={styles.faceGlyphIcon} aria-hidden>
              <CoverIconComponent size={32} strokeWidth={1.8} />
            </span>
          ) : (
            <span className={styles.glyph} aria-hidden>
              {resolvedGlyph}
            </span>
          )}
        </div>
        {ribbon.label && (ribbon.fromTag || allowFallbackBadge) && (
          <span
            ref={badgeAnchorRef}
            className={styles.badge}
            data-variant={ribbon.fromTag ? 'tag' : 'status'}
            data-tooltip={badgeTooltip ?? undefined}
            aria-label={badgeTooltip ?? undefined}
            onMouseEnter={handleBadgePointerEnter}
            onMouseLeave={handleBadgePointerLeave}
            onFocus={handleBadgePointerEnter}
            onBlur={handleBadgePointerLeave}
            style={ribbon.fromTag ? undefined : resolvedStatusColor ? { backgroundColor: resolvedStatusColor } : undefined}
          >
            {ribbon.label}
          </span>
        )}
        {resolvedPinned && (
          <span className={styles.pinBadge} title={t('books.meta.pinLabel')} aria-label={t('books.meta.pinLabel')}>
            <Star size={14} strokeWidth={2} aria-hidden />
          </span>
        )}
        {showHover && hasHoverActions && (
          <div className={styles.actionsDock} data-menu-open={isMenuOpen ? 'true' : undefined}>
            {onEdit && (
              <button
                type="button"
                className={styles.hoverIconButton}
                aria-label={t('books.card.actions.edit')}
                onClick={(event) => {
                  event.stopPropagation();
                  onEdit();
                }}
              >
                <Pencil size={12} strokeWidth={1.8} />
              </button>
            )}
            {hasMenuItems && (
              <button
                type="button"
                className={styles.hoverIconButton}
                aria-label={t('books.menu.moreActions')}
                data-active={isMenuOpen ? 'true' : undefined}
                ref={menuAnchorRef}
                onClick={(event) => {
                  event.stopPropagation();
                  if (isMenuOpen) {
                    closeMenu();
                    return;
                  }
                  if (menuAnchorRef.current) {
                    const rect = menuAnchorRef.current.getBoundingClientRect();
                    setMenuPosition({
                      top: rect.bottom + 12,
                      left: rect.left + rect.width / 2,
                      placement: 'below',
                    });
                  }
                  setIsMenuOpen(true);
                }}
              >
                <MoreHorizontal size={12} strokeWidth={1.8} />
              </button>
            )}
            {onTogglePin && (
              <button
                type="button"
                className={styles.hoverIconButton}
                aria-label={resolvedPinned ? t('books.card.actions.unpin') : t('books.card.actions.pin')}
                onClick={(event) => {
                  event.stopPropagation();
                  handleTogglePin();
                }}
                data-role="pin"
                data-active={resolvedPinned ? 'true' : undefined}
              >
                <Star size={12} strokeWidth={1.8} />
              </button>
            )}
            {isMenuOpen && hasMenuItems && isPortalReady && menuPosition && menuAnchorRef.current &&
              createPortal(
                <div
                  className={styles.quickMenu}
                  ref={menuRef}
                  data-placement={menuPosition.placement}
                  style={{ top: `${menuPosition.top}px`, left: `${menuPosition.left}px` }}
                >
                  {menuSections.map((section, sectionIndex) => (
                    <React.Fragment key={`section-${sectionIndex}`}>
                      <div className={styles.quickMenuSection}>
                        {section.map((item) => {
                          const Icon = item.icon;
                          return (
                            <button
                              key={item.key}
                              type="button"
                              className={`${styles.quickMenuItem} ${item.tone === 'danger' ? styles.quickMenuItemDanger : ''}`.trim()}
                              onClick={(event) => {
                                event.stopPropagation();
                                if (item.disabled || !item.onSelect) {
                                  return;
                                }
                                item.onSelect();
                                closeMenu();
                              }}
                              disabled={item.disabled || !item.onSelect}
                            >
                              <Icon size={16} strokeWidth={1.8} aria-hidden />
                              <span>{item.label}</span>
                            </button>
                          );
                        })}
                      </div>
                      {sectionIndex < menuSections.length - 1 && <div className={styles.quickMenuDivider} />}
                    </React.Fragment>
                  ))}
                </div>,
                menuAnchorRef.current.ownerDocument?.body ?? document.body,
              )}
          </div>
        )}
      </div>
      {showShadow && <div className={styles.shadow} aria-hidden />}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleCoverFileChange}
        onClick={(event) => event.stopPropagation()}
        style={{ display: 'none' }}
      />
      {badgeTooltipVisible && badgeTooltip && badgeTooltipCoords && isPortalReady &&
        createPortal(
          <div
            className={styles.badgeTooltipBubble}
            data-placement={badgeTooltipCoords.placement}
            style={{ top: badgeTooltipCoords.top, left: badgeTooltipCoords.left }}
            role="tooltip"
          >
            {badgeTooltip}
          </div>,
          badgeAnchorRef.current?.ownerDocument?.body ?? document.body,
        )}
    </div>
  );
});

BookFlatCard.displayName = 'BookFlatCard';
