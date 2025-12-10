import { apiClient } from '@/shared/api';
import { TagDto, CreateTagRequest, UpdateTagRequest } from '@/entities/tag';

const BASE_URL = '/tags';

interface TagListApiResponse {
  total?: number;
  items?: TagDto[];
}

export interface TagListResponseDto {
  total: number;
  items: TagDto[];
  page: number;
  size: number;
  has_more: boolean;
}

export interface ListTagsParams {
  page?: number;
  size?: number;
  includeDeleted?: boolean;
  onlyTopLevel?: boolean;
  order?: 'name_asc' | 'name_desc' | 'usage_desc' | 'created_desc';
}

const normalizeListPayload = (payload?: TagListApiResponse | TagDto[]) => {
  if (!payload) return [] as TagDto[];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.items)) return payload.items;
  return [] as TagDto[];
};

export interface SearchTagsParams {
  keyword?: string;
  limit?: number;
  order?: 'name_asc' | 'name_desc' | 'usage_desc' | 'created_desc';
}

export const searchTags = async (params: SearchTagsParams = {}): Promise<TagDto[]> => {
  const { keyword, limit = 12, order = 'name_asc' } = params;
  const response = await apiClient.get<TagListApiResponse | TagDto[]>(BASE_URL, {
    params: {
      keyword: keyword || undefined,
      limit,
      order,
    },
  });
  return normalizeListPayload(response.data);
};

export const getMostUsedTags = async (limit = 10): Promise<TagDto[]> => {
  const response = await apiClient.get<TagListApiResponse | TagDto[]>(`${BASE_URL}/most-used`, {
    params: { limit },
  });
  return normalizeListPayload(response.data);
};

export const listTags = async (params: ListTagsParams = {}): Promise<TagListResponseDto> => {
  const {
    page = 1,
    size = 50,
    includeDeleted = false,
    onlyTopLevel = true,
    order = 'name_asc',
  } = params;

  const response = await apiClient.get<TagListResponseDto>(`${BASE_URL}/catalog`, {
    params: {
      page,
      size,
      include_deleted: includeDeleted ? 'true' : undefined,
      only_top_level: onlyTopLevel ? 'true' : 'false',
      order,
    },
  });

  const data = response.data || ({} as TagListResponseDto);
  const items = Array.isArray((data as any).items) ? (data as any).items as TagDto[] : [];

  return {
    total: typeof data.total === 'number' ? data.total : items.length,
    items,
    page: typeof data.page === 'number' ? data.page : page,
    size: typeof data.size === 'number' ? data.size : size,
    has_more: Boolean((data as any).has_more) && items.length > 0
      ? Boolean((data as any).has_more)
      : page * size < (typeof data.total === 'number' ? data.total : items.length),
  };
};

export const getTag = async (tagId: string): Promise<TagDto> => {
  const response = await apiClient.get<TagDto>(`${BASE_URL}/${tagId}`);
  return response.data;
};

export const createTag = async (request: CreateTagRequest): Promise<TagDto> => {
  const response = await apiClient.post<TagDto>(BASE_URL, request);
  return response.data;
};

export const updateTag = async (tagId: string, request: UpdateTagRequest): Promise<TagDto> => {
  const response = await apiClient.patch<TagDto>(`${BASE_URL}/${tagId}`, request);
  return response.data;
};

export const deleteTag = async (tagId: string): Promise<void> => {
  await apiClient.delete(`${BASE_URL}/${tagId}`);
};

export const restoreTag = async (tagId: string): Promise<TagDto> => {
  const response = await apiClient.post<TagDto>(`${BASE_URL}/${tagId}/restore`);
  return response.data;
};

export type TagEntityType = 'library' | 'bookshelf' | 'book' | 'block';

export interface TagAssociationPayload {
  tagId: string;
  entityId: string;
  entityType?: TagEntityType;
}

export const associateTagWithEntity = async ({
  tagId,
  entityId,
  entityType = 'book',
}: TagAssociationPayload): Promise<void> => {
  await apiClient.post(
    `${BASE_URL}/${tagId}/associate`,
    undefined,
    {
      params: {
        entity_type: entityType,
        entity_id: entityId,
      },
    },
  );
};

export const disassociateTagFromEntity = async ({
  tagId,
  entityId,
  entityType = 'book',
}: TagAssociationPayload): Promise<void> => {
  await apiClient.delete(
    `${BASE_URL}/${tagId}/disassociate`,
    {
      params: {
        entity_type: entityType,
        entity_id: entityId,
      },
    },
  );
};
