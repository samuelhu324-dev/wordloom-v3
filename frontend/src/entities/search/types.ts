import { BaseDto } from '@/shared/api';

/** Search Result DTO */
export interface SearchResultDto extends BaseDto {
  entity_type: 'LIBRARY' | 'BOOKSHELF' | 'BOOK' | 'BLOCK' | 'TAG';
  entity_id: string;
  title: string;
  preview?: string;
  score: number;
}

/** Search Request */
export interface SearchRequest {
  query: string;
  entity_type?: SearchResultDto['entity_type'];
  limit?: number;
  offset?: number;
}

/** Search Response */
export interface SearchResponse {
  results: SearchResultDto[];
  total: number;
}
