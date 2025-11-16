import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listTags, getTag, createTag, updateTag, deleteTag } from './api';
import { CreateTagRequest, UpdateTagRequest } from '@/entities/tag';

const QUERY_KEY = {
  all: ['tags'] as const,
  byLibrary: (libraryId: string) => [...QUERY_KEY.all, libraryId] as const,
  detail: (libraryId: string, tagId: string) => [...QUERY_KEY.byLibrary(libraryId), tagId] as const,
};

export const useTags = (libraryId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.byLibrary(libraryId),
    queryFn: () => listTags(libraryId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useTag = (libraryId: string, tagId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(libraryId, tagId),
    queryFn: () => getTag(libraryId, tagId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useCreateTag = (libraryId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateTagRequest) => createTag(libraryId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};

export const useUpdateTag = (libraryId: string, tagId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateTagRequest) => updateTag(libraryId, tagId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(libraryId, tagId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};

export const useDeleteTag = (libraryId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tagId: string) => deleteTag(libraryId, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};
