import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import type { InfiniteData, QueryKey } from '@tanstack/react-query';
import { listBooks, getBook, createBook, updateBook, deleteBook, moveBookToBasement, BookListPage, recalculateBookMaturity, uploadBookCover } from './api';
import { CreateBookRequest, UpdateBookRequest, BookDto } from '@/entities/book';

const QUERY_KEY = {
  all: ['books'] as const,
  list: (filters?: { bookshelfId?: string }) => [...QUERY_KEY.all, { filters }] as const,
  infinite: (filters?: { bookshelfId?: string; pageSize?: number }) =>
    [...QUERY_KEY.all, 'infinite', { filters }] as const,
  detail: (bookId: string) => [...QUERY_KEY.all, bookId] as const,
};

const mergeBookIntoCachedPage = (page: BookListPage, updatedBook: BookDto): { page: BookListPage; changed: boolean } => {
  let changed = false;
  const items = page.items.map((item) => {
    if (item.id === updatedBook.id) {
      changed = true;
      return updatedBook;
    }
    return item;
  });
  if (!changed) {
    return { page, changed: false };
  }
  return { page: { ...page, items }, changed: true };
};

const mergeBookIntoCache = (oldData: unknown, updatedBook: BookDto): unknown => {
  if (!oldData || typeof oldData !== 'object') {
    return oldData;
  }

  if (Array.isArray((oldData as any).pages)) {
    const existing = oldData as InfiniteData<BookListPage>;
    let hasChanges = false;
    const pages = existing.pages.map((page) => {
      const { page: nextPage, changed } = mergeBookIntoCachedPage(page, updatedBook);
      if (changed) {
        hasChanges = true;
        return nextPage;
      }
      return page;
    });
    if (!hasChanges) {
      return oldData;
    }
    return {
      ...existing,
      pages,
    };
  }

  if (Array.isArray((oldData as any).items)) {
    const existing = oldData as BookListPage;
    const { page: nextPage, changed } = mergeBookIntoCachedPage(existing, updatedBook);
    if (!changed) {
      return oldData;
    }
    return nextPage;
  }

  return oldData;
};

const applyPinnedFlagToCachedPage = (page: BookListPage, bookId: string, isPinned: boolean) => {
  let changed = false;
  const items = page.items.map((item) => {
    if (item.id !== bookId) {
      return item;
    }
    if (item.is_pinned === isPinned) {
      return item;
    }
    changed = true;
    return { ...item, is_pinned: isPinned };
  });

  if (!changed) {
    return page;
  }

  return { ...page, items };
};

const applyPinnedFlagToCache = (oldData: unknown, bookId: string, isPinned: boolean): unknown => {
  if (!oldData || typeof oldData !== 'object') {
    return oldData;
  }

  if ((oldData as BookDto)?.id === bookId) {
    const book = oldData as BookDto;
    if (book.is_pinned === isPinned) {
      return book;
    }
    return { ...book, is_pinned: isPinned };
  }

  if (Array.isArray((oldData as any).pages)) {
    const existing = oldData as InfiniteData<BookListPage>;
    let changed = false;
    const pages = existing.pages.map((page) => {
      const nextPage = applyPinnedFlagToCachedPage(page, bookId, isPinned);
      if (nextPage !== page) {
        changed = true;
      }
      return nextPage;
    });
    if (!changed) {
      return oldData;
    }
    return { ...existing, pages };
  }

  if (Array.isArray((oldData as any).items)) {
    const existing = oldData as BookListPage;
    const nextPage = applyPinnedFlagToCachedPage(existing, bookId, isPinned);
    if (nextPage === existing) {
      return oldData;
    }
    return nextPage;
  }

  return oldData;
};

const findBookInCachedData = (data: unknown, bookId: string): BookDto | undefined => {
  if (!data || typeof data !== 'object') {
    return undefined;
  }

  if ((data as BookDto)?.id === bookId) {
    return data as BookDto;
  }

  if (Array.isArray((data as any).items)) {
    return ((data as BookListPage).items || []).find((item) => item.id === bookId);
  }

  if (Array.isArray((data as any).pages)) {
    const pages = (data as InfiniteData<BookListPage>).pages;
    for (const page of pages) {
      const match = page.items.find((item) => item.id === bookId);
      if (match) {
        return match;
      }
    }
  }

  return undefined;
};

const mergeDisplayFields = (updated: BookDto, fallback?: BookDto): BookDto => {
  if (!fallback) {
    return updated;
  }

  let next = updated;

  if ((!updated.tagsSummary || updated.tagsSummary.length === 0) && fallback.tagsSummary?.length) {
    next = { ...next, tagsSummary: fallback.tagsSummary };
  }

  return next;
};

/** Fetch all books, optionally filtered by bookshelf_id */
export const useBooks = (bookshelfId?: string) => {
  return useQuery({
    queryKey: QUERY_KEY.list({ bookshelfId }),
    queryFn: () => listBooks(bookshelfId),
    staleTime: 1000 * 60 * 5,
  });
};

/** Infinite books list for incremental loading */
export const useInfiniteBooks = (bookshelfId?: string, pageSize: number = 20) => {
  return useInfiniteQuery<BookListPage>({
    queryKey: QUERY_KEY.infinite({ bookshelfId, pageSize }),
    queryFn: ({ pageParam }) => {
      const page = typeof pageParam === 'number' ? pageParam : 1;
      return listBooks(bookshelfId, page, pageSize);
    },
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.page + 1 : undefined),
    initialPageParam: 1,
    staleTime: 1000 * 60 * 5,
    placeholderData: (previous) => previous,
  });
};

/** Fetch single book by ID */
export const useBook = (bookId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(bookId),
    queryFn: () => getBook(bookId),
    staleTime: 1000 * 60 * 5,
    enabled: !!bookId,
  });
};

/** Create book (request must include bookshelf_id) */
export const useCreateBook = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateBookRequest) => createBook(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

/** Update book */
export const useUpdateBook = (bookId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateBookRequest) => updateBook(bookId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(bookId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

/** Delete book */
export const useDeleteBook = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bookId: string) => deleteBook(bookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

interface MoveBookToBasementVariables {
  bookId: string;
  basementBookshelfId: string;
}

/** Soft delete book by moving it into Basement */
export const useMoveBookToBasement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bookId, basementBookshelfId }: MoveBookToBasementVariables) =>
      moveBookToBasement({ bookId, basementBookshelfId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['basement'] });
      queryClient.invalidateQueries({ queryKey: ['bookshelves', 'dashboard'] });
    },
  });
};

/** Toggle pinned state for a book */
export const useToggleBookPin = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bookId, isPinned }: { bookId: string; isPinned: boolean }) =>
      updateBook(bookId, { is_pinned: isPinned }),
    onMutate: async ({ bookId, isPinned }) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEY.all });
      const previousDetail = queryClient.getQueryData<BookDto>(QUERY_KEY.detail(bookId));
      const previousListEntries = queryClient.getQueriesData({ queryKey: QUERY_KEY.all });

       const fallbackBook = previousDetail
         ?? previousListEntries
           .map(([, data]) => findBookInCachedData(data, bookId))
           .find((item): item is BookDto => Boolean(item));

      queryClient.setQueryData(QUERY_KEY.detail(bookId), (old) => (old ? { ...old, is_pinned: isPinned } : old));
      queryClient.setQueriesData({ queryKey: QUERY_KEY.all }, (oldData) => applyPinnedFlagToCache(oldData, bookId, isPinned));

      return {
        previousDetail,
        previousListEntries,
        fallbackBook,
      } as {
        previousDetail?: BookDto;
        previousListEntries: Array<[QueryKey, unknown]>;
        fallbackBook?: BookDto;
      };
    },
    onError: (_error, variables, context) => {
      if (!context) return;
      if (context.previousDetail) {
        queryClient.setQueryData(QUERY_KEY.detail(variables.bookId), context.previousDetail);
      }
      context.previousListEntries?.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
    },
    onSuccess: (updatedBook, _variables, context) => {
      const hydrated = mergeDisplayFields(updatedBook, context?.fallbackBook);
      queryClient.setQueryData(QUERY_KEY.detail(hydrated.id), hydrated);
      queryClient.setQueriesData({ queryKey: QUERY_KEY.all }, (oldData) => mergeBookIntoCache(oldData, hydrated));
    },
    onSettled: (_result, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
      queryClient.invalidateQueries({ queryKey: ['bookshelves', 'dashboard'] });
      if (variables?.bookId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(variables.bookId) });
      }
    },
  });
};

/** Recalculate maturity for a book (with optional ops bonus). */
export const useRecalculateBookMaturity = (bookId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload?: Parameters<typeof recalculateBookMaturity>[1]) =>
      recalculateBookMaturity(bookId, payload),
    onSuccess: (updatedBook) => {
      // Update detail cache immediately and refresh related lists.
      queryClient.setQueryData(QUERY_KEY.detail(updatedBook.id), updatedBook);
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(updatedBook.id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
      queryClient.invalidateQueries({ queryKey: ['maturity'] });
    },
  });
};

/** Upload a custom cover image for a stable book */
export const useUploadBookCover = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bookId, file, correlationId }: { bookId: string; file: File; correlationId?: string }) =>
      uploadBookCover(bookId, file, correlationId),
    onSuccess: (updatedBook) => {
      queryClient.setQueryData(QUERY_KEY.detail(updatedBook.id), updatedBook);
      queryClient.setQueriesData({ queryKey: QUERY_KEY.all }, (oldData) => mergeBookIntoCache(oldData, updatedBook));
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};
