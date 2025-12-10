import { useQuery } from '@tanstack/react-query';
import { listBookMaturitySnapshots, MaturitySnapshotDto } from './api';

const MATURITY_QUERY_KEY = {
  root: ['maturity'] as const,
  snapshots: (bookId: string, limit: number) => [...MATURITY_QUERY_KEY.root, 'books', bookId, 'snapshots', limit] as const,
  latest: (bookId: string) => [...MATURITY_QUERY_KEY.root, 'books', bookId, 'latest'] as const,
};

export const useBookMaturitySnapshots = (bookId: string, limit: number = 5) => {
  return useQuery({
    queryKey: MATURITY_QUERY_KEY.snapshots(bookId, limit),
    queryFn: () => listBookMaturitySnapshots(bookId, limit),
    enabled: Boolean(bookId),
    staleTime: 1000 * 60 * 2,
  });
};

export const useLatestBookMaturitySnapshot = (bookId: string) => {
  return useQuery<MaturitySnapshotDto | null>({
    queryKey: MATURITY_QUERY_KEY.latest(bookId),
    queryFn: async () => {
      const snapshots = await listBookMaturitySnapshots(bookId, 1);
      return snapshots[0] ?? null;
    },
    enabled: Boolean(bookId),
    staleTime: 1000 * 60 * 2,
  });
};

export { MATURITY_QUERY_KEY };
