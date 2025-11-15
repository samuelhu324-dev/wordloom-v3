/**
 * useLibraries Hook
 * TanStack Query wrapper for libraries operations
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listLibraries, createLibrary, updateLibrary, deleteLibrary, CreateLibraryRequest, UpdateLibraryRequest, LibraryDto } from '../api';

const LIBRARIES_QUERY_KEY = ['libraries'];

/**
 * Fetch all libraries for current user
 */
export function useLibraries() {
  return useQuery({
    queryKey: LIBRARIES_QUERY_KEY,
    queryFn: listLibraries,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Create new library
 */
export function useCreateLibrary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateLibraryRequest) => createLibrary(request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LIBRARIES_QUERY_KEY,
      });
    },
  });
}

/**
 * Update library
 */
export function useUpdateLibrary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: UpdateLibraryRequest }) =>
      updateLibrary(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LIBRARIES_QUERY_KEY,
      });
    },
  });
}

/**
 * Delete library
 */
export function useDeleteLibrary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteLibrary(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LIBRARIES_QUERY_KEY,
      });
    },
  });
}
