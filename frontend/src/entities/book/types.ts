import { BaseDto } from '@/shared/api';

/** Book DTO */
export interface BookDto extends BaseDto {
  bookshelf_id: string;
  name: string;
  description?: string;
  cover_media_id?: string;
}

/** Create Book Request */
export interface CreateBookRequest {
  bookshelf_id: string;
  name: string;
  description?: string;
}

/** Update Book Request */
export interface UpdateBookRequest {
  name?: string;
  description?: string;
  cover_media_id?: string;
}
