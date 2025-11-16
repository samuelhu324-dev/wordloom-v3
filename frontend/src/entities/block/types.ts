import { BaseDto } from '@/shared/api';

/** Block DTO - 书中的最小单位 */
export interface BlockDto extends BaseDto {
  book_id: string;
  type: 'HEADING' | 'PARAGRAPH' | 'LIST' | 'CODE' | 'IMAGE' | 'VIDEO';
  content: string;
  fractional_index: string;
  media_ids?: string[];
}

/** Create Block Request */
export interface CreateBlockRequest {
  book_id: string;
  type: BlockDto['type'];
  content: string;
}

/** Update Block Request */
export interface UpdateBlockRequest {
  type?: BlockDto['type'];
  content?: string;
}
