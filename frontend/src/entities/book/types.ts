import { BaseDto } from '@/shared/api';
import type { BookCoverIconId } from './lib/book-cover-icons';

export type BookMaturity = 'seed' | 'growing' | 'stable' | 'legacy';

/** Book DTO */
export interface BookDto extends BaseDto {
  library_id?: string;
  bookshelf_id: string;
  title: string;
  summary?: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED' | 'DELETED';
  block_count: number;
  is_pinned: boolean;
  due_at?: string | null;
  cover_media_id?: string;
  maturity: BookMaturity;
  maturityScore: number;
  legacyFlag: boolean;
  manualMaturityOverride: boolean;
  manualMaturityReason?: string;
  visitCount90d: number;
  lastVisitedAt?: string | null;
  tagsSummary?: string[];
  coverIconId?: BookCoverIconId | null;
  library_theme_color?: string | null;
}

/** Backend Book Response from API */
export interface BackendBook {
  id: string;
  bookshelf_id: string;
  library_id: string;
  title: string;
  summary?: string | null;
  status: string;
  maturity?: string | null;
  maturity_score?: number | null;
  legacy_flag?: boolean | null;
  manual_maturity_override?: boolean | null;
  manual_maturity_reason?: string | null;
  block_count: number;
  is_pinned: boolean;
  due_at?: string | null;
  created_at: string;
  updated_at: string;
  soft_deleted_at?: string | null;
  tags_summary?: string[] | null;
  cover_icon?: string | null;
  cover_media_id?: string | null;
  visit_count_90d?: number | null;
  last_visited_at?: string | null;
  library_theme_color?: string | null;
}

/** Create Book Request */
export interface CreateBookRequest {
  bookshelf_id: string;
  library_id: string; // 后端需要用于权限与聚合根范围验证
  title: string;
  summary?: string;
  cover_icon?: BookCoverIconId | null;
}

/** Update Book Request */
export interface UpdateBookRequest {
  title?: string;
  summary?: string;
  is_pinned?: boolean;
  status?: string;
  maturity?: BookMaturity;
  tag_ids?: string[];
  cover_icon?: BookCoverIconId | null;
}

/** Convert backend Book to DTO */
const clampScore = (value?: number | null) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round(value)));
};

export const toBookDto = (b: BackendBook): BookDto => {
  const maturityRaw = typeof b.maturity === 'string' && b.maturity
    ? b.maturity.toLowerCase()
    : 'seed';
  const coverIcon = typeof b.cover_icon === 'string' && b.cover_icon.trim().length > 0
    ? (b.cover_icon.trim().toLowerCase() as BookCoverIconId)
    : undefined;
  const manualReason = typeof b.manual_maturity_reason === 'string' && b.manual_maturity_reason.trim().length > 0
    ? b.manual_maturity_reason.trim()
    : undefined;

  return {
    id: b.id,
    library_id: b.library_id,
    bookshelf_id: b.bookshelf_id,
    title: b.title,
    summary: b.summary || undefined,
    status: (b.status.toUpperCase() as any) || 'DRAFT',
    block_count: b.block_count || 0,
    is_pinned: b.is_pinned || false,
    due_at: b.due_at || null,
    created_at: b.created_at || new Date().toISOString(),
    updated_at: b.updated_at || b.created_at || new Date().toISOString(),
    maturity: maturityRaw as BookMaturity,
    maturityScore: clampScore(b.maturity_score),
    legacyFlag: Boolean(b.legacy_flag),
    manualMaturityOverride: Boolean(b.manual_maturity_override),
    manualMaturityReason: manualReason,
    visitCount90d: typeof b.visit_count_90d === 'number' ? b.visit_count_90d : 0,
    lastVisitedAt: b.last_visited_at || undefined,
    tagsSummary: Array.isArray(b.tags_summary) ? b.tags_summary : undefined,
    coverIconId: coverIcon,
    cover_media_id: b.cover_media_id || undefined,
    library_theme_color: b.library_theme_color || undefined,
  };
};
