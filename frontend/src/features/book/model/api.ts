import { apiClient } from '@/shared/api';
import { BookDto, CreateBookRequest, UpdateBookRequest } from '@/entities/book';

export const listBooks = async (libraryId: string, bookshelfId: string): Promise<BookDto[]> => {
  const response = await apiClient.get<BookDto[]>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books`
  );
  return response.data;
};

export const getBook = async (libraryId: string, bookshelfId: string, bookId: string): Promise<BookDto> => {
  const response = await apiClient.get<BookDto>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}`
  );
  return response.data;
};

export const createBook = async (
  libraryId: string,
  bookshelfId: string,
  request: CreateBookRequest
): Promise<BookDto> => {
  const response = await apiClient.post<BookDto>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books`,
    request
  );
  return response.data;
};

export const updateBook = async (
  libraryId: string,
  bookshelfId: string,
  bookId: string,
  request: UpdateBookRequest
): Promise<BookDto> => {
  const response = await apiClient.patch<BookDto>(
    `/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}`,
    request
  );
  return response.data;
};

export const deleteBook = async (libraryId: string, bookshelfId: string, bookId: string): Promise<void> => {
  await apiClient.delete(`/libraries/${libraryId}/bookshelves/${bookshelfId}/books/${bookId}`);
};
