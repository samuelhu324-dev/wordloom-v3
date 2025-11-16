import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listBlocks, getBlock, createBlock, updateBlock, deleteBlock } from './api';
import { CreateBlockRequest, UpdateBlockRequest } from '@/entities/block';

const QUERY_KEY = {
  all: ['blocks'] as const,
  byBook: (libraryId: string, bookshelfId: string, bookId: string) =>
    [...QUERY_KEY.all, libraryId, bookshelfId, bookId] as const,
  detail: (libraryId: string, bookshelfId: string, bookId: string, blockId: string) =>
    [...QUERY_KEY.byBook(libraryId, bookshelfId, bookId), blockId] as const,
};

export const useBlocks = (libraryId: string, bookshelfId: string, bookId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.byBook(libraryId, bookshelfId, bookId),
    queryFn: () => listBlocks(libraryId, bookshelfId, bookId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useBlock = (libraryId: string, bookshelfId: string, bookId: string, blockId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(libraryId, bookshelfId, bookId, blockId),
    queryFn: () => getBlock(libraryId, bookshelfId, bookId, blockId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useCreateBlock = (libraryId: string, bookshelfId: string, bookId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateBlockRequest) => createBlock(libraryId, bookshelfId, bookId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byBook(libraryId, bookshelfId, bookId) });
    },
  });
};

export const useUpdateBlock = (
  libraryId: string,
  bookshelfId: string,
  bookId: string,
  blockId: string
) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateBlockRequest) => updateBlock(libraryId, bookshelfId, bookId, blockId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(libraryId, bookshelfId, bookId, blockId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byBook(libraryId, bookshelfId, bookId) });
    },
  });
};

export const useDeleteBlock = (libraryId: string, bookshelfId: string, bookId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blockId: string) => deleteBlock(libraryId, bookshelfId, bookId, blockId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byBook(libraryId, bookshelfId, bookId) });
    },
  });
};
