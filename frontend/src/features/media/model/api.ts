import { apiClient } from '@/shared/api';
import { MediaDto } from '@/entities/media';

export const listMedia = async (libraryId: string): Promise<MediaDto[]> => {
  const response = await apiClient.get<MediaDto[]>(`/libraries/${libraryId}/media`);
  return response.data;
};

export const getMedia = async (libraryId: string, mediaId: string): Promise<MediaDto> => {
  const response = await apiClient.get<MediaDto>(`/libraries/${libraryId}/media/${mediaId}`);
  return response.data;
};

export const deleteMedia = async (libraryId: string, mediaId: string): Promise<void> => {
  await apiClient.delete(`/libraries/${libraryId}/media/${mediaId}`);
};

export const restoreMedia = async (libraryId: string, mediaId: string): Promise<MediaDto> => {
  const response = await apiClient.post<MediaDto>(`/libraries/${libraryId}/media/${mediaId}/restore`);
  return response.data;
};
