import { BaseDto } from '@/shared/api';

/** Bookshelf DTO */
export interface BookshelfDto extends BaseDto {
  library_id: string;
  name: string;
  description?: string;
  type: 'NORMAL' | 'BASEMENT';
}

/** Create Bookshelf Request */
export interface CreateBookshelfRequest {
  library_id: string;
  name: string;
  description?: string;
}

/** Update Bookshelf Request */
export interface UpdateBookshelfRequest {
  name?: string;
  description?: string;
}
