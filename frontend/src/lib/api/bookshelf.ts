/**
 * Bookshelf API Endpoints
 * Handles /bookshelves and related CRUD operations
 * Aligns with Backend Router: /api/bookshelves (12 endpoints)
 */

import { apiClient } from './client';
import {
  BookshelfDto,
  CreateBookshelfRequest,
  UpdateBookshelfRequest,
} from './types';

/**
 * Fetch all bookshelves for a specific library
 * GET /bookshelves?libraryId={libraryId}
 *
 * @param libraryId - The parent library ID
 * @returns Promise<BookshelfDto[]> Array of bookshelves
 * @throws ApiErrorResponse if request fails
 */
export async function listBookshelves(libraryId: string): Promise<BookshelfDto[]> {
  const response = await apiClient.get<BookshelfDto[]>('/bookshelves', {
    params: { libraryId },
  });
  return response.data;
}

/**
 * Fetch a single bookshelf by ID
 * GET /bookshelves/{id}
 *
 * @param id - The bookshelf ID
 * @returns Promise<BookshelfDto> Bookshelf details
 * @throws ApiErrorResponse if bookshelf not found (404) or request fails
 */
export async function getBookshelf(id: string): Promise<BookshelfDto> {
  const response = await apiClient.get<BookshelfDto>(`/bookshelves/${id}`);
  return response.data;
}

/**
 * Create a new bookshelf in a library
 * POST /bookshelves
 *
 * @param libraryId - The parent library ID
 * @param request - CreateBookshelfRequest with name, description, position
 * @returns Promise<BookshelfDto> Newly created bookshelf
 * @throws ApiErrorResponse if validation fails or parent library not found
 */
export async function createBookshelf(
  libraryId: string,
  request: CreateBookshelfRequest
): Promise<BookshelfDto> {
  const response = await apiClient.post<BookshelfDto>('/bookshelves', {
    libraryId,
    ...request,
  });
  return response.data;
}

/**
 * Update an existing bookshelf
 * PATCH /bookshelves/{id}
 *
 * @param id - The bookshelf ID
 * @param request - UpdateBookshelfRequest with optional fields to update
 * @returns Promise<BookshelfDto> Updated bookshelf
 * @throws ApiErrorResponse if bookshelf not found (404) or validation fails
 */
export async function updateBookshelf(
  id: string,
  request: UpdateBookshelfRequest
): Promise<BookshelfDto> {
  const response = await apiClient.patch<BookshelfDto>(`/bookshelves/${id}`, request);
  return response.data;
}

/**
 * Delete a bookshelf (soft delete)
 * DELETE /bookshelves/{id}
 *
 * Performs soft delete - bookshelf remains in database but marked as deleted
 * Can be recovered within retention period (see POLICY-010)
 *
 * @param id - The bookshelf ID
 * @returns Promise<void>
 * @throws ApiErrorResponse if bookshelf not found (404) or request fails
 */
export async function deleteBookshelf(id: string): Promise<void> {
  await apiClient.delete(`/bookshelves/${id}`);
}

/**
 * Get the basement of a bookshelf
 * GET /bookshelves/{id}/basement
 *
 * The basement is a special container for miscellaneous books
 * Reference: ADR-005 (Bookshelf Domain Simplification)
 *
 * @param id - The bookshelf ID
 * @returns Promise<BookshelfDto> Basement bookshelf
 * @throws ApiErrorResponse if bookshelf not found or has no basement
 */
export async function getBookshelfBasement(id: string): Promise<BookshelfDto> {
  const response = await apiClient.get<BookshelfDto>(`/bookshelves/${id}/basement`);
  return response.data;
}
