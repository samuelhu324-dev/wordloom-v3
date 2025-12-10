import { BaseDto } from '@/shared/api';

const DEFAULT_TAG_COLOR = '#6366F1';

export interface BookshelfTagSummary {
  id: string;
  name: string;
  color: string;
  description?: string;
}

/** Bookshelf DTO */
export interface BookshelfDto extends BaseDto {
  library_id: string;
  name: string;
  description?: string;
  type: 'NORMAL' | 'BASEMENT';
  /** UI 仅用：封面颜色（根据名称哈希确定，确保 SSR/CSR 一致） */
  coverColor?: string;
  /** 后端存储的书橱主题色（优先使用） */
  color?: string;
  status?: string;
  is_pinned?: boolean;
  pinned_at?: string;
  is_favorite?: boolean;
  book_count?: number;
  position?: number | null;
  tagIds?: string[];
  tagsSummary?: string[];
}

/** Create Bookshelf Request */
export interface CreateBookshelfRequest {
  name: string;
  description?: string;
  /** Required by backend flat endpoint when creating */
  library_id?: string;
  /** Optional initial tag associations */
  tag_ids?: string[];
}

/** Update Bookshelf Request */
export interface UpdateBookshelfRequest {
  name?: string;
  description?: string;
  status?: 'active' | 'archived' | string;
  is_pinned?: boolean;
  tagIds?: string[];
}

/**
 * Mapping helpers between Backend transport shape and UI DTO
 * Backend Router fields (bookshelf_router.py):
 *  - id, library_id, name, description, is_basement, status, is_pinned, is_favorite, created_at
 * UI expects: BookshelfDto with `type` (NORMAL|BASEMENT) and BaseDto fields
 */
export type BackendBookshelf = {
  id: string;
  library_id: string;
  name: string;
  description?: string | null;
  color?: string | null;
  position?: number | null;
  is_basement?: boolean;
  is_pinned?: boolean;
  is_favorite?: boolean;
  status?: string;
  pinned_at?: string | null;
  book_count?: number | null;
  created_at?: string;
  updated_at?: string | null;
  tags_summary?: string[] | null;
  tag_ids?: string[] | null;
};

const palette = [
  '#4F46E5', // indigo
  '#2563EB', // blue
  '#0D9488', // teal
  '#16A34A', // green
  '#D97706', // amber
  '#DC2626', // red
  '#9333EA', // purple
  '#0891B2', // cyan
];

const deriveCoverColor = (seedSource: string): string => {
  const seed = seedSource.toLowerCase();
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return palette[hash % palette.length];
};

export const toBookshelfDto = (b: BackendBookshelf): BookshelfDto => {
  const coverColor = deriveCoverColor(b.name || b.id || '');
  return {
    id: b.id,
    library_id: b.library_id,
    name: b.name,
    description: b.description || undefined,
    type: b.is_basement ? 'BASEMENT' : 'NORMAL',
    coverColor,
    color: b.color || undefined,
    status: b.status,
    is_pinned: Boolean(b.is_pinned),
    pinned_at: b.pinned_at || undefined,
    is_favorite: Boolean(b.is_favorite),
    book_count: typeof b.book_count === 'number' ? b.book_count : undefined,
    position: typeof b.position === 'number' ? b.position : null,
    created_at: b.created_at || new Date().toISOString(),
    updated_at: b.updated_at || b.created_at || new Date().toISOString(),
    tagIds: Array.isArray(b.tag_ids) ? b.tag_ids : undefined,
    tagsSummary: Array.isArray(b.tags_summary) ? b.tags_summary : undefined,
  } as BookshelfDto;
};

export type BookshelfDashboardSort =
  | 'recent_activity'
  | 'name_asc'
  | 'created_desc'
  | 'book_count_desc';

export type BookshelfDashboardFilter = 'all' | 'active' | 'stale' | 'archived' | 'pinned';

export type BookshelfHealth = 'active' | 'slowing' | 'cooling' | 'archived';

export interface BookshelfDashboardCounts {
  total: number;
  seed: number;
  growing: number;
  stable: number;
  legacy: number;
}

export interface BookshelfDashboardHealthBuckets {
  active: number;
  slowing: number;
  cooling: number;
  archived: number;
}

export interface BookshelfDashboardSnapshot {
  total: number;
  pinned: number;
  health: BookshelfDashboardHealthBuckets;
}

export interface BookshelfDashboardItemDto extends BaseDto {
  library_id: string;
  name: string;
  description?: string;
  status: string;
  is_pinned: boolean;
  is_archived: boolean;
  is_basement: boolean;
  tagIds?: string[];
  tagsSummary?: string[];
  tagsMeta?: BookshelfTagSummary[];
  book_counts: BookshelfDashboardCounts;
  edits_last_7d: number;
  views_last_7d: number;
  last_activity_at?: string;
  health: BookshelfHealth;
  theme_color?: string;
  cover_media_id?: string;
  wall_color: string;
  base_color: string;
}

export interface BackendBookshelfDashboardCounts {
  total: number;
  seed: number;
  growing: number;
  stable: number;
  legacy: number;
}

export interface BackendBookshelfDashboardItem {
  id: string;
  library_id: string;
  name: string;
  description?: string | null;
  status: string;
  is_pinned: boolean;
  is_archived: boolean;
  is_basement: boolean;
  created_at: string;
  updated_at: string;
  last_activity_at?: string | null;
  health: BookshelfHealth;
  theme_color?: string | null;
  cover_media_id?: string | null;
  book_counts: BackendBookshelfDashboardCounts;
  edits_last_7d: number;
  views_last_7d: number;
  tags_summary?: string[] | null;
  tag_ids?: string[] | null;
  tags?: BackendBookshelfTagSummary[] | null;
}

export interface BackendBookshelfDashboardSnapshot {
  total?: number;
  pinned?: number;
  health?: Partial<BookshelfDashboardHealthBuckets> | null;
}

export interface BackendBookshelfTagSummary {
  id: string;
  name: string;
  color?: string | null;
  description?: string | null;
}

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const lightenColor = (hex: string, lighten = 0.06, saturateDelta = -0.08): string => {
  const base = hex.startsWith('#') ? hex.slice(1) : hex;
  if (base.length !== 6) {
    return `#${base}`;
  }
  const r = parseInt(base.slice(0, 2), 16);
  const g = parseInt(base.slice(2, 4), 16);
  const b = parseInt(base.slice(4, 6), 16);

  const rNorm = r / 255;
  const gNorm = g / 255;
  const bNorm = b / 255;

  const max = Math.max(rNorm, gNorm, bNorm);
  const min = Math.min(rNorm, gNorm, bNorm);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case rNorm:
        h = (gNorm - bNorm) / d + (gNorm < bNorm ? 6 : 0);
        break;
      case gNorm:
        h = (bNorm - rNorm) / d + 2;
        break;
      default:
        h = (rNorm - gNorm) / d + 4;
        break;
    }
    h /= 6;
  }

  const newS = clamp(s + saturateDelta, 0, 1);
  const newL = clamp(l + lighten, 0, 1);

  const hueToRgb = (p: number, q: number, t: number) => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };

  let rOut = newL;
  let gOut = newL;
  let bOut = newL;

  if (newS !== 0) {
    const q = newL < 0.5 ? newL * (1 + newS) : newL + newS - newL * newS;
    const p = 2 * newL - q;
    rOut = hueToRgb(p, q, h + 1 / 3);
    gOut = hueToRgb(p, q, h);
    bOut = hueToRgb(p, q, h - 1 / 3);
  }

  const toHex = (value: number) => {
    return clamp(Math.round(value * 255), 0, 255).toString(16).padStart(2, '0');
  };

  return `#${toHex(rOut)}${toHex(gOut)}${toHex(bOut)}`;
};

export const toBookshelfDashboardItem = (
  item: BackendBookshelfDashboardItem,
  fallbackLibraryColor?: string,
): BookshelfDashboardItemDto => {
  const baseColor = item.theme_color || fallbackLibraryColor || deriveCoverColor(`${item.name}_${item.id}`);
  const wallColor = lightenColor(baseColor);
  const tagsMeta = Array.isArray(item.tags)
    ? item.tags.map((tag) => ({
        id: tag.id,
        name: tag.name,
        color: tag.color || DEFAULT_TAG_COLOR,
        description: tag.description || undefined,
      }))
    : undefined;
  return {
    id: item.id,
    created_at: item.created_at,
    updated_at: item.updated_at,
    library_id: item.library_id,
    name: item.name,
    description: item.description || undefined,
    status: item.status,
    is_pinned: Boolean(item.is_pinned),
    is_archived: Boolean(item.is_archived),
    is_basement: Boolean(item.is_basement),
    tagIds: Array.isArray(item.tag_ids) ? item.tag_ids : undefined,
    tagsSummary: Array.isArray(item.tags_summary) ? item.tags_summary : undefined,
    tagsMeta,
    book_counts: {
      total: item.book_counts.total,
      seed: item.book_counts.seed,
      growing: item.book_counts.growing,
      stable: item.book_counts.stable,
      legacy: item.book_counts.legacy,
    },
    edits_last_7d: item.edits_last_7d,
    views_last_7d: item.views_last_7d,
    last_activity_at: item.last_activity_at || undefined,
    health: item.health,
    theme_color: item.theme_color || undefined,
    cover_media_id: item.cover_media_id || undefined,
    wall_color: wallColor,
    base_color: baseColor,
  };
};

