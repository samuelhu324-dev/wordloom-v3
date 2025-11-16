/**
 * Unified TypeScript Interface Definitions
 * Shared DTOs and Request/Response types for all API operations
 * Aligns with backend ADR-053 (Database Schema) + ADR-055 (Router Integration)
 */

/**
 * API Error Response Standard Format
 * All failed API calls return this structure
 */
export interface ApiErrorResponse {
  statusCode: number;
  message: string;
  error?: string;
  details?: Record<string, any>;
}

/**
 * Base Response wrapper for API responses
 * Used for paginated or complex responses
 */
export interface ApiResponse<T> {
  data: T;
  meta?: {
    total?: number;
    page?: number;
    pageSize?: number;
  };
}

// ============================================
// LIBRARY DTOs
// ============================================

/**
 * Library Data Transfer Object
 * Represents a user's personal library (one per user)
 * Reference: Backend Library aggregate
 */
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

// ============================================
// BOOKSHELF DTOs
// ============================================

/**
 * Bookshelf Data Transfer Object
 * Represents a collection of books within a library
 * Reference: Backend Bookshelf aggregate
 */
export interface BookshelfDto {
  id: string;
  libraryId: string;
  name: string;
  description?: string;
  position: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateBookshelfRequest {
  name: string;
  description?: string;
}

export interface UpdateBookshelfRequest {
  name?: string;
  description?: string;
  position?: number;
}

// ============================================
// BOOK DTOs
// ============================================

/**
 * Book Data Transfer Object
 * Represents a book as an independent aggregate root
 * Reference: Backend Book aggregate (Independent AR)
 */
export interface BookDto {
  id: string;
  bookshelfId: string;
  title: string;
  description?: string;
  coverImageUrl?: string;
  position: number;
  isArchived: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateBookRequest {
  bookshelfId: string;
  title: string;
  description?: string;
  coverImageUrl?: string;
}

export interface UpdateBookRequest {
  title?: string;
  description?: string;
  coverImageUrl?: string;
  position?: number;
  isArchived?: boolean;
}

// ============================================
// BLOCK DTOs
// ============================================

/**
 * Block Data Transfer Object
 * Represents a markdown block within a book
 * Uses Fractional Index for ordering (RULE-015)
 * Reference: Backend Block aggregate
 */
export interface BlockDto {
  id: string;
  bookId: string;
  type: 'markdown' | 'heading' | 'image' | 'video';
  content: string;
  fractionalIndex: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateBlockRequest {
  bookId: string;
  type: 'markdown' | 'heading' | 'image' | 'video';
  content: string;
}

export interface UpdateBlockRequest {
  type?: 'markdown' | 'heading' | 'image' | 'video';
  content?: string;
  fractionalIndex?: string;
}

// ============================================
// BATCH RESPONSE DTOs
// ============================================

/**
 * Paginated list response
 * Used for list endpoints
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

/**
 * Standard list response without pagination
 * Used when pagination is not needed
 */
export interface ListResponse<T> {
  items: T[];
  total: number;
}

/**
 * Delete response confirmation
 */
export interface DeleteResponse {
  id: string;
  deleted: boolean;
  deletedAt: string;
}

// ============================================
// UNION TYPES FOR EASIER USE
// ============================================

/**
 * Any DTO type
 */
export type AnyDto = LibraryDto | BookshelfDto | BookDto | BlockDto;

/**
 * Any Create Request type
 */
export type CreateRequestType =
  | CreateLibraryRequest
  | CreateBookshelfRequest
  | CreateBookRequest
  | CreateBlockRequest;

/**
 * Any Update Request type
 */
export type UpdateRequestType =
  | UpdateLibraryRequest
  | UpdateBookshelfRequest
  | UpdateBookRequest
  | UpdateBlockRequest;
