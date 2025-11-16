/**
 * useBookshelves Hook
 * TanStack Query wrapper for bookshelf CRUD operations
 * Manages caching, mutations, and cache invalidation
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listBookshelves,
  getBookshelf,
  createBookshelf,
  updateBookshelf,
  deleteBookshelf,
  CreateBookshelfRequest,
  UpdateBookshelfRequest,
  BookshelfDto,
} from '../api';

const BOOKSHELVES_QUERY_KEY = ['bookshelves'];

/**
 * Create query key for specific bookshelf
 * Used for single-item caching
 */
const bookshelfQueryKey = (id: string) => ['bookshelves', id];

/**
 * Fetch all bookshelves for a library
 *
 * @param libraryId - The parent library ID
 * @returns useQuery result with data, isLoading, error, etc.
 */
export function useBookshelves(libraryId: string) {
  return useQuery({
    queryKey: [BOOKSHELVES_QUERY_KEY, libraryId],
    queryFn: () => listBookshelves(libraryId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!libraryId, // Only query if libraryId is provided
  });
}

/**
 * Fetch a single bookshelf by ID
 *
 * @param id - The bookshelf ID
 * @returns useQuery result with single bookshelf data
 */
export function useBookshelf(id: string) {
  return useQuery({
    queryKey: bookshelfQueryKey(id),
    queryFn: () => getBookshelf(id),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!id,
  });
}

/**
 * Create a new bookshelf
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useCreateBookshelf();
 * mutate({ name: 'My Bookshelf' });
 * ```
 */
export function useCreateBookshelf(libraryId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateBookshelfRequest) => createBookshelf(libraryId, request),
    onSuccess: () => {
      // Invalidate all bookshelves for this library
      queryClient.invalidateQueries({
        queryKey: [BOOKSHELVES_QUERY_KEY, libraryId],
      });
    },
  });
}

/**
 * Update an existing bookshelf
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useUpdateBookshelf();
 * mutate({ id: 'bookshelf-1', request: { name: 'Updated Name' } });
 * ```
 */
export function useUpdateBookshelf(libraryId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateBookshelfRequest }) =>
      updateBookshelf(id, request),
    onSuccess: (updatedBookshelf) => {
      // Update single item cache
      queryClient.setQueryData(bookshelfQueryKey(updatedBookshelf.id), updatedBookshelf);

      // Invalidate list cache
      queryClient.invalidateQueries({
        queryKey: [BOOKSHELVES_QUERY_KEY, libraryId],
      });
    },
  });
}

/**
 * Delete a bookshelf
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useDeleteBookshelf();
 * mutate('bookshelf-1');
 * ```
 */
export function useDeleteBookshelf(libraryId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteBookshelf(id),
    onSuccess: () => {
      // Invalidate all bookshelves for this library
      queryClient.invalidateQueries({
        queryKey: [BOOKSHELVES_QUERY_KEY, libraryId],
      });
    },
  });
}
