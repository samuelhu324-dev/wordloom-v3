/**
 * Library API Endpoints
 * Handles /libraries and related operations
 */

import { apiClient } from './client';

export interface LibraryDto {
  id: string;
  name: string;
  description?: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateLibraryRequest {
  name: string;
  description?: string;
}

export interface UpdateLibraryRequest {
  name?: string;
  description?: string;
}

/**
 * List all libraries for the current user
 */
export async function listLibraries(): Promise<LibraryDto[]> {
  const response = await apiClient.get<LibraryDto[]>('/libraries');
  return response.data;
}

/**
 * Get library by ID
 */
export async function getLibrary(id: string): Promise<LibraryDto> {
  const response = await apiClient.get<LibraryDto>(`/libraries/${id}`);
  return response.data;
}

/**
 * Create a new library
 */
export async function createLibrary(request: CreateLibraryRequest): Promise<LibraryDto> {
  const response = await apiClient.post<LibraryDto>('/libraries', request);
  return response.data;
}

/**
 * Update library
 */
export async function updateLibrary(id: string, request: UpdateLibraryRequest): Promise<LibraryDto> {
  const response = await apiClient.put<LibraryDto>(`/libraries/${id}`, request);
  return response.data;
}

/**
 * Delete library
 */
export async function deleteLibrary(id: string): Promise<void> {
  await apiClient.delete(`/libraries/${id}`);
}
