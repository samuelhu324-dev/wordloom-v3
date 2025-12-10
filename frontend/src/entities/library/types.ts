import { BaseDto } from '@/shared/api';

export interface LibraryTagSummaryDto {
  id: string;
  name: string;
  color: string;
  description?: string | null;
}

/** Library DTO - 用户的数据容器 */
export interface LibraryDto extends BaseDto {
  user_id: string;
  name: string;
  description?: string;
  basement_bookshelf_id?: string;
  cover_media_id?: string;
  theme_color?: string | null;
  coverUrl?: string; // Derived client-side from media association (if loaded)
  pinned: boolean;
  pinned_order?: number | null;
  archived_at?: string | null;
  last_activity_at: string;
  views_count: number;
  last_viewed_at?: string | null;
  tags?: LibraryTagSummaryDto[];
  tag_total_count?: number;
}

/** Create Library Request */
export interface CreateLibraryRequest {
  name: string;
  description?: string;
  cover_media_id?: string;
  theme_color?: string | null;
}

/** Update Library Request */
export interface UpdateLibraryRequest {
  name?: string;
  description?: string;
  cover_media_id?: string;
  pinned?: boolean;
  pinned_order?: number | null;
  archived?: boolean;
  theme_color?: string | null;
}

export type { LibraryTagSummaryDto as LibraryTagSummary };
