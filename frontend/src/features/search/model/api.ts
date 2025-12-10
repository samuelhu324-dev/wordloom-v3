import { apiClient } from '@/shared/api';
import { SearchResultDto, SearchRequest } from '@/entities/search';

export interface SearchResultItem {
  id: string;
  entity_type: string;
  title?: string;
  snippet?: string;
  book_id?: string;
  relevance?: number;
  created_at?: string;
}

export interface SearchResponse {
  items: SearchResultItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface BookSearchHit {
  book_id: string;
  title: string;
  snippet?: string;
  maturity?: string;
  bookshelf_name?: string;
  path?: string;
  score?: number;
}

export interface BookSearchResponse {
  query: string;
  total: number;
  limit: number;
  offset: number;
  hits: BookSearchHit[];
}

export interface BookSearchRequest {
  text: string;
  bookshelfId?: string;
  limit?: number;
  offset?: number;
}

export const searchGlobal = async (q: string, limit = 20, offset = 0): Promise<SearchResponse> => {
  const resp = await apiClient.get<SearchResponse>(`/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`);
  return resp.data;
};

export const searchBlocks = async (q: string, bookId?: string, limit = 20, offset = 0): Promise<SearchResponse> => {
  const scope = bookId ? `&book_id=${bookId}` : '';
  const resp = await apiClient.get<SearchResponse>(`/search/blocks?q=${encodeURIComponent(q)}${scope}&limit=${limit}&offset=${offset}`);
  return resp.data;
};

export const searchBooks = async ({ text, bookshelfId, limit = 5, offset = 0 }: BookSearchRequest): Promise<BookSearchResponse> => {
  const params = new URLSearchParams();
  params.set('text', text);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  if (bookshelfId) params.set('bookshelf_id', bookshelfId);
  const resp = await apiClient.get<BookSearchResponse>(`/search/books?${params.toString()}`);
  return resp.data;
};

export const search = async (libraryId: string, request: SearchRequest): Promise<SearchResponse> => {
  const response = await apiClient.post<SearchResponse>(`/libraries/${libraryId}/search`, request);
  return response.data;
};

export const getSearchResult = async (libraryId: string, resultId: string): Promise<SearchResultDto> => {
  const response = await apiClient.get<SearchResultDto>(`/libraries/${libraryId}/search/${resultId}`);
  return response.data;
};
