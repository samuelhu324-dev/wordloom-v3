import { apiClient } from '@/shared/api';
import { TagDto, CreateTagRequest, UpdateTagRequest } from '@/entities/tag';

export const listTags = async (libraryId: string): Promise<TagDto[]> => {
  const response = await apiClient.get<TagDto[]>(`/libraries/${libraryId}/tags`);
  return response.data;
};

export const getTag = async (libraryId: string, tagId: string): Promise<TagDto> => {
  const response = await apiClient.get<TagDto>(`/libraries/${libraryId}/tags/${tagId}`);
  return response.data;
};

export const createTag = async (libraryId: string, request: CreateTagRequest): Promise<TagDto> => {
  const response = await apiClient.post<TagDto>(`/libraries/${libraryId}/tags`, request);
  return response.data;
};

export const updateTag = async (libraryId: string, tagId: string, request: UpdateTagRequest): Promise<TagDto> => {
  const response = await apiClient.patch<TagDto>(`/libraries/${libraryId}/tags/${tagId}`, request);
  return response.data;
};

export const deleteTag = async (libraryId: string, tagId: string): Promise<void> => {
  await apiClient.delete(`/libraries/${libraryId}/tags/${tagId}`);
};
