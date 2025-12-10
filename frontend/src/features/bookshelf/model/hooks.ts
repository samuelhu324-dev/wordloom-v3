import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listBookshelves,
  getBookshelf,
  createBookshelf,
  updateBookshelf,
  deleteBookshelf,
  BOOKSHELF_LIST_DEFAULT_PAGE_SIZE,
  ListBookshelvesOptions,
  fetchBookshelfDashboard,
  FetchBookshelfDashboardOptions,
} from './api';
import {
  CreateBookshelfRequest,
  UpdateBookshelfRequest,
  BookshelfDashboardSort,
  BookshelfDashboardFilter,
} from '@/entities/bookshelf';

const QUERY_KEY = {
  all: ['bookshelves'] as const,
  list: (filters?: { libraryId?: string; page?: number; pageSize?: number }) => [...QUERY_KEY.all, { filters }] as const,
  detail: (bookshelfId: string) => [...QUERY_KEY.all, bookshelfId] as const,
  dashboard: (filters: {
    libraryId: string;
    page: number;
    size: number;
    sort: BookshelfDashboardSort;
    status: BookshelfDashboardFilter;
  }) => [...QUERY_KEY.all, 'dashboard', { filters }] as const,
};

type UseBookshelvesParams = Pick<ListBookshelvesOptions, 'libraryId' | 'page' | 'pageSize'>;

/** Fetch paginated bookshelves (optionally filtered by library_id) */
export const useBookshelves = (params?: UseBookshelvesParams) => {
  const { libraryId, page = 1, pageSize = BOOKSHELF_LIST_DEFAULT_PAGE_SIZE } = params ?? {};
  return useQuery({
    queryKey: QUERY_KEY.list({ libraryId, page, pageSize }),
    queryFn: () => listBookshelves({ libraryId, page, pageSize }),
    staleTime: 1000 * 60 * 5,
  });
};

/** Fetch single bookshelf by ID */
export const useBookshelf = (bookshelfId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(bookshelfId),
    queryFn: () => getBookshelf(bookshelfId),
    staleTime: 1000 * 60 * 5,
    enabled: !!bookshelfId,
  });
};

/** Create bookshelf (must include library_id in request) */
export const useCreateBookshelf = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateBookshelfRequest) => createBookshelf(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

/** Update bookshelf */
export const useUpdateBookshelf = (bookshelfId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateBookshelfRequest) => updateBookshelf(bookshelfId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(bookshelfId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

/** Delete bookshelf */
export const useDeleteBookshelf = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bookshelfId: string) => deleteBookshelf(bookshelfId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
      queryClient.invalidateQueries({ queryKey: ['bookshelves', 'dashboard'] });
    },
  });
};

interface QuickUpdateBookshelfInput {
  bookshelfId: string;
  data: Partial<UpdateBookshelfRequest>;
}

export const useQuickUpdateBookshelf = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bookshelfId, data }: QuickUpdateBookshelfInput) =>
      updateBookshelf(bookshelfId, data),
    onSuccess: (updatedBookshelf) => {
      queryClient.setQueryData(QUERY_KEY.detail(updatedBookshelf.id), updatedBookshelf);
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
      queryClient.invalidateQueries({ queryKey: ['bookshelves', 'dashboard'] });
    },
  });
};

type UseBookshelfDashboardParams = Omit<FetchBookshelfDashboardOptions, 'libraryId'> & {
  libraryId?: string;
};

export const useBookshelfDashboard = (params: UseBookshelfDashboardParams) => {
  const {
    libraryId,
    page = 1,
    size = 20,
    sort = 'recent_activity',
    statusFilter = 'active',
    fallbackThemeColor,
  } = params;

  return useQuery({
    queryKey: QUERY_KEY.dashboard({
      libraryId: libraryId ?? 'unknown',
      page,
      size,
      sort,
      status: statusFilter,
    }),
    queryFn: () =>
      fetchBookshelfDashboard({
        libraryId: libraryId as string,
        page,
        size,
        sort,
        statusFilter,
        fallbackThemeColor,
      }),
    enabled: Boolean(libraryId),
    staleTime: 60_000,
  });
};
