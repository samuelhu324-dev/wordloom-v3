import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listBlocks,
  listBlocksPaginatedPhase0,
  getBlock,
  createBlock,
  updateBlock,
  deleteBlock,
  restoreBlock,
  listDeletedBlocks,
  reorderBlock,
} from './api';
import { CreateBlockRequest, UpdateBlockRequest } from '@/entities/block';

const QUERY_KEY = {
  all: ['blocks'] as const,
  list: (filters?: { bookId?: string }) => [...QUERY_KEY.all, { filters }] as const,
  detail: (blockId: string) => [...QUERY_KEY.all, blockId] as const,
};

/** Fetch all blocks, optionally filtered by book_id */
export const useBlocks = (bookId?: string) => {
  return useQuery({
    queryKey: QUERY_KEY.list({ bookId }),
    queryFn: () => listBlocks(bookId),
    staleTime: 1000 * 60 * 5,
  });
};

// Phase0 分页（Pagination V2）
export const usePaginatedBlocksPhase0 = (
  bookId: string,
  page: number,
  pageSize: number
) => {
  return useQuery({
    queryKey: [...QUERY_KEY.list({ bookId }), { page, pageSize }],
    queryFn: () => listBlocksPaginatedPhase0(bookId, page, pageSize),
    enabled: !!bookId,
    placeholderData: (previous) => previous,
  });
};

/** Fetch single block by ID */
export const useBlock = (blockId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(blockId),
    queryFn: () => getBlock(blockId),
    staleTime: 1000 * 60 * 5,
    enabled: !!blockId,
  });
};

/** Create block (request must include book_id) */
export const useCreateBlock = () => {
  return useMutation({
    mutationFn: (request: CreateBlockRequest) => createBlock(request),
  });
};

/** Update block */
export const useUpdateBlock = (blockId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateBlockRequest) => updateBlock(blockId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(blockId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

export const useUpdateBlockContentMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { blockId: string; content: string }) =>
      updateBlock(payload.blockId, { content: payload.content }),
    onSuccess: (_, variables) => {
      if (variables?.blockId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(variables.blockId) });
      }
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

/** Delete block */
export const useDeleteBlock = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blockId: string) => deleteBlock(blockId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

export const useRestoreBlock = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blockId: string) => restoreBlock(blockId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

export const useDeletedBlocks = (bookId: string, skip=0, limit=50) => {
  return useQuery({
    queryKey: ['blocks','deleted',{bookId,skip,limit}],
    queryFn: () => listDeletedBlocks(bookId, skip, limit),
    enabled: !!bookId,
    staleTime: 1000 * 30,
  });
};

export const useReorderBlock = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { blockId: string; newOrder: string }) => reorderBlock(payload.blockId, payload.newOrder),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};
