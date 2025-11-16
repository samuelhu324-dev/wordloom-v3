/**
 * useBlocks Hook
 * TanStack Query wrapper for block CRUD operations
 * Manages caching, mutations, and cache invalidation
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listBlocks,
  getBlock,
  createBlock,
  updateBlock,
  deleteBlock,
  reorderBlock,
  duplicateBlock,
  convertBlockType,
  getBlockHistory,
  CreateBlockRequest,
  UpdateBlockRequest,
  BlockDto,
} from '../api';

const BLOCKS_QUERY_KEY = ['blocks'];

/**
 * Create query key for specific block
 * Used for single-item caching
 */
const blockQueryKey = (id: string) => ['blocks', id];

/**
 * Fetch all blocks in a book
 * Blocks are automatically ordered by fractionalIndex (not creation date)
 *
 * @param bookId - The parent book ID
 * @returns useQuery result with data, isLoading, error, etc.
 */
export function useBlocks(bookId: string) {
  return useQuery({
    queryKey: [BLOCKS_QUERY_KEY, bookId],
    queryFn: () => listBlocks(bookId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!bookId,
  });
}

/**
 * Fetch a single block by ID
 *
 * @param id - The block ID
 * @returns useQuery result with single block data
 */
export function useBlock(id: string) {
  return useQuery({
    queryKey: blockQueryKey(id),
    queryFn: () => getBlock(id),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!id,
  });
}

/**
 * Create a new block
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useCreateBlock(bookId);
 * mutate({ type: 'markdown', content: '# Heading' });
 * ```
 */
export function useCreateBlock(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateBlockRequest) => createBlock(request),
    onSuccess: () => {
      // Invalidate blocks list for this book
      queryClient.invalidateQueries({
        queryKey: [BLOCKS_QUERY_KEY, bookId],
      });
    },
  });
}

/**
 * Update an existing block
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useUpdateBlock(bookId);
 * mutate({ id: 'block-1', request: { content: 'Updated content' } });
 * ```
 */
export function useUpdateBlock(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateBlockRequest }) =>
      updateBlock(id, request),
    onSuccess: (updatedBlock) => {
      // Update single item cache
      queryClient.setQueryData(blockQueryKey(updatedBlock.id), updatedBlock);

      // Invalidate blocks list
      queryClient.invalidateQueries({
        queryKey: [BLOCKS_QUERY_KEY, bookId],
      });
    },
  });
}

/**
 * Delete a block (soft delete)
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useDeleteBlock(bookId);
 * mutate('block-1');
 * ```
 */
export function useDeleteBlock(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteBlock(id),
    onSuccess: () => {
      // Invalidate blocks list
      queryClient.invalidateQueries({
        queryKey: [BLOCKS_QUERY_KEY, bookId],
      });
    },
  });
}

/**
 * Reorder a block using fractionalIndex
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useReorderBlock(bookId);
 * mutate({ id: 'block-1', beforeBlockId: 'block-2' }); // Insert before block-2
 * ```
 */
export function useReorderBlock(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, beforeBlockId }: { id: string; beforeBlockId: string | null }) =>
      reorderBlock(id, beforeBlockId),
    onSuccess: (reorderedBlock) => {
      // Invalidate blocks list (order may have changed)
      queryClient.invalidateQueries({
        queryKey: [BLOCKS_QUERY_KEY, bookId],
      });
    },
  });
}

/**
 * Duplicate a block (create copy)
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useDuplicateBlock(bookId);
 * mutate('block-1');
 * ```
 */
export function useDuplicateBlock(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => duplicateBlock(id),
    onSuccess: () => {
      // Invalidate blocks list (new block added)
      queryClient.invalidateQueries({
        queryKey: [BLOCKS_QUERY_KEY, bookId],
      });
    },
  });
}

/**
 * Convert block between types
 *
 * Usage:
 * ```
 * const { mutate, isPending } = useConvertBlockType(bookId);
 * mutate({ id: 'block-1', targetType: 'heading' });
 * ```
 */
export function useConvertBlockType(bookId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      targetType,
    }: {
      id: string;
      targetType: 'markdown' | 'heading' | 'image' | 'video';
    }) => convertBlockType(id, targetType),
    onSuccess: (convertedBlock) => {
      // Update single item cache
      queryClient.setQueryData(blockQueryKey(convertedBlock.id), convertedBlock);

      // Invalidate blocks list
      queryClient.invalidateQueries({
        queryKey: [BLOCKS_QUERY_KEY, bookId],
      });
    },
  });
}

/**
 * Fetch block history (audit trail)
 *
 * @param blockId - The block ID
 * @returns useQuery result with array of historical block versions
 */
export function useBlockHistory(blockId: string) {
  return useQuery({
    queryKey: [blockQueryKey(blockId), 'history'],
    queryFn: () => getBlockHistory(blockId),
    staleTime: 10 * 60 * 1000, // 10 minutes (history changes infrequently)
    enabled: !!blockId,
  });
}
