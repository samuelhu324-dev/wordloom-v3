import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listBookshelves, getBookshelf, createBookshelf, updateBookshelf, deleteBookshelf } from './api';
import { BookshelfDto, CreateBookshelfRequest, UpdateBookshelfRequest } from '@/entities/bookshelf';

const QUERY_KEY = {
  all: ['bookshelves'] as const,
  byLibrary: (libraryId: string) => [...QUERY_KEY.all, libraryId] as const,
  detail: (libraryId: string, bookshelfId: string) => [...QUERY_KEY.byLibrary(libraryId), bookshelfId] as const,
};

export const useBookshelves = (libraryId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.byLibrary(libraryId),
    queryFn: () => listBookshelves(libraryId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useBookshelf = (libraryId: string, bookshelfId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(libraryId, bookshelfId),
    queryFn: () => getBookshelf(libraryId, bookshelfId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useCreateBookshelf = (libraryId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateBookshelfRequest) => createBookshelf(libraryId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};

export const useUpdateBookshelf = (libraryId: string, bookshelfId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateBookshelfRequest) => updateBookshelf(libraryId, bookshelfId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(libraryId, bookshelfId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};

export const useDeleteBookshelf = (libraryId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bookshelfId: string) => deleteBookshelf(libraryId, bookshelfId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};
