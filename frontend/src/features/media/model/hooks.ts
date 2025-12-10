import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listMedia, getMedia, deleteMedia, restoreMedia } from './api';

const QUERY_KEY = {
  all: ['media'] as const,
  byLibrary: (libraryId: string) => [...QUERY_KEY.all, libraryId] as const,
  detail: (libraryId: string, mediaId: string) => [...QUERY_KEY.byLibrary(libraryId), mediaId] as const,
};

export const useMedia = (libraryId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.byLibrary(libraryId),
    queryFn: () => listMedia(libraryId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useMediaItem = (libraryId: string, mediaId: string) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(libraryId, mediaId),
    queryFn: () => getMedia(libraryId, mediaId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useDeleteMedia = (libraryId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mediaId: string) => deleteMedia(libraryId, mediaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};

export const useRestoreMedia = (libraryId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mediaId: string) => restoreMedia(libraryId, mediaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.byLibrary(libraryId) });
    },
  });
};
