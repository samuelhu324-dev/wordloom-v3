import { useQuery } from '@tanstack/react-query';
import { fetchBasementGroups } from '../api';
import type { BasementGroupsResponseDto } from '@/entities/basement/types';

export interface UseBasementGroupsParams {
  libraryId?: string;
  skip?: number;
  limit?: number;
}

export function useBasementGroups(params: UseBasementGroupsParams) {
  const { libraryId, skip = 0, limit = 40 } = params;
  return useQuery<BasementGroupsResponseDto>({
    queryKey: ['basement', 'groups', libraryId ?? 'none', skip, limit],
    queryFn: () => fetchBasementGroups({
      libraryId: libraryId!,
      skip,
      limit,
    }),
    enabled: Boolean(libraryId),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: (failureCount, error: any) => {
      const status = error?.response?.status;
      if (!status) return failureCount < 2;
      if (status === 429) return failureCount < 2;
      return status >= 500 && failureCount < 2;
    },
  });
}
