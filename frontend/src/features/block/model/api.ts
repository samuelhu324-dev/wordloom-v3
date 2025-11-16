import { apiClient } from '@/shared/api';
import { BlockDto, CreateBlockRequest, UpdateBlockRequest } from '@/entities/block';

export const listBlocks = async (libraryId: string, bookshelfId: string, bookId: string): Promise<BlockDto[]> => {
  const response = await apiClient.get<BlockDto[]>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}/blocks`
  );
  return response.data;
};

export const getBlock = async (
  libraryId: string,
  bookshelfId: string,
  bookId: string,
  blockId: string
): Promise<BlockDto> => {
  const response = await apiClient.get<BlockDto>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}/blocks/${blockId}`
  );
  return response.data;
};

export const createBlock = async (
  libraryId: string,
  bookshelfId: string,
  bookId: string,
  request: CreateBlockRequest
): Promise<BlockDto> => {
  const response = await apiClient.post<BlockDto>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}/blocks`,
    request
  );
  return response.data;
};

export const updateBlock = async (
  libraryId: string,
  bookshelfId: string,
  bookId: string,
  blockId: string,
  request: UpdateBlockRequest
): Promise<BlockDto> => {
  const response = await apiClient.patch<BlockDto>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}/blocks/${blockId}`,
    request
  );
  return response.data;
};

export const deleteBlock = async (
  libraryId: string,
  bookshelfId: string,
  bookId: string,
  blockId: string
): Promise<void> => {
  await apiClient.delete(`/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}/blocks/${blockId}`);
};
