import { useMemo } from 'react';
import type { BookDto } from '@/entities/book';
import { buildBookMaturitySnapshot, type BookMaturitySnapshot } from '../maturity';

interface UseBookMaturitySnapshotInput {
  books: BookDto[];
  totalFromApi?: number;
}

export const useBookMaturitySnapshot = ({ books, totalFromApi }: UseBookMaturitySnapshotInput): BookMaturitySnapshot => (
  useMemo(
    () => buildBookMaturitySnapshot(books, totalFromApi),
    [books, totalFromApi],
  )
);
