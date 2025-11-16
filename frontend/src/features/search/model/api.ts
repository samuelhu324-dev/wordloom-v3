import { apiClient } from '@/shared/api';
import { SearchResultDto, SearchRequest, SearchResponse } from '@/entities/search';

export const search = async (libraryId: string, request: SearchRequest): Promise<SearchResponse> => {
  const response = await apiClient.post<SearchResponse>(`/libraries/${libraryId}/search`, request);
  return response.data;
};

export const getSearchResult = async (libraryId: string, resultId: string): Promise<SearchResultDto> => {
  const response = await apiClient.get<SearchResultDto>(`/libraries/${libraryId}/search/${resultId}`);
  return response.data;
};
