'use client';

import { api } from '@/shared/api';
import { CreateLibraryRequest, LibraryDto, UpdateLibraryRequest } from '@/entities/library';

const BASE_URL = '/libraries';

/** List all libraries */
export async function listLibraries(): Promise<LibraryDto[]> {
  const response = await api.get<LibraryDto[]>(BASE_URL);
  return response.data;
}

/** Get library by ID */
export async function getLibrary(id: string): Promise<LibraryDto> {
  const response = await api.get<LibraryDto>(`${BASE_URL}/${id}`);
  return response.data;
}

/** Create new library */
export async function createLibrary(request: CreateLibraryRequest): Promise<LibraryDto> {
  const response = await api.post<LibraryDto>(BASE_URL, request);
  return response.data;
}

/** Update library */
export async function updateLibrary(
  id: string,
  request: UpdateLibraryRequest
): Promise<LibraryDto> {
  const response = await api.patch<LibraryDto>(`${BASE_URL}/${id}`, request);
  return response.data;
}

/** Delete library */
export async function deleteLibrary(id: string): Promise<void> {
  await api.delete(`${BASE_URL}/${id}`);
}
