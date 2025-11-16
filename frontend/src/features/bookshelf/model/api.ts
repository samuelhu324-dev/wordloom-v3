import { apiClient } from '@/shared/api';
import { BookshelfDto, CreateBookshelfRequest, UpdateBookshelfRequest } from '@/entities/bookshelf';

export const listBookshelves = async (libraryId: string): Promise<BookshelfDto[]> => {
  const response = await apiClient.get<BookshelfDto[]>(`/libraries/${libraryId}/bookshelves`);
  return response.data;
};

export const getBookshelf = async (libraryId: string, bookshelfId: string): Promise<BookshelfDto> => {
  const response = await apiClient.get<BookshelfDto>(`/libraries/${libraryId}/bookshelves/${bookshelfId}`);
  return response.data;
};

export const createBookshelf = async (libraryId: string, request: CreateBookshelfRequest): Promise<BookshelfDto> => {
  const response = await apiClient.post<BookshelfDto>(`/libraries/${libraryId}/bookshelves`, request);
  return response.data;
};

export const updateBookshelf = async (libraryId: string, bookshelfId: string, request: UpdateBookshelfRequest): Promise<BookshelfDto> => {
  const response = await apiClient.patch<BookshelfDto>(`/libraries/${libraryId}/bookshelves/${bookshelfId}`, request);
  return response.data;
};

export const deleteBookshelf = async (libraryId: string, bookshelfId: string): Promise<void> => {
  await apiClient.delete(`/libraries/${libraryId}/bookshelves/${bookshelfId}`);
};
