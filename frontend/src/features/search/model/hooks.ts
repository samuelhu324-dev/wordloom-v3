import { useQuery, useMutation } from '@tanstack/react-query';
import { searchGlobal, searchBlocks, search, getSearchResult, searchBooks } from './api';
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

// Global search (multi-entity scope)
export const useGlobalSearch = (q: string, limit = 20, offset = 0) => {
  return useQuery({
    queryKey: ['search','global',{ q, limit, offset }],
    queryFn: () => searchGlobal(q, limit, offset),
    enabled: q.length > 0,
    placeholderData: (previous) => previous,
  });
};

// Block-level (book scoped) search
export const useBlockSearch = (q: string, bookId?: string, limit = 20, offset = 0) => {
  return useQuery({
    queryKey: ['search','blocks',{ q, bookId, limit, offset }],
    queryFn: () => searchBlocks(q, bookId, limit, offset),
    enabled: q.length > 0,
    placeholderData: (previous) => previous,
  });
};

export const useBookSearch = (
  params: {
    text: string;
    bookshelfId?: string;
    limit?: number;
    offset?: number;
    enabled?: boolean;
  },
) => {
  const { text, enabled = true, ...rest } = params;
  return useQuery({
    queryKey: ['search','books',{ text, ...rest }],
    queryFn: () => searchBooks({ text, ...rest }),
    enabled: enabled && text.trim().length >= 3,
    staleTime: 1000 * 30,
    placeholderData: (previous) => previous,
  });
};
