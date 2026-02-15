import { apiClient } from '@/shared/api';
import { BookDto, CreateBookRequest, UpdateBookRequest, toBookDto, BackendBook } from '@/entities/book';

// Backend unified pagination shape (new) + legacy shape support
interface BackendBookPaginatedResponseNew {
  items: BackendBook[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
interface BackendBookPaginatedResponseLegacy {
  items: BackendBook[];
  total: number;
}
type BackendBookPaginatedResponse = BackendBookPaginatedResponseNew | BackendBookPaginatedResponseLegacy;

// Normalized frontend pagination shape
export interface BookListPage {
  items: BookDto[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/** List all books, optionally filtered by bookshelf_id */
// Sunset notice: legacy {items,total} shape deprecated after 2025-12-15

export const listBooks = async (
  bookshelfId?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<BookListPage> => {
  const params: string[] = [];
  if (bookshelfId) params.push(`bookshelf_id=${bookshelfId}`);
  // pagination → skip/limit for backend compatibility
  const skip = (page - 1) * pageSize;
  params.push(`skip=${skip}`);
  params.push(`limit=${pageSize}`);
  const query = params.length ? `?${params.join('&')}` : '';
  try {
    console.log('[listBooks] Fetching from /books' + query);
    const response = await apiClient.get<BackendBookPaginatedResponse>(`/books${query}`);
    const data = response.data;
    console.log('[listBooks] Raw response:', data);
    // Defensive parsing for both legacy and new pagination shapes
    const items: BackendBook[] = Array.isArray((data as any)?.items) ? (data as any).items : [];
    const total: number = typeof (data as any)?.total === 'number' ? (data as any).total : items.length;
    const norm: BookListPage = {
      items: items.map(toBookDto),
      total,
      page: typeof (data as any)?.page === 'number' ? (data as any).page : page,
      page_size: typeof (data as any)?.page_size === 'number' ? (data as any).page_size : pageSize,
      has_more: typeof (data as any)?.has_more === 'boolean'
        ? (data as any).has_more
        : (skip + items.length) < total,
    };
    console.log('[listBooks] Normalized pagination:', norm);
    return norm;
  } catch (err) {
    console.error('[listBooks] Error:', err);
    throw err;
  }
};

/** Get single book by ID */
export const getBook = async (bookId: string): Promise<BookDto> => {
  try {
    const response = await apiClient.get<BackendBook>(
      `/books/${bookId}`
    );
    return toBookDto(response.data as BackendBook);
  } catch (err) {
    console.error('[getBook] Error:', err);
    throw err;
  }
};

/** Create book (request must include bookshelf_id) */
export const createBook = async (
  request: CreateBookRequest
): Promise<BookDto> => {
  try {
    const response = await apiClient.post<BackendBook>(
      `/books`,
      request
    );
    return toBookDto(response.data as BackendBook);
  } catch (err) {
    console.error('[createBook] Error:', err);
    throw err;
  }
};

/** Update book */
export const updateBook = async (
  bookId: string,
  request: UpdateBookRequest
): Promise<BookDto> => {
  try {
    const response = await apiClient.patch<BackendBook>(
      `/books/${bookId}`,
      request
    );
    return toBookDto(response.data as BackendBook);
  } catch (err) {
    console.error('[updateBook] Error:', err);
    throw err;
  }
};

/** Delete book */
export const deleteBook = async (bookId: string): Promise<void> => {
  try {
    await apiClient.delete(`/books/${bookId}`);
  } catch (err) {
    console.error('[deleteBook] Error:', err);
    throw err;
  }
};

export interface MoveBookToBasementPayload {
  bookId: string;
  basementBookshelfId: string;
}

/** Soft-delete book by moving it into Basement */
export const moveBookToBasement = async ({
  bookId,
  basementBookshelfId,
}: MoveBookToBasementPayload): Promise<void> => {
  try {
    await apiClient.post(`/admin/books/${bookId}/move-to-basement`, {
      basement_bookshelf_id: basementBookshelfId,
    });
  } catch (err) {
    console.error('[moveBookToBasement] Error:', err);
    throw err;
  }
};

/** Recalculate maturity score for a book (optionally include operations_bonus 0-60) */
export const recalculateBookMaturity = async (
  bookId: string,
  payload?: Partial<{
    tag_count: number;
    block_type_count: number;
    block_count: number;
    open_todo_count: number;
    operations_bonus: number;
    cover_icon: string | null;
    trigger: string;
  }>
): Promise<BookDto> => {
  try {
    const response = await apiClient.post<BackendBook>(
      `/books/${bookId}/maturity/recalculate`,
      payload || {}
    );
    return toBookDto(response.data as BackendBook);
  } catch (err) {
    console.error('[recalculateBookMaturity] Error:', err);
    throw err;
  }
};

/** Upload cover image for a book (stable-only enforcement handled server-side) */
export const uploadBookCover = async (
  bookId: string,
  file: File,
  correlationId?: string,
): Promise<BookDto> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post<BackendBook>(`/books/${bookId}/cover`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(correlationId ? { 'X-Request-Id': correlationId } : null),
      },
    });
    return toBookDto(response.data as BackendBook);
  } catch (err) {
    console.error('[uploadBookCover] Error:', err);
    throw err;
  }
};

