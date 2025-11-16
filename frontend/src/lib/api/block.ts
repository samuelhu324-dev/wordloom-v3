/**
 * Block API Endpoints
 * Handles /blocks and related CRUD operations
 * Aligns with Backend Router: /api/blocks (13 endpoints)
 * Reference: ADR-042 (Block Paperballs Integration)
 */

import { apiClient } from './client';
import { BlockDto, CreateBlockRequest, UpdateBlockRequest } from './types';

/**
 * Fetch all blocks in a book
 * GET /blocks?bookId={bookId}
 *
 * Blocks are ordered by fractionalIndex (not creation date)
 * Reference: RULE-015 (Fractional Index Ordering)
 *
 * @param bookId - The parent book ID
 * @returns Promise<BlockDto[]> Array of blocks ordered by fractionalIndex
 * @throws ApiErrorResponse if request fails or parent book not found
 */
export async function listBlocks(bookId: string): Promise<BlockDto[]> {
  const response = await apiClient.get<BlockDto[]>('/blocks', {
    params: { bookId },
  });
  return response.data;
}

/**
 * Fetch a single block by ID
 * GET /blocks/{id}
 *
 * @param id - The block ID
 * @returns Promise<BlockDto> Block details
 * @throws ApiErrorResponse if block not found (404) or request fails
 */
export async function getBlock(id: string): Promise<BlockDto> {
  const response = await apiClient.get<BlockDto>(`/blocks/${id}`);
  return response.data;
}

/**
 * Create a new block in a book
 * POST /blocks
 *
 * New blocks are automatically assigned a fractionalIndex for ordering
 * If no fractionalIndex provided, defaults to end of list
 *
 * @param request - CreateBlockRequest with bookId, type, content
 * @returns Promise<BlockDto> Newly created block with assigned fractionalIndex
 * @throws ApiErrorResponse if validation fails or parent book not found
 */
export async function createBlock(request: CreateBlockRequest): Promise<BlockDto> {
  const response = await apiClient.post<BlockDto>('/blocks', request);
  return response.data;
}

/**
 * Update an existing block
 * PATCH /blocks/{id}
 *
 * Can update block type, content, and fractionalIndex (for reordering)
 *
 * @param id - The block ID
 * @param request - UpdateBlockRequest with optional fields to update
 * @returns Promise<BlockDto> Updated block
 * @throws ApiErrorResponse if block not found (404) or validation fails
 */
export async function updateBlock(id: string, request: UpdateBlockRequest): Promise<BlockDto> {
  const response = await apiClient.patch<BlockDto>(`/blocks/${id}`, request);
  return response.data;
}

/**
 * Delete a block (soft delete)
 * DELETE /blocks/{id}
 *
 * Performs soft delete - block remains in database but marked as deleted
 * Can be recovered within retention period (30 days, see POLICY-010)
 * Block's content is archived in chronicle_events audit trail
 *
 * @param id - The block ID
 * @returns Promise<void>
 * @throws ApiErrorResponse if block not found (404) or request fails
 */
export async function deleteBlock(id: string): Promise<void> {
  await apiClient.delete(`/blocks/${id}`);
}

/**
 * Reorder blocks using fractionalIndex
 * PATCH /blocks/{id}/reorder
 *
 * Fractional Index algorithm allows O(1) insertion at any position
 * without needing to update all subsequent indices
 * Reference: RULE-015
 *
 * @param id - The block ID to move
 * @param beforeBlockId - The ID of the block to insert before (null = append to end)
 * @returns Promise<BlockDto> Updated block with new fractionalIndex
 * @throws ApiErrorResponse if block not found or invalid operation
 */
export async function reorderBlock(
  id: string,
  beforeBlockId: string | null
): Promise<BlockDto> {
  const response = await apiClient.patch<BlockDto>(`/blocks/${id}/reorder`, {
    beforeBlockId,
  });
  return response.data;
}

/**
 * Duplicate a block (create copy with new ID)
 * POST /blocks/{id}/duplicate
 *
 * Creates an exact copy of the block with new ID, inserted after the original
 * Useful for reusing block templates
 *
 * @param id - The block ID to duplicate
 * @returns Promise<BlockDto> Newly created duplicate block
 * @throws ApiErrorResponse if source block not found (404) or request fails
 */
export async function duplicateBlock(id: string): Promise<BlockDto> {
  const response = await apiClient.post<BlockDto>(`/blocks/${id}/duplicate`, {});
  return response.data;
}

/**
 * Convert block between types
 * PATCH /blocks/{id}/convert
 *
 * Converts block from one type to another (e.g., markdown → heading)
 * Content may be re-formatted based on target type
 *
 * @param id - The block ID
 * @param targetType - Target block type ('markdown' | 'heading' | 'image' | 'video')
 * @returns Promise<BlockDto> Updated block with new type
 * @throws ApiErrorResponse if block not found or invalid conversion
 */
export async function convertBlockType(
  id: string,
  targetType: 'markdown' | 'heading' | 'image' | 'video'
): Promise<BlockDto> {
  const response = await apiClient.patch<BlockDto>(`/blocks/${id}/convert`, {
    targetType,
  });
  return response.data;
}

/**
 * Get block history (audit trail)
 * GET /blocks/{id}/history
 *
 * Returns all past versions of the block from chronicle_events
 * Useful for undo functionality and change tracking
 *
 * @param id - The block ID
 * @returns Promise<BlockDto[]> Array of block versions ordered by date (newest first)
 * @throws ApiErrorResponse if block not found (404) or request fails
 */
export async function getBlockHistory(id: string): Promise<BlockDto[]> {
  const response = await apiClient.get<BlockDto[]>(`/blocks/${id}/history`);
  return response.data;
}
