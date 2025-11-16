'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as libraryApi from './api';
import { CreateLibraryRequest, LibraryDto, UpdateLibraryRequest } from '@/entities/library';

const QUERY_KEY = ['libraries'];
const QUERY_KEY_DETAIL = (id: string) => [...QUERY_KEY, id];

/** Fetch all libraries */
export function useLibraries() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: libraryApi.listLibraries,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/** Fetch single library */
export function useLibrary(id: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEY_DETAIL(id || ''),
    queryFn: () => libraryApi.getLibrary(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

/** Create library */
export function useCreateLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: libraryApi.createLibrary,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

/** Update library */
export function useUpdateLibrary(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateLibraryRequest) =>
      libraryApi.updateLibrary(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_DETAIL(id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

/** Delete library */
export function useDeleteLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: libraryApi.deleteLibrary,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
