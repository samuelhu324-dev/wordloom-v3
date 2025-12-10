import type { BookDto } from '@/entities/book';
import type { TagSelection } from './types';

const TAG_COLOR_PALETTE = ['#6366F1', '#0EA5E9', '#10B981', '#F97316', '#F59E0B', '#EF4444', '#8B5CF6'];

export const extractInitialSelections = (book?: BookDto | null): TagSelection[] => {
  if (!book) return [];
  const tags = Array.isArray(book.tagsSummary) ? book.tagsSummary : [];
  return tags.slice(0, 3).map((name) => ({ name }));
};

export const generateTagColor = (seed: string): string => {
  const normalized = seed.trim().toLowerCase() || 'tag';
  let hash = 0;
  for (let index = 0; index < normalized.length; index += 1) {
    hash = (hash * 31 + normalized.charCodeAt(index)) >>> 0;
  }
  return TAG_COLOR_PALETTE[hash % TAG_COLOR_PALETTE.length];
};
