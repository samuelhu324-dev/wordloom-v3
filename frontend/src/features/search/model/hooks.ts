import { useQuery, useMutation } from '@tanstack/react-query';
import { search, getSearchResult } from './api';
import { SearchRequest } from '@/entities/search';

const QUERY_KEY = {
  all: ['search'] as const,
  byLibrary: (libraryId: string, query: string) => [...QUERY_KEY.all, libraryId, query] as const,
  result: (libraryId: string, resultId: string) => [...QUERY_KEY.all, libraryId, resultId] as const,
};

export const useSearch = (libraryId: string, query: string, enabled = true) => {
  return useQuery({
    queryKey: QUERY_KEY.byLibrary(libraryId, query),
    queryFn: () => search(libraryId, { query, limit: 50, offset: 0 }),
    enabled: enabled && query.length > 0,
    staleTime: 1000 * 60 * 5,
  });
};

export const useSearchResult = (libraryId: string, resultId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.result(libraryId, resultId),
    queryFn: () => getSearchResult(libraryId, resultId),
    staleTime: 1000 * 60 * 5,
  });
};

export const usePerformSearch = (libraryId: string) => {
  return useMutation({
    mutationFn: (request: SearchRequest) => search(libraryId, request),
  });
};
