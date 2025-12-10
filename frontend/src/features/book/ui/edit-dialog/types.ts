import type { BookCoverIconId } from '@/entities/book';

export type DialogMode = 'edit' | 'create';

export interface TagSelection {
  id?: string;
  name: string;
}

export interface BookEditFormState {
  title: string;
  summary: string;
  coverIconId: BookCoverIconId | null;
  tagInput: string;
  tagSelections: TagSelection[];
}

export const MAX_TAGS = 3;
