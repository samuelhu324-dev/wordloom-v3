import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listBooks, getBook, createBook, updateBook, deleteBook } from './api';
import { BookDto, CreateBookRequest, UpdateBookRequest } from '@/entities/book';

const QUERY_KEY = {
  all: ['books'] as const,
  byBookshelf: (libraryId: string, bookshelfId: string) => [...QUERY_KEY.all, libraryId, bookshelfId] as const,
  detail: (libraryId: string, bookshelfId: string, bookId: string) =>
    [...QUERY_KEY.byBookshelf(libraryId, bookshelfId), bookId] as const,
};

export const useBooks = (libraryId: string, bookshelfId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.byBookshelf(libraryId, bookshelfId),
    queryFn: () => listBooks(libraryId, bookshelfId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useBook = (libraryId: string, bookshelfId: string, bookId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(libraryId, bookshelfId, bookId),
    queryFn: () => getBook(libraryId, bookshelfId, bookId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useCreateBook = (libraryId: string, bookshelfId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateBookRequest) => createBook(libraryId, bookshelfId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byBookshelf(libraryId, bookshelfId) });
    },
  });
};

export const useUpdateBook = (libraryId: string, bookshelfId: string, bookId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateBookRequest) => updateBook(libraryId, bookshelfId, bookId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(libraryId, bookshelfId, bookId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byBookshelf(libraryId, bookshelfId) });
    },
  });
};

export const useDeleteBook = (libraryId: string, bookshelfId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bookId: string) => deleteBook(libraryId, bookshelfId, bookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byBookshelf(libraryId, bookshelfId) });
    },
  });
};
