/**
 * useBooks Hook
 * TanStack Query wrapper for book CRUD operations
 * Manages caching, mutations, and cache invalidation
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listBooks,
  getBook,
  createBook,
  updateBook,
  deleteBook,
  moveBook,
  archiveBook,
  restoreBook,
  CreateBookRequest,
  UpdateBookRequest,
  BookDto,
} from '../api';

const BOOKS_QUERY_KEY = ['books'];

/**
 * Create query key for specific book
 * Used for single-item caching
 */
const bookQueryKey = (id: string) => ['books', id];

/**
 * Fetch all books in a bookshelf
 *
 * @param bookshelfId - The parent bookshelf ID
 * @param includeArchived - Whether to include archived books
 * @returns useQuery result with data, isLoading, error, etc.
 */
export function useBooks(bookshelfId: string, includeArchived: boolean = false) {
  return useQuery({
    queryKey: [BOOKS_QUERY_KEY, bookshelfId, includeArchived],
    queryFn: () => listBooks(bookshelfId, includeArchived),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!bookshelfId,
  });
}

/**
 * Fetch a single book by ID
 *
 * @param id - The book ID
 * @returns useQuery result with single book data
 */
export function useBook(id: string) {
  return useQuery({
    queryKey: bookQueryKey(id),
    queryFn: () => getBook(id),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!id,
  });
}

/**
 * Create a new book
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useCreateBook(bookshelfId);
 * mutate({ title: 'My Book' });
 * ```
 */
export function useCreateBook(bookshelfId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateBookRequest) => createBook(request),
    onSuccess: () => {
      // Invalidate books list for this bookshelf
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, bookshelfId],
      });
    },
  });
}

/**
 * Update an existing book
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useUpdateBook(bookshelfId);
 * mutate({ id: 'book-1', request: { title: 'Updated Title' } });
 * ```
 */
export function useUpdateBook(bookshelfId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateBookRequest }) =>
      updateBook(id, request),
    onSuccess: (updatedBook) => {
      // Update single item cache
      queryClient.setQueryData(bookQueryKey(updatedBook.id), updatedBook);

      // Invalidate books list
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, bookshelfId],
      });
    },
  });
}

/**
 * Delete a book (soft delete)
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useDeleteBook(bookshelfId);
 * mutate('book-1');
 * ```
 */
export function useDeleteBook(bookshelfId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteBook(id),
    onSuccess: () => {
      // Invalidate books list
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, bookshelfId],
      });
    },
  });
}

/**
 * Move a book to a different bookshelf
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useMoveBook(currentBookshelfId);
 * mutate({ id: 'book-1', targetBookshelfId: 'bookshelf-2' });
 * ```
 */
export function useMoveBook(currentBookshelfId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, targetBookshelfId }: { id: string; targetBookshelfId: string }) =>
      moveBook(id, targetBookshelfId),
    onSuccess: (movedBook) => {
      // Invalidate both source and target bookshelf lists
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, currentBookshelfId],
      });
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, movedBook.bookshelfId],
      });
    },
  });
}

/**
 * Archive a book
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useArchiveBook(bookshelfId);
 * mutate('book-1');
 * ```
 */
export function useArchiveBook(bookshelfId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => archiveBook(id),
    onSuccess: (archivedBook) => {
      // Update single item cache
      queryClient.setQueryData(bookQueryKey(archivedBook.id), archivedBook);

      // Invalidate books list
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, bookshelfId],
      });
    },
  });
}

/**
 * Restore an archived book
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useRestoreBook(bookshelfId);
 * mutate('book-1');
 * ```
 */
export function useRestoreBook(bookshelfId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => restoreBook(id),
    onSuccess: (restoredBook) => {
      // Update single item cache
      queryClient.setQueryData(bookQueryKey(restoredBook.id), restoredBook);

      // Invalidate books list
      queryClient.invalidateQueries({
        queryKey: [BOOKS_QUERY_KEY, bookshelfId],
      });
    },
  });
}
