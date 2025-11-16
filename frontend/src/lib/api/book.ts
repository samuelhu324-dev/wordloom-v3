/**
 * Book API Endpoints
 * Handles /books and related CRUD operations
 * Aligns with Backend Router: /api/books (11 endpoints)
 * Reference: ADR-039 (Book Module Refactoring - Hexagonal Alignment)
 */

import { apiClient } from './client';
import { BookDto, CreateBookRequest, UpdateBookRequest } from './types';

/**
 * Fetch all books in a bookshelf
 * GET /books?bookshelfId={bookshelfId}
 *
 * Returns only non-archived books by default
 *
 * @param bookshelfId - The parent bookshelf ID
 * @param includeArchived - If true, include archived books (default: false)
 * @returns Promise<BookDto[]> Array of books
 * @throws ApiErrorResponse if request fails or parent bookshelf not found
 */
export async function listBooks(
  bookshelfId: string,
  includeArchived: boolean = false
): Promise<BookDto[]> {
  const response = await apiClient.get<BookDto[]>('/books', {
    params: { bookshelfId, includeArchived },
  });
  return response.data;
}

/**
 * Fetch a single book by ID
 * GET /books/{id}
 *
 * @param id - The book ID
 * @returns Promise<BookDto> Book details
 * @throws ApiErrorResponse if book not found (404) or request fails
 */
export async function getBook(id: string): Promise<BookDto> {
  const response = await apiClient.get<BookDto>(`/books/${id}`);
  return response.data;
}

/**
 * Create a new book in a bookshelf
 * POST /books
 *
 * @param request - CreateBookRequest with bookshelfId, title, description, coverImageUrl
 * @returns Promise<BookDto> Newly created book
 * @throws ApiErrorResponse if validation fails or parent bookshelf not found
 */
export async function createBook(request: CreateBookRequest): Promise<BookDto> {
  const response = await apiClient.post<BookDto>('/books', request);
  return response.data;
}

/**
 * Update an existing book
 * PATCH /books/{id}
 *
 * Can update title, description, cover image, position, and archive status
 *
 * @param id - The book ID
 * @param request - UpdateBookRequest with optional fields to update
 * @returns Promise<BookDto> Updated book
 * @throws ApiErrorResponse if book not found (404) or validation fails
 */
export async function updateBook(id: string, request: UpdateBookRequest): Promise<BookDto> {
  const response = await apiClient.patch<BookDto>(`/books/${id}`, request);
  return response.data;
}

/**
 * Delete a book (soft delete)
 * DELETE /books/{id}
 *
 * Performs soft delete - book remains in database but marked as deleted
 * Can be recovered within retention period (30 days, see POLICY-010)
 * Related blocks are also soft-deleted
 *
 * @param id - The book ID
 * @returns Promise<void>
 * @throws ApiErrorResponse if book not found (404) or request fails
 */
export async function deleteBook(id: string): Promise<void> {
  await apiClient.delete(`/books/${id}`);
}

/**
 * Move a book to a different bookshelf
 * PATCH /books/{id}/move
 *
 * Moves the book to a new bookshelf while preserving its blocks and metadata
 *
 * @param id - The book ID
 * @param targetBookshelfId - The destination bookshelf ID
 * @returns Promise<BookDto> Updated book with new bookshelf reference
 * @throws ApiErrorResponse if book/bookshelf not found or invalid move operation
 */
export async function moveBook(id: string, targetBookshelfId: string): Promise<BookDto> {
  const response = await apiClient.patch<BookDto>(`/books/${id}/move`, {
    targetBookshelfId,
  });
  return response.data;
}

/**
 * Archive a book without full deletion
 * PATCH /books/{id}/archive
 *
 * Sets isArchived flag to true, book becomes invisible in normal views
 * but remains in database and can be restored
 *
 * @param id - The book ID
 * @returns Promise<BookDto> Updated book with isArchived = true
 * @throws ApiErrorResponse if book not found (404) or request fails
 */
export async function archiveBook(id: string): Promise<BookDto> {
  const response = await apiClient.patch<BookDto>(`/books/${id}/archive`, {});
  return response.data;
}

/**
 * Restore an archived book
 * PATCH /books/{id}/restore
 *
 * Sets isArchived flag to false, book becomes visible again
 *
 * @param id - The book ID
 * @returns Promise<BookDto> Updated book with isArchived = false
 * @throws ApiErrorResponse if book not found (404) or request fails
 */
export async function restoreBook(id: string): Promise<BookDto> {
  const response = await apiClient.patch<BookDto>(`/books/${id}/restore`, {});
  return response.data;
}
