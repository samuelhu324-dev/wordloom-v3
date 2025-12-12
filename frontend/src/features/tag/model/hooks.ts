import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  searchTags,
  getTag,
  createTag,
  createSubtag,
  updateTag,
  deleteTag,
  getMostUsedTags,
  listTags,
  restoreTag,
  SearchTagsParams,
  CreateSubtagRequest,
} from './api';
import { CreateTagRequest, UpdateTagRequest } from '@/entities/tag';

const QUERY_KEY = {
  all: ['tags'] as const,
  search: (keyword: string, limit: number, order: string) => [...QUERY_KEY.all, 'search', keyword, limit, order] as const,
  mostUsed: (limit: number) => [...QUERY_KEY.all, 'most-used', limit] as const,
  detail: (tagId: string) => [...QUERY_KEY.all, tagId] as const,
  catalog: (
    page: number,
    size: number,
    includeDeleted: boolean,
    onlyTopLevel: boolean,
    order: string,
  ) => [...QUERY_KEY.all, 'catalog', page, size, includeDeleted, onlyTopLevel, order] as const,
};

interface UseTagSearchOptions extends Omit<SearchTagsParams, 'keyword'> {
  enabled?: boolean;
}

export const useTagSearch = (keyword: string, options?: UseTagSearchOptions) => {
  const limit = options?.limit ?? 12;
  const enabled = options?.enabled ?? Boolean(keyword?.trim());
  const trimmed = keyword?.trim() ?? '';
  const order = 'name_asc';
  return useQuery({
    queryKey: QUERY_KEY.search(trimmed, limit, order),
    queryFn: () => searchTags({ keyword: trimmed, limit, order }),
    enabled: enabled && trimmed.length > 0,
    staleTime: 1000 * 60 * 5,
  });
};

interface UseMostUsedTagsOptions {
  limit?: number;
  enabled?: boolean;
}

export const useMostUsedTags = (options?: UseMostUsedTagsOptions) => {
  const limit = options?.limit ?? 10;
  const enabled = options?.enabled ?? true;
  return useQuery({
    queryKey: QUERY_KEY.mostUsed(limit),
    queryFn: () => getMostUsedTags(limit),
    enabled,
    staleTime: 1000 * 60 * 5,
  });
};

export const useTag = (tagId: string | undefined) => {
  return useQuery({
    queryKey: QUERY_KEY.detail(tagId || ''),
    queryFn: () => getTag(tagId!),
    enabled: Boolean(tagId),
    staleTime: 1000 * 60 * 5,
  });
};

export const useCreateTag = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateTagRequest) => createTag(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

interface CreateSubtagPayload {
  parentTagId: string;
  data: CreateSubtagRequest;
}

export const useCreateSubtag = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ parentTagId, data }: CreateSubtagPayload) => createSubtag(parentTagId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

interface UpdateTagPayload {
  tagId: string;
  data: UpdateTagRequest;
}

export const useUpdateTag = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tagId, data }: UpdateTagPayload) => updateTag(tagId, data),
    onSuccess: (_, variables) => {
      if (variables?.tagId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(variables.tagId) });
      }
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

export const useDeleteTag = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tagId: string) => deleteTag(tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

export const useRestoreTag = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tagId: string) => restoreTag(tagId),
    onSuccess: (_, tagId) => {
      if (tagId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEY.detail(tagId) });
      }
      queryClient.invalidateQueries({ queryKey: QUERY_KEY.all });
    },
  });
};

interface UseTagCatalogOptions {
  page?: number;
  size?: number;
  includeDeleted?: boolean;
  onlyTopLevel?: boolean;
  order?: 'name_asc' | 'name_desc' | 'usage_desc' | 'created_desc';
  enabled?: boolean;
}

export const useTagCatalog = (options?: UseTagCatalogOptions) => {
  const page = options?.page ?? 1;
  const size = options?.size ?? 50;
  const includeDeleted = options?.includeDeleted ?? false;
  const onlyTopLevel = options?.onlyTopLevel ?? true;
  const order = options?.order ?? 'name_asc';
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: QUERY_KEY.catalog(page, size, includeDeleted, onlyTopLevel, order),
    queryFn: () => listTags({
      page,
      size,
      includeDeleted,
      onlyTopLevel,
      order,
    }),
    enabled,
    staleTime: 1000 * 60 * 2,
  });
};
